from collections.abc import Callable

from app.core import logger, settings
from app.core import messages as msg
from app.core.enums import SignalAction
from app.core.protocols import BrokerProtocol
from app.engine.execution_helpers import execute_order
from app.engine.splitter import SplitOrderManager
from app.models.metaapi import SymbolInfo
from app.models.signal import TradeSignal
from app.risk import RiskManager
from app.risk.ai_guard import evaluate_trade as ai_evaluate_trade
from app.risk.sizing.strategies import calculate_risk_lot
from app.strategies.base import BaseStrategy


class SignalExecutor:
    """Handles professional execution of trading signals."""

    def __init__(self, risk_manager: RiskManager, broker: BrokerProtocol, gemini=None):
        self.risk_manager = risk_manager
        self.broker = broker
        self.gemini = gemini
        self.notification_callback: Callable[[str], None] | None = None
        self.split_manager = SplitOrderManager(self.broker, self._notify)

    async def process_signal(
        self, signal: TradeSignal, strategy: BaseStrategy | None = None
    ) -> None:
        """Process a validated TradeSignal model."""
        try:
            action = signal.action
            symbol = signal.symbol

            # Get current account info
            account_info = await self.broker.get_account_info()
            if not account_info:
                logger.error(msg.ACC_INFO_FAILED)
                return

            # Get symbol info
            symbol_info = await self.broker.get_symbol_info(symbol)
            if not symbol_info:
                logger.error(msg.EXECUTOR_SYM_INFO_FAILED.format(symbol=symbol))
                return

            current_price = signal.price
            stop_loss = signal.stop_loss

            # 3. Calculate Position Size
            volume = calculate_risk_lot(
                account=account_info,
                symbol_info=symbol_info,
                risk_pct=settings.PER_TRADE_RISK_PCT,
                sl_pips=self._calculate_sl_pips(current_price, stop_loss, symbol_info),
            )

            if volume <= 0:
                logger.warning(msg.EXECUTOR_ZERO_VOLUME.format(symbol=symbol))
                return

            # Global Risk Check
            if not self.risk_manager.check_risk(symbol, action, volume):
                logger.warning(msg.EXECUTOR_RISK_BLOCKED.format(symbol=symbol))
                return

            # 5. AI Risk Guard (optional, fail-open)
            if (
                settings.ENABLE_AI_RISK_GUARD
                and self.gemini
                and self.gemini.is_available
            ):
                try:
                    drawdown_pct = (
                        (1 - account_info.equity / account_info.balance) * 100
                        if account_info.balance > 0
                        else 0.0
                    )
                    positions = await self.broker.get_positions()
                    guard_result = await ai_evaluate_trade(
                        gemini=self.gemini,
                        symbol=symbol,
                        action=action.value,
                        volume=volume,
                        balance=account_info.balance,
                        equity=account_info.equity,
                        drawdown_pct=drawdown_pct,
                        daily_dd_pct=drawdown_pct,
                        open_positions=len(positions) if positions else 0,
                    )
                    if not guard_result.approved:
                        message = msg.AI_GUARD_BLOCKED.format(
                            action=action.value,
                            symbol=symbol,
                            reason=guard_result.reasoning,
                        )
                        logger.warning(message)
                        self._notify(message)
                        return
                    logger.info(msg.AI_MARKET_ANALYSING.format(symbol=symbol))
                    analysis_result = await self.gemini.analyze_market(
                        symbol, timeframe="H1"
                    )
                    if not analysis_result:
                        logger.warning(msg.AI_MARKET_FAILED)
                except Exception as e:
                    logger.warning(msg.AI_GUARD_ERROR.format(error=e))

            # Check for Take Profits (Split Execution)
            tp_levels = signal.tp_levels
            take_profit = signal.take_profit
            comment = signal.comment
            if not comment and strategy:
                comment = strategy.__class__.__name__

            if tp_levels and isinstance(tp_levels, list) and len(tp_levels) > 1:
                await self.split_manager.execute(
                    action, symbol, volume, stop_loss, tp_levels, comment
                )
            else:
                await self._execute_single_order(
                    action, symbol, volume, stop_loss, take_profit, comment
                )

        except Exception as e:
            error_msg = msg.SIGNAL_PROCESS_ERROR.format(symbol=symbol, error=e)
            logger.error(error_msg, exc_info=True)
            self._notify(error_msg)

    async def _execute_single_order(
        self,
        action: SignalAction,
        symbol: str,
        volume: float,
        stop_loss: float | None,
        take_profit: float | None,
        comment: str,
    ):
        """Execute a standard single order."""

        await execute_order(
            action=action,
            symbol=symbol,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment=comment,
            notification_callback=self.notification_callback,
        )

    def _calculate_sl_pips(self, entry: float, sl: float, info: SymbolInfo) -> float:
        """Calculate Stop Loss in pips."""
        if not sl or not entry:
            return settings.DEFAULT_SL_PIPS  # Default fallback

        diff = abs(entry - sl)
        return diff / info.point / 10 if "JPY" in info.symbol else diff / info.point

    def _notify(self, message: str):
        if self.notification_callback:
            self.notification_callback(message)
