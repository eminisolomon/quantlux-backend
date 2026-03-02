import numpy as np
import pandas as pd
import pytest

from app.core.enums import SignalAction
from app.strategies.momentum.strategy import MomentumStrategy


@pytest.fixture
def momentum_strategy():
    return MomentumStrategy(
        symbol="EURUSD",
        timeframe="H1",
        channel_period=20,
        atr_period=14,
        min_risk_reward=2.0,
        use_volatility_filter=False,
        use_volume_filter=False,
    )


@pytest.fixture
def sample_data_bullish():
    # 30 periods of data
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=30, freq="h")

    # Generate prices inside a channel
    highs = np.random.uniform(1.0500, 1.0600, 30)
    lows = np.random.uniform(1.0400, 1.0500, 30)
    closes = np.random.uniform(1.0450, 1.0550, 30)
    volumes = np.random.randint(100, 1000, 30)

    # Create the breakout at the very end
    # previous high would be max ~1.0600
    closes[-1] = 1.0650  # Bullish breakout
    highs[-1] = 1.0660

    df = pd.DataFrame(
        {
            "time": dates,
            "high": highs,
            "low": lows,
            "close": closes,
            "tickVolume": volumes,
        }
    )
    return df


@pytest.fixture
def sample_data_bearish():
    # 30 periods of data
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=30, freq="h")

    # Generate prices inside a channel
    highs = np.random.uniform(1.0500, 1.0600, 30)
    lows = np.random.uniform(1.0400, 1.0500, 30)
    closes = np.random.uniform(1.0450, 1.0550, 30)
    volumes = np.random.randint(100, 1000, 30)

    # Create the breakout at the very end
    # previous low would be min ~1.0400
    closes[-1] = 1.0350  # Bearish breakout
    lows[-1] = 1.0340

    df = pd.DataFrame(
        {
            "time": dates,
            "high": highs,
            "low": lows,
            "close": closes,
            "tickVolume": volumes,
        }
    )
    return df


def test_momentum_strategy_bullish_breakout(momentum_strategy, sample_data_bullish):
    signal = momentum_strategy.analyze(sample_data_bullish)
    assert signal is not None
    assert signal.action == SignalAction.BUY
    assert signal.entry_price == 1.0650
    assert signal.reason == "Bullish Donchian Breakout"
    assert signal.risk_reward_ratio >= 2.0


def test_momentum_strategy_bearish_breakout(momentum_strategy, sample_data_bearish):
    signal = momentum_strategy.analyze(sample_data_bearish)
    assert signal is not None
    assert signal.action == SignalAction.SELL
    assert signal.entry_price == 1.0350
    assert signal.reason == "Bearish Donchian Breakout"
    assert signal.risk_reward_ratio >= 2.0


def test_momentum_strategy_no_breakout(momentum_strategy, sample_data_bullish):
    # remove breakout
    sample_data_bullish.loc[sample_data_bullish.index[-1], "close"] = 1.0550
    signal = momentum_strategy.analyze(sample_data_bullish)
    assert signal is None
