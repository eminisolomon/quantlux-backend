import pandas as pd

from app.core.enums import SignalAction
from app.strategies.filters import FilterMixin
from app.strategies.momentum.models import MomentumSignal
from app.utils.logger import logger


class MomentumStrategy(FilterMixin):
    """
    Momentum Strategy base on Donchian Channel breakout.

    Logic:
    1. Define upper and lower channels as N-period high/low.
    2. Enter BUY when price closes above the upper channel.
    3. Enter SELL when price closes below the lower channel.
    4. Confirm with Volatility and Volume filters.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        channel_period: int = 20,
        atr_period: int = 14,
        min_risk_reward: float = 2.0,
        use_volatility_filter: bool = True,
        use_volume_filter: bool = False,
        volatility_ma_period: int = 20,
        volume_ma_period: int = 20,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.channel_period = channel_period
        self.atr_period = atr_period
        self.min_risk_reward = min_risk_reward
        self.use_volatility_filter = use_volatility_filter
        self.use_volume_filter = use_volume_filter
        self.volatility_ma_period = volatility_ma_period
        self.volume_ma_period = volume_ma_period

    def analyze(self, df: pd.DataFrame) -> MomentumSignal | None:
        """Analyze market for Momentum setups."""
        required_len = (
            max(
                self.channel_period,
                self.atr_period,
                self.volatility_ma_period,
                self.volume_ma_period,
            )
            + 1
        )
        if len(df) < required_len:
            logger.warning(
                f"Not enough data for Momentum analysis. Need {required_len}, got {len(df)}"
            )
            return None

        if not self._check_volatility(df):
            return None
        if not self._check_volume(df):
            return None

        df["upper_channel"] = (
            df["high"].rolling(window=self.channel_period).max().shift(1)
        )
        df["lower_channel"] = (
            df["low"].rolling(window=self.channel_period).min().shift(1)
        )

        current_close = df["close"].iloc[-1]
        prev_upper = df["upper_channel"].iloc[-1]
        prev_lower = df["lower_channel"].iloc[-1]

        atr = self._calculate_atr(df, self.atr_period)

        if pd.isna(prev_upper) or pd.isna(prev_lower):
            return None

        if current_close > prev_upper:
            stop_loss = current_close - (atr * 2.0)
            take_profit = current_close + (atr * 4.0)

            risk = current_close - stop_loss
            if risk > 0:
                rr = (take_profit - current_close) / risk
                if rr < self.min_risk_reward:
                    take_profit = current_close + (risk * self.min_risk_reward)
                    rr = self.min_risk_reward
            else:
                rr = 0

            return MomentumSignal(
                action=SignalAction.BUY,
                entry_price=current_close,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=80.0,
                reason="Bullish Donchian Breakout",
                risk_reward_ratio=rr,
            )

        if current_close < prev_lower:
            stop_loss = current_close + (atr * 2.0)
            take_profit = current_close - (atr * 4.0)

            risk = stop_loss - current_close
            if risk > 0:
                rr = (current_close - take_profit) / risk
                if rr < self.min_risk_reward:
                    take_profit = current_close - (risk * self.min_risk_reward)
                    rr = self.min_risk_reward
            else:
                rr = 0

            return MomentumSignal(
                action=SignalAction.SELL,
                entry_price=current_close,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=80.0,
                reason="Bearish Donchian Breakout",
                risk_reward_ratio=rr,
            )

        return None

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR for dynamic stop loss."""
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean().iloc[-1]
        return atr
