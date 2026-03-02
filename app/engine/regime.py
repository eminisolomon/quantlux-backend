"""Market Regime Detection module using ADX and MA."""

from enum import Enum
import pandas as pd
from app.indicators.adx import calculate_adx


class MarketRegimeType(Enum):
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"


class MarketRegimeDetector:
    """
    Detects the current market regime using ADX and EMAs.
    ADX determines trend strength, while EMAs determine direction.
    """

    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        fast_ema: int = 20,
        slow_ema: int = 50,
    ):
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema

    def detect(self, df: pd.DataFrame) -> MarketRegimeType:
        """
        Detect regime from DataFrame containing OHLC data.
        """
        if df.empty or len(df) < self.slow_ema:
            return MarketRegimeType.RANGING

        # Calculate Indicators
        adx_df = calculate_adx(df, period=self.adx_period)
        ema_fast = df["close"].ewm(span=self.fast_ema, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow_ema, adjust=False).mean()

        current_adx = adx_df["ADX"].iloc[-1]
        pos_di = adx_df["+DI"].iloc[-1]
        neg_di = adx_df["-DI"].iloc[-1]

        current_fast = ema_fast.iloc[-1]
        current_slow = ema_slow.iloc[-1]

        # Check Trend Strength
        is_trending = current_adx >= self.adx_threshold

        if is_trending:
            # Bullish: +DI > -DI and Fast EMA > Slow EMA
            if pos_di > neg_di and current_fast > current_slow:
                return MarketRegimeType.TRENDING_BULL
            # Bearish: -DI > +DI and Fast EMA < Slow EMA
            elif neg_di > pos_di and current_fast < current_slow:
                return MarketRegimeType.TRENDING_BEAR
            else:
                return MarketRegimeType.VOLATILE
        else:
            return MarketRegimeType.RANGING
