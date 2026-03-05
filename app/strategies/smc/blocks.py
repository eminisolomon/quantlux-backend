"""
Smart Money Concepts - Order Blocks Detection

Order blocks represent institutional footprints where large orders were placed,
causing significant price movements. They are key reversal and continuation zones.
"""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from app.core.enums import MarketRegime
from app.utils.logger import logger


@dataclass
class OrderBlock:
    """Represents an institutional order block zone."""

    type: MarketRegime
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    time: datetime
    strength: float
    mitigated: bool = False
    touches: int = 0

    @property
    def zone_top(self) -> float:
        """Top of the order block zone."""
        return self.high_price

    @property
    def zone_bottom(self) -> float:
        """Bottom of the order block zone."""
        return self.low_price

    @property
    def zone_mid(self) -> float:
        """Middle of the order block zone."""
        return (self.zone_top + self.zone_bottom) / 2

    def is_price_in_zone(self, price: float) -> bool:
        """Check if price is within the order block zone."""
        return self.zone_bottom <= price <= self.zone_top


class OrderBlockDetector:
    """Detects institutional order blocks on price charts."""

    def __init__(
        self,
        min_impulse_candles: int = 3,
        impulse_strength_threshold: float = 0.5,
        max_blocks: int = 10,
    ):
        """Initialize order block detector."""
        self.min_impulse_candles = min_impulse_candles
        self.impulse_strength_threshold = impulse_strength_threshold
        self.max_blocks = max_blocks

    def detect_blocks(self, df: pd.DataFrame) -> list[OrderBlock]:
        """Detect order blocks in OHLC data."""
        if len(df) < self.min_impulse_candles + 5:
            logger.warning("Not enough data for order block detection")
            return []

        blocks = []

        bullish_obs = self._detect_bullish_blocks(df)
        blocks.extend(bullish_obs)

        bearish_obs = self._detect_bearish_blocks(df)
        blocks.extend(bearish_obs)

        blocks.sort(key=lambda x: x.strength, reverse=True)
        blocks = blocks[: self.max_blocks]

        self._update_mitigation_status(blocks, df)

        logger.info(f"Detected {len(blocks)} order blocks")
        return blocks

    def _detect_bullish_blocks(self, df: pd.DataFrame) -> list[OrderBlock]:
        """Detect bullish order blocks (last down candle before up impulse)."""
        blocks = []

        for i in range(len(df) - self.min_impulse_candles - 1):
            if df.iloc[i]["close"] >= df.iloc[i]["open"]:
                continue

            impulse_start = i + 1
            impulse_end = min(i + 1 + self.min_impulse_candles, len(df))

            if self._is_bullish_impulse(df.iloc[impulse_start:impulse_end]):
                candle = df.iloc[i]
                strength = self._calculate_ob_strength(df, i, MarketRegime.BULLISH)

                ob = OrderBlock(
                    type=MarketRegime.BULLISH,
                    open_price=candle["open"],
                    close_price=candle["close"],
                    high_price=candle["high"],
                    low_price=candle["low"],
                    time=candle["time"] if "time" in candle else candle.name,
                    strength=strength,
                )
                blocks.append(ob)

        return blocks

    def _detect_bearish_blocks(self, df: pd.DataFrame) -> list[OrderBlock]:
        """Detect bearish order blocks (last up candle before down impulse)."""
        blocks = []

        for i in range(len(df) - self.min_impulse_candles - 1):
            if df.iloc[i]["close"] <= df.iloc[i]["open"]:
                continue

            impulse_start = i + 1
            impulse_end = min(i + 1 + self.min_impulse_candles, len(df))

            if self._is_bearish_impulse(df.iloc[impulse_start:impulse_end]):
                candle = df.iloc[i]
                strength = self._calculate_ob_strength(df, i, MarketRegime.BEARISH)

                ob = OrderBlock(
                    type=MarketRegime.BEARISH,
                    open_price=candle["open"],
                    close_price=candle["close"],
                    high_price=candle["high"],
                    low_price=candle["low"],
                    time=candle["time"] if "time" in candle else candle.name,
                    strength=strength,
                )
                blocks.append(ob)

        return blocks

    def _is_bullish_impulse(self, candles: pd.DataFrame) -> bool:
        """Check if candles form a bullish impulse move."""
        if len(candles) < self.min_impulse_candles:
            return False

        bullish_count = (candles["close"] > candles["open"]).sum()
        if bullish_count < self.min_impulse_candles * 0.8:
            return False

        total_move = (
            (candles.iloc[-1]["close"] - candles.iloc[0]["open"])
            / candles.iloc[0]["open"]
            * 100
        )

        return total_move >= self.impulse_strength_threshold

    def _is_bearish_impulse(self, candles: pd.DataFrame) -> bool:
        """Check if candles form a bearish impulse move."""
        if len(candles) < self.min_impulse_candles:
            return False

        bearish_count = (candles["close"] < candles["open"]).sum()
        if bearish_count < self.min_impulse_candles * 0.8:
            return False

        total_move = (
            (candles.iloc[0]["open"] - candles.iloc[-1]["close"])
            / candles.iloc[0]["open"]
            * 100
        )

        return total_move >= self.impulse_strength_threshold

    def _calculate_ob_strength(
        self, df: pd.DataFrame, index: int, ob_type: MarketRegime
    ) -> float:
        """
        Calculate order block strength (0-100).

        Factors:
        - Candle size (larger = stronger)
        - Volume (higher = stronger)
        - Distance from current price (closer = stronger)
        - Impulse strength following the OB
        """
        candle = df.iloc[index]
        current_price = df.iloc[-1]["close"]

        candle_range = candle["high"] - candle["low"]
        avg_range = (df["high"] - df["low"]).rolling(20).mean().iloc[index]
        size_score = min(30, (candle_range / avg_range) * 15) if avg_range > 0 else 15

        volume_score = 15
        if "volume" in df.columns and df["volume"].iloc[index] > 0:
            avg_volume = df["volume"].rolling(20).mean().iloc[index]
            volume_score = (
                min(30, (df["volume"].iloc[index] / avg_volume) * 15)
                if avg_volume > 0
                else 15
            )

        bars_ago = len(df) - index - 1
        recency_score = max(0, 20 - (bars_ago / 10))

        ob_mid = (candle["high"] + candle["low"]) / 2
        distance_pct = abs(current_price - ob_mid) / current_price * 100
        distance_score = max(0, 20 - distance_pct * 2)

        total_score = size_score + volume_score + recency_score + distance_score
        return min(100, total_score)

    def _update_mitigation_status(self, blocks: list[OrderBlock], df: pd.DataFrame):
        """Update which order blocks have been mitigated (price returned)."""
        current_price = df.iloc[-1]["close"]

        for ob in blocks:
            if ob.is_price_in_zone(current_price):
                ob.touches += 1
                ob.mitigated = True

    def get_active_blocks(self, blocks: list[OrderBlock]) -> list[OrderBlock]:
        """Filter for only unmitigated (active) order blocks."""
        return [ob for ob in blocks if not ob.mitigated]

    def get_nearest_order_block(
        self,
        blocks: list[OrderBlock],
        current_price: float,
        ob_type: MarketRegime | None = None,
    ) -> OrderBlock | None:
        """Get the nearest order block to current price."""
        filtered_obs = blocks
        if ob_type:
            filtered_obs = [ob for ob in blocks if ob.type == ob_type]

        if not filtered_obs:
            return None

        nearest = min(filtered_obs, key=lambda ob: abs(current_price - ob.zone_mid))

        return nearest
