import pandas as pd

from app.indicators.atr import calculate_atr, calculate_atr_series, normalize_atr


def test_calculate_atr():
    highs = [15, 16, 17, 18, 19]
    lows = [10, 11, 12, 13, 14]
    closes = [12, 13, 14, 15, 16]

    atr = calculate_atr(highs, lows, closes, period=3)
    assert atr == 5.0


def test_calculate_atr_short_data():
    assert calculate_atr([10, 11], [9, 10], [9.5, 10.5], period=3) == 0.0


def test_calculate_atr_series():
    df = pd.DataFrame(
        {
            "high": [15, 16, 17, 18, 19],
            "low": [10, 11, 12, 13, 14],
            "close": [12, 13, 14, 15, 16],
        }
    )
    series = calculate_atr_series(df, period=3)

    assert len(series) == 5
    assert pd.isna(series.iloc[0])
    assert pd.isna(series.iloc[1])
    assert pd.isna(series.iloc[2])  # indices 0,1,2 < period (3)
    assert series.iloc[3] == 5.0
    assert series.iloc[4] == 5.0


def test_normalize_atr():
    assert normalize_atr(5.0, 100.0) == 5.0
    assert normalize_atr(1.0, 50.0) == 2.0
    assert normalize_atr(5.0, 0.0) == 0.0
