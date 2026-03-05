"""RSI Calculation Logic."""

import numpy as np
import pandas as pd

from app.core.enums import RSISmoothing, SignalAction
from app.indicators.rsi.config import RSIConfig
from app.utils.logger import logger


class ModernRSI:
    """Modern RSI calculator with vectorized operations."""

    def __init__(self, config: RSIConfig | None = None):
        self.config = config or RSIConfig()

    def calculate(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI using vectorized operations."""
        if len(prices) < self.config.period + 1:
            logger.warning(
                f"Not enough data for RSI calculation. Need {self.config.period + 1}, got {len(prices)}"
            )
            return pd.Series(index=prices.index, dtype=float)

        delta = prices.diff()

        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        if self.config.smoothing == RSISmoothing.WILDER:
            avg_gains = self._wilder_smoothing(gains, self.config.period)
            avg_losses = self._wilder_smoothing(losses, self.config.period)
        elif self.config.smoothing == RSISmoothing.EMA:
            avg_gains = gains.ewm(span=self.config.period, adjust=False).mean()
            avg_losses = losses.ewm(span=self.config.period, adjust=False).mean()
        else:
            avg_gains = gains.rolling(window=self.config.period).mean()
            avg_losses = losses.rolling(window=self.config.period).mean()

        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def _wilder_smoothing(series: pd.Series, period: int) -> pd.Series:
        """Wilder's smoothing method (original RSI calculation)."""
        alpha = 1.0 / period
        return series.ewm(alpha=alpha, adjust=False).mean()

    def get_signal(self, rsi_value: float) -> SignalAction:
        """Get trading signal based on RSI value."""
        if rsi_value <= self.config.oversold:
            return SignalAction.BUY
        elif rsi_value >= self.config.overbought:
            return SignalAction.SELL
        return SignalAction.HOLD

    def calculate_adaptive_period(self, prices: pd.Series, lookback: int = 50) -> int:
        """Calculate adaptive RSI period based on recent volatility."""
        if len(prices) < lookback:
            return self.config.period

        returns = prices.pct_change().iloc[-lookback:]
        volatility = returns.std()

        min_period, max_period = 7, 28
        normalized = np.clip(volatility * 1000, 0, 1)
        adaptive_period = int(max_period - (normalized * (max_period - min_period)))

        return adaptive_period
