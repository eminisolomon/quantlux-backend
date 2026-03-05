"""Signal generation logic for Mean Reversion strategy."""

import pandas as pd

from app.core.enums import SignalAction, VolatilityRegime
from app.indicators.bollinger import BollingerBandsResult
from app.indicators.rsi import ModernRSI, RSIDivergence
from app.strategies.mean_rev.signals import MeanReversionSignal


class MeanReversionSignalGenerator:
    """Generates trading signals based on market analysis."""

    def __init__(
        self,
        rsi_calculator: ModernRSI,
        divergence_detector: RSIDivergence,
        min_confidence: float = 70.0,
        min_risk_reward: float = 2.0,
    ):
        self.rsi_calculator = rsi_calculator
        self.divergence_detector = divergence_detector
        self.min_confidence = min_confidence
        self.min_risk_reward = min_risk_reward

    def generate_buy_signal(
        self,
        df: pd.DataFrame,
        current_price: float,
        bb_result: BollingerBandsResult,
        rsi_series: pd.Series,
        mtf_data: dict[str, pd.DataFrame] | None,
        volatility_state: VolatilityRegime,
    ) -> MeanReversionSignal | None:
        """Generate buy signal with confirmation."""
        confidence = 50.0
        reason_parts = []
        rsi_values = {}

        current_rsi = rsi_series.iloc[-1]
        rsi_values["primary"] = current_rsi

        if current_rsi < 25:
            confidence += 20.0
            reason_parts.append(f"Strong oversold RSI {current_rsi:.1f}")
        elif current_rsi < 30:
            confidence += 15.0
            reason_parts.append(f"Oversold RSI {current_rsi:.1f}")

        percent_b = bb_result.percent_b.iloc[-1]
        if percent_b < 0:
            confidence += 15.0
            reason_parts.append("Price below lower BB")
        elif percent_b < 0.1:
            confidence += 10.0
            reason_parts.append("Price near lower BB")

        if mtf_data:
            mtf_oversold = self._check_mtf_oversold(mtf_data, rsi_values)
            if mtf_oversold >= 2:
                confidence += 15.0
                reason_parts.append(f"{mtf_oversold} TF oversold")

        if self.divergence_detector.detect_bullish_divergence(
            df["close"], rsi_series, lookback=20
        ):
            confidence += 15.0
            reason_parts.append("Bullish divergence")

        if volatility_state == VolatilityRegime.LOW:
            confidence += 5.0
            reason_parts.append("Low volatility")

        lower_band = bb_result.lower_band.iloc[-1]
        middle_band = bb_result.middle_band.iloc[-1]

        entry_price = current_price
        stop_loss = lower_band - (middle_band - lower_band) * 0.2
        take_profit = middle_band

        risk = abs(entry_price - stop_loss)
        if risk > 0 and (take_profit - entry_price) / risk < self.min_risk_reward:
            take_profit = entry_price + (risk * self.min_risk_reward)

        reason = "BUY (Mean Reversion): " + ", ".join(reason_parts)

        if confidence < self.min_confidence:
            return None

        return MeanReversionSignal(
            action=SignalAction.BUY,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=min(confidence, 100.0),
            reason=reason,
            rsi_values=rsi_values,
            bb_position=bb_result.get_current_position(current_price),
            volatility_state=volatility_state,
        )

    def generate_sell_signal(
        self,
        df: pd.DataFrame,
        current_price: float,
        bb_result: BollingerBandsResult,
        rsi_series: pd.Series,
        mtf_data: dict[str, pd.DataFrame] | None,
        volatility_state: VolatilityRegime,
    ) -> MeanReversionSignal | None:
        """Generate sell signal with confirmation."""
        confidence = 50.0
        reason_parts = []
        rsi_values = {}

        current_rsi = rsi_series.iloc[-1]
        rsi_values["primary"] = current_rsi

        if current_rsi > 75:
            confidence += 20.0
            reason_parts.append(f"Strong overbought RSI {current_rsi:.1f}")
        elif current_rsi > 70:
            confidence += 15.0
            reason_parts.append(f"Overbought RSI {current_rsi:.1f}")

        percent_b = bb_result.percent_b.iloc[-1]
        if percent_b > 1.0:
            confidence += 15.0
            reason_parts.append("Price above upper BB")
        elif percent_b > 0.9:
            confidence += 10.0
            reason_parts.append("Price near upper BB")

        if mtf_data:
            mtf_overbought = self._check_mtf_overbought(mtf_data, rsi_values)
            if mtf_overbought >= 2:
                confidence += 15.0
                reason_parts.append(f"{mtf_overbought} TF overbought")

        if self.divergence_detector.detect_bearish_divergence(
            df["close"], rsi_series, lookback=20
        ):
            confidence += 15.0
            reason_parts.append("Bearish divergence")

        if volatility_state == VolatilityRegime.LOW:
            confidence += 5.0
            reason_parts.append("Low volatility")

        upper_band = bb_result.upper_band.iloc[-1]
        middle_band = bb_result.middle_band.iloc[-1]

        entry_price = current_price
        stop_loss = upper_band + (upper_band - middle_band) * 0.2
        take_profit = middle_band

        risk = abs(stop_loss - entry_price)
        if risk > 0 and (entry_price - take_profit) / risk < self.min_risk_reward:
            take_profit = entry_price - (risk * self.min_risk_reward)

        reason = "SELL (Mean Reversion): " + ", ".join(reason_parts)

        if confidence < self.min_confidence:
            return None

        return MeanReversionSignal(
            action=SignalAction.SELL,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=min(confidence, 100.0),
            reason=reason,
            rsi_values=rsi_values,
            bb_position=bb_result.get_current_position(current_price),
            volatility_state=volatility_state,
        )

    def _check_mtf_oversold(
        self, mtf_data: dict[str, pd.DataFrame], rsi_values: dict
    ) -> int:
        """Check how many timeframes show oversold RSI."""
        oversold_count = 0
        for tf, df in mtf_data.items():
            if len(df) >= self.rsi_calculator.config.period:
                rsi = self.rsi_calculator.calculate(df["close"])
                if not rsi.empty:
                    current_rsi = rsi.iloc[-1]
                    rsi_values[tf] = current_rsi
                    if current_rsi < self.rsi_calculator.config.oversold:
                        oversold_count += 1
        return oversold_count

    def _check_mtf_overbought(
        self, mtf_data: dict[str, pd.DataFrame], rsi_values: dict
    ) -> int:
        """Check how many timeframes show overbought RSI."""
        overbought_count = 0
        for tf, df in mtf_data.items():
            if len(df) >= self.rsi_calculator.config.period:
                rsi = self.rsi_calculator.calculate(df["close"])
                if not rsi.empty:
                    current_rsi = rsi.iloc[-1]
                    rsi_values[tf] = current_rsi
                    if current_rsi > self.rsi_calculator.config.overbought:
                        overbought_count += 1
        return overbought_count
