"""
Smart Money Concepts - Market Structure Analysis

Analyzes market structure through Break of Structure (BOS) and
Change of Character (ChoCH) to identify trend continuation and reversals.
"""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from app.core.enums import MarketRegime, StructureType, SwingType
from app.utils.logger import logger


@dataclass
class StructurePoint:
    """Represents a swing high or swing low."""

    type: SwingType
    price: float
    time: datetime
    index: int


@dataclass
class StructureBreak:
    """Represents a break of market structure."""

    type: StructureType  # Break of Structure or Change of Character
    direction: MarketRegime
    price: float
    time: datetime
    previous_structure: StructurePoint


class MarketStructureAnalyzer:
    """Analyzes market structure through BOS and ChoCH for trend identification."""

    def __init__(self, swing_lookback: int = 5):
        """Initialize market structure analyzer."""
        self.swing_lookback = swing_lookback
        self.current_trend: MarketRegime | None = None

    def analyze_structure(
        self, df: pd.DataFrame
    ) -> tuple[list[StructurePoint], list[StructureBreak]]:
        """Analyze market structure. Returns (swing_points, structure_breaks)."""
        # Find swing highs and lows
        swing_highs = self._find_swing_highs(df)
        swing_lows = self._find_swing_lows(df)

        # Combine and sort by time
        all_swings = sorted(swing_highs + swing_lows, key=lambda x: x.index)

        # Identify structure breaks
        structure_breaks = self._identify_structure_breaks(all_swings, df)

        logger.info(
            f"Found {len(all_swings)} swing points, {len(structure_breaks)} structure breaks"
        )
        return all_swings, structure_breaks

    def _find_swing_highs(self, df: pd.DataFrame) -> list[StructurePoint]:
        """Find swing high points."""
        swing_highs = []

        for i in range(self.swing_lookback, len(df) - self.swing_lookback):
            current_high = df.iloc[i]["high"]

            # Check if this is higher than surrounding candles
            is_swing_high = True

            for j in range(i - self.swing_lookback, i + self.swing_lookback + 1):
                if j != i and df.iloc[j]["high"] >= current_high:
                    is_swing_high = False
                    break

            if is_swing_high:
                swing_highs.append(
                    StructurePoint(
                        type=SwingType.HIGH,
                        price=current_high,
                        time=(
                            df.iloc[i]["time"] if "time" in df.iloc[i] else df.index[i]
                        ),
                        index=i,
                    )
                )

        return swing_highs

    def _find_swing_lows(self, df: pd.DataFrame) -> list[StructurePoint]:
        """Find swing low points."""
        swing_lows = []

        for i in range(self.swing_lookback, len(df) - self.swing_lookback):
            current_low = df.iloc[i]["low"]

            # Check if this is lower than surrounding candles
            is_swing_low = True

            for j in range(i - self.swing_lookback, i + self.swing_lookback + 1):
                if j != i and df.iloc[j]["low"] <= current_low:
                    is_swing_low = False
                    break

            if is_swing_low:
                swing_lows.append(
                    StructurePoint(
                        type=SwingType.LOW,
                        price=current_low,
                        time=(
                            df.iloc[i]["time"] if "time" in df.iloc[i] else df.index[i]
                        ),
                        index=i,
                    )
                )

        return swing_lows

    def _identify_structure_breaks(
        self, swings: list[StructurePoint], df: pd.DataFrame
    ) -> list[StructureBreak]:
        """Identify BOS and ChoCH from swing points."""
        structure_breaks = []

        if len(swings) < 2:
            return structure_breaks

        for i in range(1, len(swings)):
            current_swing = swings[i]
            previous_swing = swings[i - 1]

            # Skip if same type consecutive
            if current_swing.type == previous_swing.type:
                continue

            # Check for bullish structure break
            if (
                current_swing.type == SwingType.HIGH
                and previous_swing.type == SwingType.LOW
            ):
                if current_swing.price > previous_swing.price:
                    # Price made higher high - bullish
                    break_type = (
                        StructureType.BOS
                        if self.current_trend == MarketRegime.BULLISH
                        else StructureType.CHOCH
                    )

                    structure_breaks.append(
                        StructureBreak(
                            type=break_type,
                            direction=MarketRegime.BULLISH,
                            price=current_swing.price,
                            time=current_swing.time,
                            previous_structure=previous_swing,
                        )
                    )

                    if break_type == StructureType.CHOCH:
                        self.current_trend = MarketRegime.BULLISH

            # Check for bearish structure break
            elif (
                current_swing.type == SwingType.LOW
                and previous_swing.type == SwingType.HIGH
            ):
                if current_swing.price < previous_swing.price:
                    # Price made lower low - bearish
                    break_type = (
                        StructureType.BOS
                        if self.current_trend == MarketRegime.BEARISH
                        else StructureType.CHOCH
                    )

                    structure_breaks.append(
                        StructureBreak(
                            type=break_type,
                            direction=MarketRegime.BEARISH,
                            price=current_swing.price,
                            time=current_swing.time,
                            previous_structure=previous_swing,
                        )
                    )

                    if break_type == StructureType.CHOCH:
                        self.current_trend = MarketRegime.BEARISH

        return structure_breaks

    def get_current_trend(
        self, structure_breaks: list[StructureBreak]
    ) -> MarketRegime | None:
        """Get current market trend based on structure breaks."""
        if not structure_breaks:
            return None

        # Get most recent structure break
        recent_break = structure_breaks[-1]

        if recent_break.type in [StructureType.CHOCH, StructureType.BOS]:
            return recent_break.direction

        return None

    def get_recent_bos(
        self, structure_breaks: list[StructureBreak]
    ) -> StructureBreak | None:
        """Get most recent Break of Structure."""
        bos_breaks = [sb for sb in structure_breaks if sb.type == StructureType.BOS]
        return bos_breaks[-1] if bos_breaks else None

    def get_recent_choch(
        self, structure_breaks: list[StructureBreak]
    ) -> StructureBreak | None:
        """Get most recent Change of Character."""
        choch_breaks = [sb for sb in structure_breaks if sb.type == StructureType.CHOCH]
        return choch_breaks[-1] if choch_breaks else None
