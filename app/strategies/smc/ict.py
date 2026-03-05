"""Smart Money Concepts (ICT) Trading Strategy."""

import pandas as pd

from app.core.enums import MarketRegime, SignalAction
from app.strategies.filters import FilterMixin
from app.utils.logger import logger

from .blocks import OrderBlock, OrderBlockDetector
from .fvg import FairValueGap, FairValueGapDetector
from .models import ICTSignal
from .structure import MarketStructureAnalyzer, StructureBreak


class SmartMoneyStrategy(FilterMixin):
    """Smart Money Concepts (ICT) Trading Strategy."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "H4",
        min_risk_reward: float = 2.0,
        min_confidence: float = 70.0,
        use_volatility_filter: bool = True,
        use_volume_filter: bool = False,
        volatility_ma_period: int = 20,
        volume_ma_period: int = 20,
    ):
        """Initialize Smart Money strategy."""
        self.symbol = symbol
        self.timeframe = timeframe
        self.min_risk_reward = min_risk_reward
        self.min_confidence = min_confidence
        self.use_volatility_filter = use_volatility_filter
        self.use_volume_filter = use_volume_filter
        self.volatility_ma_period = volatility_ma_period
        self.volume_ma_period = volume_ma_period

        self.ob_detector = OrderBlockDetector(
            min_impulse_candles=3, impulse_strength_threshold=0.5, max_blocks=10
        )
        self.fvg_detector = FairValueGapDetector(min_gap_size_pips=5.0)
        self.structure_analyzer = MarketStructureAnalyzer(swing_lookback=5)

    def analyze(self, df: pd.DataFrame) -> ICTSignal | None:
        """Analyze market and generate trading signal."""
        if len(df) < 50:
            logger.warning("Not enough data for ICT analysis")
            return None

        if not self._check_volatility(df):
            return None
        if not self._check_volume(df):
            return None

        swings, structure_breaks = self.structure_analyzer.analyze_structure(df)
        current_trend = self.structure_analyzer.get_current_trend(structure_breaks)

        if not current_trend:
            logger.info("No clear trend identified")
            return None

        blocks = self.ob_detector.detect_blocks(df)
        fvgs = self.fvg_detector.detect_fvg(df)

        active_obs = self.ob_detector.get_active_blocks(blocks)
        active_fvgs = self.fvg_detector.get_unfilled_fvgs(fvgs)

        current_price = df.iloc[-1]["close"]

        if current_trend == MarketRegime.BULLISH:
            signal = self._check_bullish_setup(
                df, current_price, active_obs, active_fvgs, structure_breaks
            )
        elif current_trend == MarketRegime.BEARISH:
            signal = self._check_bearish_setup(
                df, current_price, active_obs, active_fvgs, structure_breaks
            )
        else:
            return None

        if signal and signal.confidence >= self.min_confidence:
            if signal.risk_reward_ratio >= self.min_risk_reward:
                logger.success(
                    f"ICT Signal: {signal.action} at {signal.entry_price:.5f} (Confidence: {signal.confidence:.1f}%, RR: {signal.risk_reward_ratio:.1f}:1)"
                )
                return signal

        return None

    def _check_bullish_setup(
        self,
        df: pd.DataFrame,
        current_price: float,
        blocks: list[OrderBlock],
        fvgs: list[FairValueGap],
        structure_breaks: list[StructureBreak],
    ) -> ICTSignal | None:
        """Check for bullish entry setup."""

        bullish_obs = [
            ob
            for ob in blocks
            if ob.type == MarketRegime.BULLISH and ob.zone_top < current_price
        ]

        bullish_fvgs = [
            fvg
            for fvg in fvgs
            if fvg.type == MarketRegime.BULLISH and fvg.top < current_price
        ]

        nearest_ob = self.ob_detector.get_nearest_order_block(
            bullish_obs, current_price, MarketRegime.BULLISH
        )

        nearest_fvg = min(
            bullish_fvgs, key=lambda x: abs(current_price - x.mid), default=None
        )

        entry_zone = None
        confidence = 50.0
        reason_parts = []

        if nearest_ob:
            distance_to_ob = (
                (current_price - nearest_ob.zone_mid) / current_price
            ) * 100

            if distance_to_ob < 1.0:
                entry_zone = nearest_ob
                confidence += 25.0
                confidence += min(nearest_ob.strength / 4, 15.0)
                reason_parts.append(f"Bullish OB at {nearest_ob.zone_mid:.5f}")

        if nearest_fvg:
            distance_to_fvg = ((current_price - nearest_fvg.mid) / current_price) * 100

            if distance_to_fvg < 0.5:
                if entry_zone:
                    confidence += 10.0
                    reason_parts.append("+ FVG confluence")
                else:
                    entry_zone = nearest_fvg
                    confidence += 20.0
                    reason_parts.append(f"Bullish FVG at {nearest_fvg.mid:.5f}")

        if not entry_zone:
            return None

        recent_bos = self.structure_analyzer.get_recent_bos(structure_breaks)
        if recent_bos and recent_bos.direction == MarketRegime.BULLISH:
            confidence += 10.0
            reason_parts.append("BOS confirmation")

        if isinstance(entry_zone, OrderBlock):
            entry_price = entry_zone.zone_mid
            stop_loss = entry_zone.zone_bottom - (entry_zone.size * 0.1)
            take_profit = entry_price + (abs(entry_price - stop_loss) * 2.5)
        else:
            entry_price = entry_zone.mid
            stop_loss = entry_zone.bottom - (entry_zone.size * 0.1)
            take_profit = entry_price + (abs(entry_price - stop_loss) * 2.5)

        reason = "BULLISH: " + ", ".join(reason_parts)

        return ICTSignal(
            action=SignalAction.BUY,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=min(confidence, 100.0),
            reason=reason,
            order_block=nearest_ob,
            fvg=nearest_fvg,
        )

    def _check_bearish_setup(
        self,
        df: pd.DataFrame,
        current_price: float,
        blocks: list[OrderBlock],
        fvgs: list[FairValueGap],
        structure_breaks: list[StructureBreak],
    ) -> ICTSignal | None:
        """Check for bearish entry setup."""

        bearish_obs = [
            ob
            for ob in blocks
            if ob.type == MarketRegime.BEARISH and ob.zone_bottom > current_price
        ]

        bearish_fvgs = [
            fvg
            for fvg in fvgs
            if fvg.type == MarketRegime.BEARISH and fvg.bottom > current_price
        ]

        nearest_ob = self.ob_detector.get_nearest_order_block(
            bearish_obs, current_price, MarketRegime.BEARISH
        )

        nearest_fvg = min(
            bearish_fvgs, key=lambda x: abs(current_price - x.mid), default=None
        )

        entry_zone = None
        confidence = 50.0
        reason_parts = []

        if nearest_ob:
            distance_to_ob = (
                (nearest_ob.zone_mid - current_price) / current_price
            ) * 100

            if distance_to_ob < 1.0:
                entry_zone = nearest_ob
                confidence += 25.0
                confidence += min(nearest_ob.strength / 4, 15.0)
                reason_parts.append(f"Bearish OB at {nearest_ob.zone_mid:.5f}")

        if nearest_fvg:
            distance_to_fvg = ((nearest_fvg.mid - current_price) / current_price) * 100

            if distance_to_fvg < 0.5:
                if entry_zone:
                    confidence += 10.0
                    reason_parts.append("+ FVG confluence")
                else:
                    entry_zone = nearest_fvg
                    confidence += 20.0
                    reason_parts.append(f"Bearish FVG at {nearest_fvg.mid:.5f}")

        if not entry_zone:
            return None

        recent_bos = self.structure_analyzer.get_recent_bos(structure_breaks)
        if recent_bos and recent_bos.direction == MarketRegime.BEARISH:
            confidence += 10.0
            reason_parts.append("BOS confirmation")

        if isinstance(entry_zone, OrderBlock):
            entry_price = entry_zone.zone_mid
            stop_loss = entry_zone.zone_top + (entry_zone.size * 0.1)
            take_profit = entry_price - (abs(stop_loss - entry_price) * 2.5)
        else:
            entry_price = entry_zone.mid
            stop_loss = entry_zone.top + (entry_zone.size * 0.1)
            take_profit = entry_price - (abs(stop_loss - entry_price) * 2.5)

        reason = "BEARISH: " + ", ".join(reason_parts)

        return ICTSignal(
            action=SignalAction.SELL,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=min(confidence, 100.0),
            reason=reason,
            order_block=nearest_ob,
            fvg=nearest_fvg,
        )
