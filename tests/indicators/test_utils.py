import pandas as pd

from app.indicators.utils import (
    crossover,
    crossunder,
    is_above,
    is_below,
    is_falling,
    is_rising,
)


def test_crossover():
    series_a = pd.Series([10, 15])
    series_b = pd.Series([12, 12])
    assert crossover(series_a, series_b)

    assert not crossover(pd.Series([15, 10]), series_b)
    assert not crossover(pd.Series([10, 10]), 12)
    assert crossover(pd.Series([10, 15]), 12)


def test_crossunder():
    series_a = pd.Series([15, 10])
    series_b = pd.Series([12, 12])
    assert crossunder(series_a, series_b)

    assert not crossunder(pd.Series([10, 15]), series_b)
    assert not crossunder(pd.Series([15, 15]), 12)
    assert crossunder(pd.Series([15, 10]), 12)


def test_is_rising():
    assert is_rising(pd.Series([10, 15, 20]), lookback=2)
    assert not is_rising(pd.Series([20, 15, 10]), lookback=2)


def test_is_falling():
    assert is_falling(pd.Series([20, 15, 10]), lookback=2)
    assert not is_falling(pd.Series([10, 15, 20]), lookback=2)


def test_is_above_below():
    series = pd.Series([10, 15, 20])
    assert is_above(series, 15)
    assert is_below(series, 25)
    assert not is_above(series, 25)
    assert not is_below(series, 15)
