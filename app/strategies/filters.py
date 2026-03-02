import pandas as pd


class FilterMixin:
    """Mixin class providing Volatility and Volume filtering capabilities for strategies."""

    # These attributes are expected to be initialized by the strategy subclass
    use_volatility_filter: bool = True
    use_volume_filter: bool = False
    volatility_ma_period: int = 20
    volume_ma_period: int = 20

    def _check_volatility(self, df: pd.DataFrame) -> bool:
        """Ensure current volatility is higher than recent average."""
        if not self.use_volatility_filter:
            return True

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        # Using period 14 for base ATR calculation
        atr_series = tr.ewm(span=14, adjust=False).mean()

        atr = atr_series.iloc[-1]
        atr_ma = atr_series.rolling(window=self.volatility_ma_period).mean().iloc[-1]

        # Don't trade if volatility is below the moving average
        return atr >= atr_ma

    def _check_volume(self, df: pd.DataFrame) -> bool:
        """Ensure current volume is higher than recent average."""
        if not self.use_volume_filter:
            return True

        vol_col = "tickVolume" if "tickVolume" in df.columns else "volume"
        if vol_col not in df.columns:
            return True  # Cannot filter without volume data

        current_vol = df[vol_col].iloc[-1]
        vol_ma = df[vol_col].rolling(window=self.volume_ma_period).mean().iloc[-1]

        # Require stronger closing volume
        return current_vol >= vol_ma
