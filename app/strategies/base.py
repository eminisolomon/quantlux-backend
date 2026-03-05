from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.risk.drawdown import DrawdownManager
from app.utils.logger import logger


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    def __init__(
        self,
        symbol: str,
        drawdown_manager: DrawdownManager,
        params: dict[str, Any] = None,
    ):
        """Initialize the strategy."""
        self.symbol = symbol
        self.drawdown_manager = drawdown_manager
        self.params = params or {}
        self.validate_params()

        logger.info(
            f"Initialized {self.__class__.__name__} for {symbol} with params: {self.params}"
        )

    def validate_params(self):
        """Validate strategy parameters. Override to check for required params."""
        pass

    @abstractmethod
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate buy/sell signals from historical data."""
        pass

    @abstractmethod
    async def process_tick(self, tick: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a new real-time tick and return a signal or None."""
        pass

    async def check_risk(self) -> bool:
        """Check if trading is allowed by risk rules."""
        is_allowed, halt_reason = await self.drawdown_manager.is_trading_allowed()
        if not is_allowed:
            logger.warning(f"Strategy {self.__class__.__name__} paused: {halt_reason}")
            return False
        return True
