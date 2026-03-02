"""Shared technical indicator utilities."""

import pandas as pd


def crossover(series_a: pd.Series, series_b: pd.Series | float) -> bool:
    """Check if series_a crossed above series_b in the last candle."""
    if len(series_a) < 2:
        return False

    if isinstance(series_b, (int, float)):
        return series_a.iloc[-2] <= series_b and series_a.iloc[-1] > series_b

    if len(series_b) < 2:
        return False

    return (
        series_a.iloc[-2] <= series_b.iloc[-2] and series_a.iloc[-1] > series_b.iloc[-1]
    )


def crossunder(series_a: pd.Series, series_b: pd.Series | float) -> bool:
    """Check if series_a crossed below series_b in the last candle."""
    if len(series_a) < 2:
        return False

    if isinstance(series_b, (int, float)):
        return series_a.iloc[-2] >= series_b and series_a.iloc[-1] < series_b

    if len(series_b) < 2:
        return False

    return (
        series_a.iloc[-2] >= series_b.iloc[-2] and series_a.iloc[-1] < series_b.iloc[-1]
    )


def is_rising(series: pd.Series, lookback: int = 2) -> bool:
    """Check if series is rising over the lookback period."""
    if len(series) < lookback:
        return False
    window = series.iloc[-lookback:]
    return bool(window.is_monotonic_increasing) and window.iloc[-1] > window.iloc[0]


def is_falling(series: pd.Series, lookback: int = 2) -> bool:
    """Check if series is falling over the lookback period."""
    if len(series) < lookback:
        return False
    window = series.iloc[-lookback:]
    return bool(window.is_monotonic_decreasing) and window.iloc[-1] < window.iloc[0]


def is_above(series: pd.Series, value: pd.Series | float) -> bool:
    """Check if current value is above target value."""
    if series.empty:
        return False

    current = series.iloc[-1]
    target = value.iloc[-1] if isinstance(value, pd.Series) else value

    return current > target


def is_below(series: pd.Series, value: pd.Series | float) -> bool:
    """Check if current value is below target value."""
    if series.empty:
        return False

    current = series.iloc[-1]
    target = value.iloc[-1] if isinstance(value, pd.Series) else value

    return current < target
