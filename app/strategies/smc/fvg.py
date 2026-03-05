"""
Smart Money Concepts - Fair Value Gaps (FVG) Detection

Fair Value Gaps are price imbalances created by rapid institutional moves,
leaving gaps in the orderbook that price tends to "fill" later.
"""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from app.core.enums import MarketRegime
from app.utils.logger import logger


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap (price imbalance)."""

    type: MarketRegime
    top: float
    bottom: float
    time: datetime
    filled: bool = False
    fill_percentage: float = 0.0

    @property
    def mid(self) -> float:
        """Middle of the FVG."""
        return (self.top + self.bottom) / 2

    @property
    def size(self) -> float:
        """Size of the gap."""
        return self.top - self.bottom

    def is_price_in_gap(self, price: float) -> bool:
        """Check if price is within the FVG."""
        return self.bottom <= price <= self.top

    def update_fill_status(self, high: float, low: float):
        """Update how much of the gap has been filled."""
        if self.type == MarketRegime.BULLISH:
            if low <= self.mid:
                self.filled = True
                if low <= self.bottom:
                    self.fill_percentage = 100.0
                else:
                    self.fill_percentage = ((self.top - low) / self.size) * 100
        else:
            if high >= self.mid:
                self.filled = True
                if high >= self.top:
                    self.fill_percentage = 100.0
                else:
                    self.fill_percentage = ((high - self.bottom) / self.size) * 100


class FairValueGapDetector:
    """Detects Fair Value Gaps (price imbalances) in price action."""

    def __init__(self, min_gap_size_pips: float = 5.0):
        """Initialize FVG detector."""
        self.min_gap_size_pips = min_gap_size_pips

    def detect_fvg(self, df: pd.DataFrame) -> list[FairValueGap]:
        """Detect all Fair Value Gaps in the data."""
        if len(df) < 3:
            return []

        fvgs = []

        for i in range(len(df) - 2):
            candle1 = df.iloc[i]
            candle2 = df.iloc[i + 1]
            candle3 = df.iloc[i + 2]

            bullish_fvg = self._detect_bullish_fvg(candle1, candle2, candle3)
            if bullish_fvg:
                fvgs.append(bullish_fvg)

            bearish_fvg = self._detect_bearish_fvg(candle1, candle2, candle3)
            if bearish_fvg:
                fvgs.append(bearish_fvg)

        if fvgs:
            self._update_fvg_fill_status(fvgs, df)

        logger.info(f"Detected {len(fvgs)} Fair Value Gaps")
        return fvgs

    def _detect_bullish_fvg(self, c1, c2, c3) -> FairValueGap | None:
        """
        Detect bullish FVG (gap below current price).

        Pattern: Candle 3's low > Candle 1's high
        """
        gap_bottom = c1["high"]
        gap_top = c3["low"]

        if gap_top <= gap_bottom:
            return None

        gap_size = gap_top - gap_bottom

        if gap_size < (self.min_gap_size_pips * 0.0001):
            return None

        return FairValueGap(
            type=MarketRegime.BULLISH,
            top=gap_top,
            bottom=gap_bottom,
            time=c2["time"] if "time" in c2 else c2.name,
        )

    def _detect_bearish_fvg(self, c1, c2, c3) -> FairValueGap | None:
        """
        Detect bearish FVG (gap above current price).

        Pattern: Candle 3's high < Candle 1's low
        """
        gap_top = c1["low"]
        gap_bottom = c3["high"]

        if gap_bottom >= gap_top:
            return None

        gap_size = gap_top - gap_bottom

        if gap_size < (self.min_gap_size_pips * 0.0001):
            return None

        return FairValueGap(
            type=MarketRegime.BEARISH,
            top=gap_top,
            bottom=gap_bottom,
            time=c2["time"] if "time" in c2 else c2.name,
        )

    def _update_fvg_fill_status(self, fvgs: list[FairValueGap], df: pd.DataFrame):
        """Update which FVGs have been filled."""
        for fvg in fvgs:
            fvg_index = (
                df[df["time"] == fvg.time].index[0]
                if "time" in df.columns
                else df.index[df.index == fvg.time][0]
            )

            for i in range(fvg_index + 1, len(df)):
                candle = df.iloc[i]
                fvg.update_fill_status(candle["high"], candle["low"])

                if fvg.filled:
                    break

    def get_unfilled_fvgs(self, fvgs: list[FairValueGap]) -> list[FairValueGap]:
        """Filter for unfilled Fair Value Gaps."""
        return [fvg for fvg in fvgs if not fvg.filled]

    def get_partially_filled_fvgs(self, fvgs: list[FairValueGap]) -> list[FairValueGap]:
        """Filter for partially filled FVGs (touched but not fully filled)."""
        return [fvg for fvg in fvgs if 0 < fvg.fill_percentage < 100]
