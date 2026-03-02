from dataclasses import dataclass

from app.core.enums import MarketRegime, RSIPattern, SignalAction


@dataclass
class RSISignal:
    """Trading signal from Advanced RSI strategy."""

    action: SignalAction
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reason: str
    rsi_value: float
    regime: MarketRegime
    pattern: RSIPattern

    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk-reward ratio."""
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        return reward / risk if risk > 0 else 0
