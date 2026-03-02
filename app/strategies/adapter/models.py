"""Adapter Data Models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.enums import SignalAction


@dataclass
class UnifiedSignal:
    """Unified trading signal format."""

    strategy_name: str
    action: SignalAction
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    risk_reward_ratio: float
    reason: str
    timestamp: datetime
    metadata: dict[str, Any]
