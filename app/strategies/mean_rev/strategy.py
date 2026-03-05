"""Enhanced Mean Reversion Strategy main class."""

import pandas as pd

from app.core.enums import RSISmoothing, VolatilityRegime
from app.indicators.bollinger import AdaptiveBollingerBands
from app.indicators.rsi import (
    ModernRSI,
    MultiTimeframeRSI,
    RSIConfig,
    RSIDivergence,
)
from app.utils.logger import logger

from .generator import MeanReversionSignalGenerator
from .signals import MeanReversionSignal


class EnhancedMeanReversionStrategy:
    """Enhanced Mean Reversion with multi-factor confirmation."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H1",
        bb_period: int = 20,
        bb_std_dev: float = 2.5,
        rsi_period: int = 14,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        min_confidence: float = 70.0,
        min_risk_reward: float = 2.0,
    ):
        """Initialize Enhanced Mean Reversion strategy."""
        self.symbol = symbol
        self.timeframe = timeframe
        self.min_confidence = min_confidence

        self.bb_calculator = AdaptiveBollingerBands(
            period=bb_period, std_dev=bb_std_dev, adaptive=True
        )

        rsi_config = RSIConfig(
            period=rsi_period,
            oversold=rsi_oversold,
            overbought=rsi_overbought,
            smoothing=RSISmoothing.WILDER,
        )
        self.rsi_calculator = ModernRSI(rsi_config)
        self.mtf_rsi = MultiTimeframeRSI(rsi_config)
        self.divergence_detector = RSIDivergence()

        self.generator = MeanReversionSignalGenerator(
            rsi_calculator=self.rsi_calculator,
            divergence_detector=self.divergence_detector,
            min_confidence=min_confidence,
            min_risk_reward=min_risk_reward,
        )

    def analyze(
        self, df: pd.DataFrame, mtf_data: dict[str, pd.DataFrame] | None = None
    ) -> MeanReversionSignal | None:
        """Analyze market for mean reversion setup."""
        if len(df) < 50:
            logger.warning("Not enough data for mean reversion analysis")
            return None

        bb_result = self.bb_calculator.calculate(df)
        rsi_series = self.rsi_calculator.calculate(df["close"])

        if rsi_series.empty:
            return None

        volatility_state = self._classify_volatility_regime(bb_result)

        if volatility_state == VolatilityRegime.HIGH:
            logger.info("Volatility too high for mean reversion")
            return None

        current_price = df.iloc[-1]["close"]
        current_rsi = rsi_series.iloc[-1]
        bb_position = bb_result.get_current_position(current_price)

        if (
            bb_position in ["BELOW_LOWER", "NEAR_LOWER"]
            and current_rsi < self.rsi_calculator.config.oversold
        ):
            signal = self.generator.generate_buy_signal(
                df, current_price, bb_result, rsi_series, mtf_data, volatility_state
            )
            if signal:
                return signal

        elif (
            bb_position in ["ABOVE_UPPER", "NEAR_UPPER"]
            and current_rsi > self.rsi_calculator.config.overbought
        ):
            signal = self.generator.generate_sell_signal(
                df, current_price, bb_result, rsi_series, mtf_data, volatility_state
            )
            if signal:
                return signal

        return None

    def _classify_volatility_regime(self, bb_result) -> VolatilityRegime:
        """Classify current volatility regime."""
        if self.bb_calculator.detect_squeeze(bb_result.bandwidth):
            return VolatilityRegime.LOW
        elif self.bb_calculator.detect_expansion(bb_result.bandwidth):
            return VolatilityRegime.HIGH
        return VolatilityRegime.MEDIUM
