from dataclasses import dataclass

from app.core.enums import SignalAction
from app.strategies.smc.blocks import OrderBlock
from app.strategies.smc.fvg import FairValueGap
from app.strategies.smc.structure import StructureBreak


@dataclass
class ICTSignal:
    """Trading signal from ICT strategy."""

    action: SignalAction
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reason: str
    order_block: OrderBlock | None = None
    fvg: FairValueGap | None = None
    structure_break: StructureBreak | None = None

    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk-reward ratio."""
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        return reward / risk if risk > 0 else 0
