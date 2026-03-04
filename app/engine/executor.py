"""Signal execution pipeline."""

from app.core import logger, settings
from app.core import messages as msg
from app.core.enums import SignalAction
from app.core.protocols import BrokerProtocol
from app.engine.execution_helpers import execute_order
from app.engine.splitter import SplitOrderManager
from app.schemas.metaapi import SymbolInfo
from app.schemas.signal import TradeSignal
from app.risk import RiskManager
from app.risk.sizing.strategies import calculate_risk_lot
from app.strategies.base import BaseStrategy


class SignalExecutor:
    """Processes trading signals through risk checks and executes orders."""

    def __init__(self, risk_manager: RiskManager, broker: BrokerProtocol):
        self.risk_manager = risk_manager
        self.broker = broker
        self.split_manager = SplitOrderManager(self.broker)

    async def process_signal(
        self, signal: TradeSignal, strategy: BaseStrategy | None = None
    ) -> None:
        """Validate, size, risk-check, and execute a trade signal."""
        try:
            account_info, symbol_info = await self._fetch_market_data(signal.symbol)
            if not account_info or not symbol_info:
                return

            volume = self._calculate_volume(signal, account_info, symbol_info)
            if volume <= 0:
                return

            comment = signal.comment or (
                strategy.__class__.__name__ if strategy else ""
            )
            await self._dispatch_order(signal, volume, comment)

        except Exception as e:
            logger.error(
                msg.SIGNAL_PROCESS_ERROR.format(symbol=signal.symbol, error=e),
                exc_info=True,
            )

    async def _fetch_market_data(self, symbol: str):
        """Fetch required account and symbol data from broker."""
        account_info = await self.broker.get_account_info()
        if not account_info:
            logger.error(msg.ACC_INFO_FAILED)
            return None, None

        symbol_info = await self.broker.get_symbol_info(symbol)
        if not symbol_info:
            logger.error(msg.EXECUTOR_SYM_INFO_FAILED.format(symbol=symbol))
            return account_info, None

        return account_info, symbol_info

    def _calculate_volume(
        self, signal: TradeSignal, account_info, symbol_info
    ) -> float:
        """Calculate risk-adjusted volume and check limits."""
        volume = calculate_risk_lot(
            account=account_info,
            symbol_info=symbol_info,
            risk_pct=settings.PER_TRADE_RISK_PCT,
            sl_pips=self._calculate_sl_pips(
                signal.price, signal.stop_loss, symbol_info
            ),
        )

        if volume <= 0:
            logger.warning(msg.EXECUTOR_ZERO_VOLUME.format(symbol=signal.symbol))
            return 0.0

        if not self.risk_manager.check_risk(signal.symbol, signal.action, volume):
            logger.warning(msg.EXECUTOR_RISK_BLOCKED.format(symbol=signal.symbol))
            return 0.0

        return volume

    async def _dispatch_order(
        self, signal: TradeSignal, volume: float, base_comment: str
    ):
        """Dispatch a split or single order based on TP levels."""
        tp_levels = signal.tp_levels

        if tp_levels and isinstance(tp_levels, list) and len(tp_levels) > 1:
            await self.split_manager.execute(
                signal.action,
                signal.symbol,
                volume,
                signal.stop_loss,
                tp_levels,
                base_comment,
            )
        else:
            await self._execute_single_order(
                signal.action,
                signal.symbol,
                volume,
                signal.stop_loss,
                signal.take_profit,
                base_comment,
            )

    async def _execute_single_order(
        self,
        action: SignalAction,
        symbol: str,
        volume: float,
        stop_loss: float | None,
        take_profit: float | None,
        comment: str,
    ):
        """Execute a single market order."""
        await execute_order(
            action=action,
            symbol=symbol,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment=comment,
        )

    def _calculate_sl_pips(self, entry: float, sl: float, info: SymbolInfo) -> float:
        """Convert SL distance to pips."""
        if not sl or not entry:
            return settings.DEFAULT_SL_PIPS

        diff = abs(entry - sl)
        return diff / info.point / 10 if "JPY" in info.symbol else diff / info.point
