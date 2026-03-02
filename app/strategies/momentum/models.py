from dataclasses import dataclass

from app.core.enums import SignalAction


@dataclass
class MomentumSignal:
    """Trading signal from Momentum strategy."""

    action: SignalAction
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reason: str
    risk_reward_ratio: float
