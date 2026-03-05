import pandas as pd
import numpy as np


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Average Directional Index (ADX), +DI, and -DI.
    Returns DataFrame with columns: ['ADX', '+DI', '-DI']
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    pos_dm_smoothed = (
        pd.Series(pos_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean()
    )
    neg_dm_smoothed = (
        pd.Series(neg_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean()
    )

    pos_di = 100 * (pos_dm_smoothed / atr)
    neg_di = 100 * (neg_dm_smoothed / atr)

    dx = 100 * (abs(pos_di - neg_di) / (pos_di + neg_di))

    adx = dx.ewm(alpha=1 / period, adjust=False).mean()

    result = pd.DataFrame({"ADX": adx, "+DI": pos_di, "-DI": neg_di})

    return result
