"""RSI Configuration."""

from pydantic import BaseModel

from app.core.enums import RSISmoothing


class RSIConfig(BaseModel):
    """Configuration for RSI calculation."""

    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0
    smoothing: RSISmoothing = RSISmoothing.WILDER
    adaptive: bool = False
