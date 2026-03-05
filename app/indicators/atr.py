"""ATR (Average True Range) indicator for volatility measurement."""

import numpy as np
import pandas as pd


def calculate_atr(
    highs: list[float], lows: list[float], closes: list[float], period: int = 14
) -> float:
    """Calculate Average True Range (ATR)."""
    if len(highs) < period + 1:
        return 0.0

    true_ranges = []

    for i in range(1, len(closes)):
        h_l = highs[i] - lows[i]
        h_pc = abs(highs[i] - closes[i - 1])
        l_pc = abs(lows[i] - closes[i - 1])

        tr = max(h_l, h_pc, l_pc)
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return 0.0

    atr = sum(true_ranges[-period:]) / period
    return atr


def calculate_atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR series for an entire DataFrame."""
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values

    atr_values = []

    for i in range(len(df)):
        if i < period:
            atr_values.append(np.nan)
        else:
            atr = calculate_atr(
                highs[: i + 1].tolist(),
                lows[: i + 1].tolist(),
                closes[: i + 1].tolist(),
                period,
            )
            atr_values.append(atr)

    return pd.Series(atr_values, index=df.index, name=f"ATR_{period}")


def normalize_atr(atr: float, current_price: float) -> float:
    """Normalize ATR as percentage of price."""
    if current_price == 0:
        return 0.0
    return (atr / current_price) * 100
