"""Adaptive Bollinger Bands indicator with ATR-based width adjustment."""

from dataclasses import dataclass

import pandas as pd

from app.utils.logger import logger


@dataclass
class BollingerBandsResult:
    """Result from Bollinger Bands calculation."""

    upper_band: pd.Series
    middle_band: pd.Series
    lower_band: pd.Series
    bandwidth: pd.Series  # Distance between bands
    percent_b: pd.Series  # Where price is relative to bands (0-1)

    def get_current_position(self, price: float) -> str:
        """Get current price position relative to bands."""
        current_pb = self.percent_b.iloc[-1]

        if current_pb >= 1.0:
            return "ABOVE_UPPER"
        elif current_pb > 0.8:
            return "NEAR_UPPER"
        elif current_pb > 0.2:
            return "MIDDLE"
        elif current_pb > 0.0:
            return "NEAR_LOWER"
        else:
            return "BELOW_LOWER"


class AdaptiveBollingerBands:
    """Adaptive Bollinger Bands using ATR for volatility adjustment."""

    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        adaptive: bool = True,
        atr_period: int = 14,
    ):
        """Initialize Adaptive Bollinger Bands."""
        self.period = period
        self.std_dev = std_dev
        self.adaptive = adaptive
        self.atr_period = atr_period

    def calculate(self, df: pd.DataFrame) -> BollingerBandsResult:
        """Calculate Bollinger Bands for the given OHLC data."""
        if len(df) < self.period:
            logger.warning(
                f"Not enough data for Bollinger Bands (need {self.period}, got {len(df)})"
            )
            return self._empty_result(df)

        closes = df["close"]

        # Calculate middle band (SMA)
        middle_band = closes.rolling(window=self.period).mean()

        # Calculate standard deviation
        std = closes.rolling(window=self.period).std()

        if self.adaptive:
            # Adjust multiplier based on ATR
            multiplier = self._calculate_adaptive_multiplier(df)
        else:
            multiplier = self.std_dev

        # Calculate upper and lower bands
        upper_band = middle_band + (std * multiplier)
        lower_band = middle_band - (std * multiplier)

        # Calculate bandwidth (volatility indicator)
        bandwidth = (upper_band - lower_band) / middle_band * 100

        # Calculate %B (price position within bands)
        percent_b = (closes - lower_band) / (upper_band - lower_band)

        return BollingerBandsResult(
            upper_band=upper_band,
            middle_band=middle_band,
            lower_band=lower_band,
            bandwidth=bandwidth,
            percent_b=percent_b,
        )

    def _calculate_adaptive_multiplier(self, df: pd.DataFrame) -> pd.Series:
        """Calculate adaptive multiplier based on ATR."""
        # Calculate ATR
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()

        # Normalize ATR to create multiplier
        # Higher volatility = wider bands
        atr_normalized = atr / close

        # Scale to reasonable range (1.5 to 3.0)
        min_mult, max_mult = 1.5, 3.0
        multiplier = min_mult + (atr_normalized * 100)
        multiplier = multiplier.clip(min_mult, max_mult)

        return multiplier.fillna(self.std_dev)

    def _empty_result(self, df: pd.DataFrame) -> BollingerBandsResult:
        """Return empty result structure."""
        empty_series = pd.Series(index=df.index, dtype=float)
        return BollingerBandsResult(
            upper_band=empty_series,
            middle_band=empty_series,
            lower_band=empty_series,
            bandwidth=empty_series,
            percent_b=empty_series,
        )

    def detect_squeeze(self, bandwidth: pd.Series, lookback: int = 100) -> bool:
        """
        Detect Bollinger Band squeeze (low volatility condition).

        Squeeze = bandwidth is in lowest 20% of recent values
        """
        if len(bandwidth) < lookback:
            return False

        recent_bandwidth = bandwidth.iloc[-lookback:]
        current_bandwidth = bandwidth.iloc[-1]

        percentile_20 = recent_bandwidth.quantile(0.20)

        return current_bandwidth <= percentile_20

    def detect_expansion(self, bandwidth: pd.Series, lookback: int = 100) -> bool:
        """
        Detect Bollinger Band expansion (high volatility condition).

        Expansion = bandwidth is in highest 20% of recent values
        """
        if len(bandwidth) < lookback:
            return False

        recent_bandwidth = bandwidth.iloc[-lookback:]
        current_bandwidth = bandwidth.iloc[-1]

        percentile_80 = recent_bandwidth.quantile(0.80)

        return current_bandwidth >= percentile_80


def calculate_bollinger_bands(
    df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, adaptive: bool = True
) -> BollingerBandsResult:
    """Quick Bollinger Bands calculation function."""
    bb = AdaptiveBollingerBands(period=period, std_dev=std_dev, adaptive=adaptive)
    return bb.calculate(df)
