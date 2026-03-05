import numpy as np
import pandas as pd
import pytest

from app.strategies.rsi.strategy import RSIStrategy
from app.strategies.smc.ict import SmartMoneyStrategy


@pytest.fixture
def base_rsi_strategy():
    return RSIStrategy(
        symbol="EURUSD",
        timeframe="H1",
        use_volatility_filter=True,
        use_volume_filter=True,
        volatility_ma_period=20,
        volume_ma_period=20,
    )


@pytest.fixture
def base_ict():
    return SmartMoneyStrategy(
        symbol="EURUSD",
        timeframe="H1",
        use_volatility_filter=True,
        use_volume_filter=True,
        volatility_ma_period=20,
        volume_ma_period=20,
    )


@pytest.fixture
def high_volatility_high_volume_data():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=50, freq="h")
    highs = np.random.uniform(1.0510, 1.0520, 50)
    lows = np.random.uniform(1.0500, 1.0510, 50)
    closes = np.random.uniform(1.0505, 1.0515, 50)
    volumes = np.random.randint(100, 200, 50)

    highs[-1] = 1.0600
    lows[-1] = 1.0400
    closes[-1] = 1.0550
    volumes[-1] = 2000

    return pd.DataFrame(
        {
            "time": dates,
            "high": highs,
            "low": lows,
            "close": closes,
            "tickVolume": volumes,
        }
    )


@pytest.fixture
def low_volatility_low_volume_data():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=50, freq="h")
    highs = np.random.uniform(1.0500, 1.0600, 50)
    lows = np.random.uniform(1.0400, 1.0500, 50)
    closes = np.random.uniform(1.0450, 1.0550, 50)
    volumes = np.random.randint(1000, 2000, 50)

    highs[-1] = 1.0505
    lows[-1] = 1.0504
    closes[-1] = 1.05045
    volumes[-1] = 10

    return pd.DataFrame(
        {
            "time": dates,
            "high": highs,
            "low": lows,
            "close": closes,
            "tickVolume": volumes,
        }
    )


def test_rsi_filter_passes_high(base_rsi_strategy, high_volatility_high_volume_data):
    vol_pass = base_rsi_strategy._check_volatility(high_volatility_high_volume_data)
    volume_pass = base_rsi_strategy._check_volume(high_volatility_high_volume_data)

    assert vol_pass
    assert volume_pass


def test_rsi_filter_fails_low(base_rsi_strategy, low_volatility_low_volume_data):
    vol_pass = base_rsi_strategy._check_volatility(low_volatility_low_volume_data)
    volume_pass = base_rsi_strategy._check_volume(low_volatility_low_volume_data)

    assert not vol_pass
    assert not volume_pass


def test_ict_filter_passes_high(base_ict, high_volatility_high_volume_data):
    vol_pass = base_ict._check_volatility(high_volatility_high_volume_data)
    volume_pass = base_ict._check_volume(high_volatility_high_volume_data)

    assert vol_pass
    assert volume_pass


def test_ict_filter_fails_low(base_ict, low_volatility_low_volume_data):
    vol_pass = base_ict._check_volatility(low_volatility_low_volume_data)
    volume_pass = base_ict._check_volume(low_volatility_low_volume_data)

    assert not vol_pass
    assert not volume_pass
