"""RSI Pattern Analysis Logic."""

import pandas as pd

from app.core.enums import MarketRegime


class RSIAnalyzer:
    """Advanced RSI pattern analysis."""

    @staticmethod
    def classify_regime(rsi_series: pd.Series, period: int = 50) -> MarketRegime:
        """Classify the current market regime based on RSI behavior."""
        if len(rsi_series) < period:
            return MarketRegime.NEUTRAL

        recent_rsi = rsi_series.iloc[-period:]
        min_rsi = recent_rsi.min()
        max_rsi = recent_rsi.max()
        avg_rsi = recent_rsi.mean()

        # Bullish rules
        if min_rsi >= 35 and max_rsi > 65 and avg_rsi > 50:
            return MarketRegime.BULLISH

        # Bearish rules
        if max_rsi <= 65 and min_rsi < 35 and avg_rsi < 50:
            return MarketRegime.BEARISH

        return MarketRegime.NEUTRAL

    @staticmethod
    def detect_failure_swing_bottom(rsi_series: pd.Series) -> bool:
        """
        Detect Bullish Failure Swing (W-bottom on RSI).

        Pattern:
        1. RSI drops below 30 (Oversold).
        2. RSI bounces back above 30.
        3. RSI pulls back but holds ABOVE the previous low (Fail point).
        4. RSI breaks above its recent high.
        """
        if len(rsi_series) < 5:
            return False

        # Get last 5 points for pattern recognition
        p1, p2, p3, p4, current = rsi_series.iloc[-5:].values

        # 1. Swing Low (< 30) (p1 or p2)
        swing_low_formed = p1 < 30 or p2 < 30

        # 2. Bounce (High)
        bounce_high = max(p2, p3)

        # 3. Higher Low (The "Failure")
        failure_low = min(p3, p4)
        is_higher_low = failure_low > min(p1, p2)

        # 4. Breakout
        breakout = current > bounce_high

        return swing_low_formed and is_higher_low and breakout

    @staticmethod
    def detect_failure_swing_top(rsi_series: pd.Series) -> bool:
        """
        Detect Bearish Failure Swing (M-top on RSI).

        Pattern:
        1. RSI goes above 70 (Overbought).
        2. RSI pulls back below 70.
        3. RSI rallies but fails to exceed previous high.
        4. RSI breaks below its recent low.
        """
        if len(rsi_series) < 5:
            return False

        p1, p2, p3, p4, current = rsi_series.iloc[-5:].values

        # 1. Swing High (> 70)
        swing_high_formed = p1 > 70 or p2 > 70

        # 2. Pullback (Low)
        pullback_low = min(p2, p3)

        # 3. Lower High (The "Failure")
        failure_high = max(p3, p4)
        is_lower_high = failure_high < max(p1, p2)

        # 4. Breakdown
        breakdown = current < pullback_low

        return swing_high_formed and is_lower_high and breakdown
