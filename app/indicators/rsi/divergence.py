"""RSI Divergence Detection."""

import pandas as pd


class RSIDivergence:
    """Detect RSI divergences for advanced signal confirmation."""

    @staticmethod
    def detect_bullish_divergence(
        prices: pd.Series, rsi: pd.Series, lookback: int = 20
    ) -> bool:
        """Detect bullish divergence (price makes lower low, RSI makes higher low)."""
        if len(prices) < lookback or len(rsi) < lookback:
            return False

        recent_prices = prices.iloc[-lookback:]
        recent_rsi = rsi.iloc[-lookback:]

        # Find price lows
        price_lows = recent_prices.nsmallest(2)
        if len(price_lows) < 2:
            return False

        # Price making lower low
        price_lower_low = price_lows.iloc[-1] < price_lows.iloc[0]

        # Find corresponding RSI values
        rsi_at_lows = recent_rsi.loc[price_lows.index]

        # RSI making higher low
        rsi_higher_low = rsi_at_lows.iloc[-1] > rsi_at_lows.iloc[0]

        return price_lower_low and rsi_higher_low

    @staticmethod
    def detect_bearish_divergence(
        prices: pd.Series, rsi: pd.Series, lookback: int = 20
    ) -> bool:
        """Detect bearish divergence (price makes higher high, RSI makes lower high)."""
        if len(prices) < lookback or len(rsi) < lookback:
            return False

        recent_prices = prices.iloc[-lookback:]
        recent_rsi = rsi.iloc[-lookback:]

        # Find price highs
        price_highs = recent_prices.nlargest(2)
        if len(price_highs) < 2:
            return False

        # Price making higher high
        price_higher_high = price_highs.iloc[-1] > price_highs.iloc[0]

        # Find corresponding RSI values
        rsi_at_highs = recent_rsi.loc[price_highs.index]

        # RSI making lower high
        rsi_lower_high = rsi_at_highs.iloc[-1] < rsi_at_highs.iloc[0]

        return price_higher_high and rsi_lower_high
