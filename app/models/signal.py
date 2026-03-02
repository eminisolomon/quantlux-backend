from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.enums import SignalAction


class TradeSignal(BaseModel):
    """Type-safe trading signal model."""

    action: SignalAction
    symbol: str
    price: float = Field(..., description="Current market price at signal time")
    stop_loss: float | None = None
    take_profit: float | None = None
    tp_levels: list[float] | None = None
    confidence: float = 0.0
    reason: str = ""
    comment: str = "QuantLux-FX"
    magic: int = 123456  # Default magic number
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("action", mode="before")
    @classmethod
    def parse_action(cls, v: Any) -> SignalAction:
        if isinstance(v, str):
            return SignalAction(v.upper())
        return v
