from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Trade(BaseModel):
    """Pydantic model for a closed trade."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str
    trade_type: str = Field(alias="type")
    open_price: float
    close_price: float
    lot_size: float
    open_time: datetime
    close_time: datetime
    profit: float


class DrawdownInfo(BaseModel):
    """Drawdown statistics."""

    max_dd_pct: float = 0.0
    max_dd_value: float = 0.0
    peak: float = 0.0
    trough: float = 0.0


class AverageTradeStats(BaseModel):
    """Averaged trade metrics."""

    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade: float = 0.0


class PerformanceStats(BaseModel):
    """Performance statistics snapshot."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0

    @classmethod
    def from_trades(
        cls, trades: list[Trade], initial_balance: float = 10000.0
    ) -> "PerformanceStats":
        if not trades:
            return cls()

        winning = [t for t in trades if t.profit > 0]
        losing = [t for t in trades if t.profit < 0]

        total_profit = sum(t.profit for t in winning)
        total_loss = abs(sum(t.profit for t in losing))

        total_trades = len(trades)
        winning_count = len(winning)
        losing_count = len(losing)

        return cls(
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            total_profit=total_profit,
            total_loss=total_loss,
            win_rate=(winning_count / total_trades * 100) if total_trades > 0 else 0.0,
            profit_factor=(
                (total_profit / total_loss) if total_loss > 0 else float("inf")
            ),
            avg_win=(total_profit / winning_count) if winning_count > 0 else 0.0,
            avg_loss=(total_loss / losing_count) if losing_count > 0 else 0.0,
            largest_win=max((t.profit for t in winning), default=0.0),
            largest_loss=abs(min((t.profit for t in losing), default=0.0)),
        )


class PerformanceReport(BaseModel):
    """Full performance report including metrics and metadata."""

    total_trades: int
    net_profit: float
    roi: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    recovery_factor: float
    max_drawdown_pct: float
    max_drawdown_value: float
    current_drawdown: float
    current_equity: float
    avg_win: float
    avg_loss: float
    avg_trade: float
