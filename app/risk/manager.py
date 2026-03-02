from typing import Any

from app.core import messages as msg
from app.core.exceptions import (
    InsufficientMarginError,
    InvalidVolumeError,
    MaxPositionsError,
    SpreadTooWideError,
)
from app.core.protocols import AccountServiceProvider, BrokerProtocol
from app.core.settings import settings
from app.schemas.metaapi import AccountInfo, SymbolInfo
from app.risk.correlation import CorrelationManager
from app.risk.drawdown import DrawdownManager
from app.utils.logger import logger


class RiskManager:
    """Core risk management engine for QuantLux-FX."""

    def __init__(
        self,
        drawdown_manager: DrawdownManager,
        correlation_manager: CorrelationManager,
        broker: BrokerProtocol,
        account_service: AccountServiceProvider,
    ):
        self.drawdown_manager = drawdown_manager
        self.correlation_manager = correlation_manager
        self.broker = broker
        self.account_service = account_service

        self.max_slippage = settings.MAX_SLIPPAGE
        self.min_margin_level = settings.MIN_MARGIN_LEVEL

    async def check_trade_allowed(
        self,
        account: AccountInfo,
        symbol: SymbolInfo,
        volume: float,
        open_positions_count: int | None = None,
    ) -> bool:
        """Validate all active risk rules."""
        if not self.drawdown_manager.is_trading_allowed():
            logger.warning(
                msg.RISK_DRAWDOWN_BLOCKED.format(
                    reason=self.drawdown_manager.halt_reason
                )
            )
            return False

        if not settings.AUTO_TRADING:
            logger.warning(msg.RISK_ACCOUNT_DISABLED)
            return False

        # Position Count Limits
        try:
            if open_positions_count is None:
                open_positions = await self._get_open_positions()
                open_positions_count = len(open_positions)

            if not self._check_position_limits(open_positions_count):
                return False
        except MaxPositionsError as e:
            logger.warning(f"Trade blocked: {e}")
            return False

        # Financial Health (Margin)
        try:
            if not self._check_margin_levels(account):
                return False
        except InsufficientMarginError as e:
            logger.warning(f"Trade blocked: {e}")
            return False

        # Market Condition (Spread/Slippage)
        try:
            if not self._check_spread(symbol):
                return False
        except SpreadTooWideError as e:
            logger.warning(f"Trade blocked: {e}")
            return False

        # Instrument Constraints (Volume)
        try:
            if not self._check_volume(symbol, volume):
                return False
        except InvalidVolumeError as e:
            logger.warning(f"Trade blocked: {e}")
            return False

        # Portfolio Exposure (Correlation)
        open_symbols = await self._get_open_symbols()
        if not self.correlation_manager.check_correlation(symbol.symbol, open_symbols):
            logger.warning(msg.RISK_CORRELATION_BLOCKED.format(symbol=symbol.symbol))
            return False

        # News Check
        if not await self.broker.is_safe_to_trade_news(
            symbol=symbol,
            impact_minutes_before=settings.NEWS_PAUSE_MINUTES_BEFORE,
            impact_minutes_after=settings.NEWS_PAUSE_MINUTES_AFTER,
        ):
            logger.warning(msg.RISK_LIMIT_EXCEEDED.format(reason="High-impact news"))
            return False

        return True

    def _check_position_limits(self, open_positions_count: int) -> bool:
        """Verify position count against MAX_OPEN_TRADES."""
        if open_positions_count >= settings.MAX_OPEN_TRADES:
            raise MaxPositionsError(
                f"Max open trades reached: {open_positions_count}/{settings.MAX_OPEN_TRADES}"
            )
        return True

    def _check_margin_levels(self, account: AccountInfo) -> bool:
        """Check margin level and issue warnings/errors if low."""
        warning_margin = self.min_margin_level * 1.5

        if 0 < account.margin_level < warning_margin:
            logger.warning(
                msg.MSG_MARGIN_LEVEL_LOW.format(
                    level=account.margin_level, limit=self.min_margin_level
                )
            )

        if 0 < account.margin_level < self.min_margin_level:
            msg_text = f"Insufficient margin: {account.margin_level:.2f}% < {self.min_margin_level}%"
            logger.error(msg_text)
            raise InsufficientMarginError(msg_text)

        return True

    def _check_spread(self, symbol: SymbolInfo) -> bool:
        """Ensure market spread is within the configured limit."""
        max_spread_points = settings.MAX_SPREAD_PIPS * 10

        if symbol.spread > max_spread_points:
            msg_text = (
                f"Spread too wide: {symbol.spread} points > {max_spread_points} points"
            )
            logger.warning(msg_text)
            raise SpreadTooWideError(msg_text)

        return True

    def _check_volume(self, symbol: SymbolInfo, volume: float) -> bool:
        """Validate if the lot size satisfies the symbol's volume constraints."""
        if volume < symbol.volume_min or (
            symbol.volume_max > 0 and volume > symbol.volume_max
        ):
            raise InvalidVolumeError(
                f"Volume {volume} outside valid range [{symbol.volume_min}, {symbol.volume_max}]"
            )
        return True

    async def _get_open_positions(self) -> list[Any]:
        """Fetch all currently open positions from the broker."""
        try:
            positions = await self.broker.get_positions()
            return [
                pos
                for pos in positions
                if (hasattr(pos, "magic") and pos.magic == settings.MAGIC_NUMBER)
                or (isinstance(pos, dict) and pos.get("magic") == settings.MAGIC_NUMBER)
            ]
        except Exception as e:
            logger.error(msg.RISK_POSITIONS_FETCH_ERROR.format(error=e))
            return []

    async def _get_open_symbols(self) -> list[str]:
        """Get a list of symbols currently in an open position."""
        positions = await self._get_open_positions()
        return [
            pos.symbol if hasattr(pos, "symbol") else pos.get("symbol")
            for pos in positions
        ]
