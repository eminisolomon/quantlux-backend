"""All enumerations and constants for the QuantLux trading system."""

from enum import IntEnum, StrEnum


class TradingEnvironment(StrEnum):
    """Trading environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Logging level"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SizingMethod(StrEnum):
    """Position sizing methods."""

    FIXED_RISK = "fixed_risk"
    FIXED_LOT = "fixed_lot"
    KELLY = "kelly"
    PERCENT_EQUITY = "percent_equity"
    ATR_BASED = "atr_based"


class SignalAction(StrEnum):
    """Trading signal actions."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class MarketRegime(StrEnum):
    """Market regime classification."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    SIDEWAYS = "SIDEWAYS"


class AccountType(StrEnum):
    """MetaApi account types."""

    DEMO = "demo"
    REAL = "real"


class Timeframe(IntEnum):
    """Timeframe constants - MetaApi uses string formats."""

    M1 = 1
    M5 = 5
    M15 = 15
    M30 = 30
    H1 = 60
    H4 = 240
    D1 = 1440
    W1 = 10080
    MN1 = 43200


TIMEFRAME_STRINGS = {
    Timeframe.M1: "1m",
    Timeframe.M5: "5m",
    Timeframe.M15: "15m",
    Timeframe.M30: "30m",
    Timeframe.H1: "1h",
    Timeframe.H4: "4h",
    Timeframe.D1: "1d",
    Timeframe.W1: "1w",
    Timeframe.MN1: "1mn",
}


def get_metaapi_timeframe(timeframe: Timeframe) -> str:
    """Convert Timeframe enum to MetaApi string format."""
    return TIMEFRAME_STRINGS.get(timeframe, "1h")


def get_mt5_timeframe(timeframe_str: str) -> int:
    """Map string timeframe to MT5 constant."""
    mapping = {
        "M1": Timeframe.M1,
        "M5": Timeframe.M5,
        "M15": Timeframe.M15,
        "M30": Timeframe.M30,
        "H1": Timeframe.H1,
        "H4": Timeframe.H4,
        "D1": Timeframe.D1,
        "W1": Timeframe.W1,
        "MN1": Timeframe.MN1,
    }
    return mapping.get(timeframe_str.upper(), Timeframe.H1)


class VolatilityRegime(StrEnum):
    """Volatility regimes."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RSISmoothing(StrEnum):
    """RSI smoothing methods."""

    WILDER = "WILDER"
    EMA = "EMA"
    SMA = "SMA"


class RSIPattern(StrEnum):
    """RSI-specific patterns."""

    FAILURE_SWING = "FAILURE_SWING"
    DIVERGENCE = "DIVERGENCE"
    OVERBOUGHT = "OVERBOUGHT"
    OVERSOLD = "OVERSOLD"


class StructureType(StrEnum):
    """Market structure break types."""

    BOS = "BOS"
    CHOCH = "CHOCH"


class SwingType(StrEnum):
    """Swing high/low types."""

    HIGH = "HIGH"
    LOW = "LOW"


class Impact(StrEnum):
    """Impact levels for economic events."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    NONE = "None"
