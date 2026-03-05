"""Advanced RSI Strategy."""

import pandas as pd

from app.core.enums import MarketRegime, RSIPattern, SignalAction
from app.indicators.rsi import (
    ModernRSI,
    MultiTimeframeRSI,
    RSIConfig,
    RSIDivergence,
)
from app.indicators.utils import is_falling, is_rising
from app.schemas import TradeSignal, RSISignal
from app.strategies.filters import FilterMixin
from app.strategies.rsi.analysis import RSIAnalyzer


class RSIStrategy(FilterMixin):
    """
    Advanced RSI Strategy incorporating Regime and Pattern Analysis.

    Logic:
    1. Determine Market Regime (Bullish/Bearish) using RSI ranges.
    2. Identify High-Probability Patterns (Failure Swings, Divergences).
    3. Confirm with Multi-Timeframe Analysis.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        min_confidence: float = 70.0,
        min_risk_reward: float = 2.0,
        use_volatility_filter: bool = True,
        use_volume_filter: bool = False,
        volatility_ma_period: int = 20,
        volume_ma_period: int = 20,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.min_confidence = min_confidence
        self.min_risk_reward = min_risk_reward
        self.use_volatility_filter = use_volatility_filter
        self.use_volume_filter = use_volume_filter
        self.volatility_ma_period = volatility_ma_period
        self.volume_ma_period = volume_ma_period

        self.config = RSIConfig(
            period=rsi_period, oversold=oversold, overbought=overbought
        )
        self.rsi_calculator = ModernRSI(self.config)
        self.mtf_rsi = MultiTimeframeRSI(self.config)
        self.divergence_detector = RSIDivergence()
        self.analyzer = RSIAnalyzer()

    def analyze(
        self, df: pd.DataFrame, mtf_data: dict[str, pd.DataFrame] | None = None
    ) -> RSISignal | None:
        """Analyze market for advanced RSI setups."""
        if len(df) < 50:
            return None

        rsi_series = self.rsi_calculator.calculate(df["close"])
        if rsi_series.empty:
            return None

        if not self._check_volatility(df):
            return None
        if not self._check_volume(df):
            return None

        current_price = df.iloc[-1]["close"]
        current_rsi = rsi_series.iloc[-1]

        regime = self.analyzer.classify_regime(rsi_series)

        if regime in [MarketRegime.BULLISH, MarketRegime.NEUTRAL]:
            signal = self._check_bullish_setup(
                df, rsi_series, current_price, current_rsi, regime, mtf_data
            )
            if signal and signal.confidence >= self.min_confidence:
                return signal

        if regime in [MarketRegime.BEARISH, MarketRegime.NEUTRAL]:
            signal = self._check_bearish_setup(
                df, rsi_series, current_price, current_rsi, regime, mtf_data
            )
            if signal and signal.confidence >= self.min_confidence:
                return signal

        return None

    def _check_bullish_setup(
        self,
        df: pd.DataFrame,
        rsi_series: pd.Series,
        price: float,
        rsi: float,
        regime: MarketRegime,
        mtf_data: dict[str, pd.DataFrame] | None,
    ) -> RSISignal | None:
        """Check for bullish patterns."""
        confidence = 50.0
        reasons = []
        pattern = RSIPattern.OVERSOLD

        if self.analyzer.detect_failure_swing_bottom(rsi_series):
            confidence += 25.0
            reasons.append("Bullish Failure Swing")
            pattern = RSIPattern.FAILURE_SWING

        if self.divergence_detector.detect_bullish_divergence(df["close"], rsi_series):
            confidence += 20.0
            reasons.append("Bullish Divergence")
            pattern = RSIPattern.DIVERGENCE

        if rsi < self.config.oversold:
            confidence += 10.0
            reasons.append(f"Oversold ({rsi:.1f})")

            if regime == MarketRegime.BULLISH:
                confidence += 10.0
                reasons.append("Bullish Regime Dip")

        if mtf_data:
            mtf_score = self._check_mtf_confluence(mtf_data, SignalAction.BUY)
            if mtf_score > 0:
                confidence += 10.0
                reasons.append(f"MTF Confirmation (+{mtf_score})")

        if confidence < self.min_confidence:
            return None

        atr = self._calculate_atr(df)
        stop_loss = price - (atr * 2.0)
        take_profit = price + (atr * 4.0)

        risk = price - stop_loss
        if risk > 0:
            rr = (take_profit - price) / risk
            if rr < self.min_risk_reward:
                take_profit = price + (risk * self.min_risk_reward)
                rr = self.min_risk_reward
        else:
            rr = 0

        return RSISignal(
            action=SignalAction.BUY,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=min(confidence, 100.0),
            reason=", ".join(reasons),
            rsi_value=rsi,
            regime=regime,
            pattern=pattern,
        )

    def _check_bearish_setup(
        self,
        df: pd.DataFrame,
        rsi_series: pd.Series,
        price: float,
        rsi: float,
        regime: MarketRegime,
        mtf_data: dict[str, pd.DataFrame] | None,
    ) -> RSISignal | None:
        """Check for bearish patterns."""
        confidence = 50.0
        reasons = []
        pattern = RSIPattern.OVERBOUGHT

        if self.analyzer.detect_failure_swing_top(rsi_series):
            confidence += 25.0
            reasons.append("Bearish Failure Swing")
            pattern = RSIPattern.FAILURE_SWING

        if self.divergence_detector.detect_bearish_divergence(df["close"], rsi_series):
            confidence += 20.0
            reasons.append("Bearish Divergence")
            pattern = RSIPattern.DIVERGENCE

        if rsi > self.config.overbought:
            confidence += 10.0
            reasons.append(f"Overbought ({rsi:.1f})")

            if regime == MarketRegime.BEARISH:
                confidence += 10.0
                reasons.append("Bearish Regime Rally")

        if mtf_data:
            mtf_score = self._check_mtf_confluence(mtf_data, SignalAction.SELL)
            if mtf_score > 0:
                confidence += 10.0
                reasons.append(f"MTF Confirmation (+{mtf_score})")

        if confidence < self.min_confidence:
            return None

        atr = self._calculate_atr(df)
        stop_loss = price + (atr * 2.0)
        take_profit = price - (atr * 4.0)

        risk = stop_loss - price
        if risk > 0:
            rr = (price - take_profit) / risk
            if rr < self.min_risk_reward:
                take_profit = price - (risk * self.min_risk_reward)
                rr = self.min_risk_reward
        else:
            rr = 0

        return RSISignal(
            action=SignalAction.SELL,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=min(confidence, 100.0),
            reason=", ".join(reasons),
            rsi_value=rsi,
            regime=regime,
            pattern=pattern,
        )

    def _check_mtf_confluence(
        self, mtf_data: dict[str, pd.DataFrame], action: SignalAction
    ) -> int:
        """Check confirmation from higher timeframes."""
        score = 0
        for tf, df in mtf_data.items():
            rsi = self.rsi_calculator.calculate(df["close"])
            if rsi.empty:
                continue

            last_rsi = rsi.iloc[-1]

            if action == SignalAction.BUY:
                if last_rsi < 30 or (40 < last_rsi < 70 and is_rising(rsi)):
                    score += 1
            else:
                if last_rsi > 70 or (30 < last_rsi < 60 and is_falling(rsi)):
                    score += 1

        return score

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
