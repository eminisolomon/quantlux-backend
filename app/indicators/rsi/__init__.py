"""RSI Indicator Package."""

from app.indicators.rsi.calculator import ModernRSI
from app.indicators.rsi.config import RSIConfig
from app.indicators.rsi.divergence import RSIDivergence
from app.indicators.rsi.mtf import MultiTimeframeRSI


def calculate_rsi(prices, period=14, smoothing="wilder"):
    """Quick RSI calculation function."""
    config = RSIConfig(period=period, smoothing=smoothing)
    calculator = ModernRSI(config)
    return calculator.calculate(prices)


__all__ = [
    "RSIConfig",
    "ModernRSI",
    "RSIDivergence",
    "MultiTimeframeRSI",
    "calculate_rsi",
]
