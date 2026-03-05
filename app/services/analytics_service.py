"""Performance metrics tracking: Sharpe, Sortino, drawdown, win rate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.schemas import (
    AverageTradeStats,
    DrawdownInfo,
    PerformanceReport,
    PerformanceStats,
    Trade,
)
from app.services.simulation import MonteCarloSimulator, SimulationResults
from app.services.visualizer import PerformanceVisualizer
from app.core import messages as msg
from app.core.settings import settings
from app.utils.logger import logger


class AnalyticsService:
    def __init__(self, initial_balance: float = 10000.0, account_id: str = "default"):
        self.initial_balance = initial_balance
        self.account_id = account_id
        self.trades: list[Trade] = []
        self.equity_curve: list[float] = [initial_balance]
        self.current_equity = initial_balance
        self.redis_key = f"quantlux:{self.account_id}:analytics:trades"

        logger.info(msg.TRACKER_INIT)

    async def initialize(self) -> None:
        """Load historical trades from Redis asynchronously."""
        from app.core.redis_client import redis_client

        redis = redis_client.redis

        trades_data = await redis.lrange(self.redis_key, 0, -1)
        if not trades_data:
            logger.info(msg.TRACKER_NO_HISTORY)
            return

        try:
            self.trades = [Trade.model_validate(json.loads(t)) for t in trades_data]
            self._rebuild_equity_curve()
            logger.info(msg.TRACKER_LOADED.format(count=len(self.trades)))
        except Exception as e:
            logger.error(msg.TRACKER_LOAD_ERROR.format(error=e))

    def _rebuild_equity_curve(self) -> None:
        """Replay trades to reconstruct the equity curve from the initial balance."""
        self.equity_curve = [self.initial_balance]
        self.current_equity = self.initial_balance
        for t in self.trades:
            self.current_equity += t.profit
            self.equity_curve.append(self.current_equity)

    async def load_history(self, trades: list[Trade]) -> None:
        """Populate tracker with a list of closed trades and save to Redis."""
        from app.core.redis_client import redis_client

        redis = redis_client.redis

        self.trades = trades
        self._rebuild_equity_curve()

        pipe = redis.pipeline()
        pipe.delete(self.redis_key)
        if trades:
            pipe.rpush(
                self.redis_key, *[t.model_dump_json(by_alias=True) for t in trades]
            )
        await pipe.execute()

        logger.info(msg.TRACKER_LOADED.format(count=len(self.trades)))

    async def add_trade(self, trade: Trade):
        """Record a new trade and update metrics in Redis."""
        from app.core.redis_client import redis_client

        redis = redis_client.redis

        self.trades.append(trade)
        new_equity = self.equity_curve[-1] + trade.profit
        self.equity_curve.append(new_equity)
        self.current_equity = new_equity

        logger.info(
            msg.TRACKER_TRADE_RECORDED.format(symbol=trade.symbol, profit=trade.profit)
        )
        await redis.rpush(self.redis_key, trade.model_dump_json(by_alias=True))

    def get_stats(self, days: int | None = None) -> PerformanceStats:
        """Get performance statistics for last N days."""
        trades = self.trades

        if days:
            if not trades:
                return PerformanceStats()
            cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
            filtered_trades = [t for t in trades if t.close_time.timestamp() >= cutoff]
            trades = filtered_trades

        stats = PerformanceStats.from_trades(trades, self.initial_balance)

        if days is None:
            dd_info = self.calculate_max_drawdown()
            stats.max_drawdown = dd_info.max_dd_value
            stats.current_drawdown = self.get_current_drawdown()
        else:
            stats.max_drawdown = 0.0

        return stats

    def calculate_returns(self) -> np.ndarray:
        if len(self.equity_curve) < 2:
            return np.array([])

        equity = np.array(self.equity_curve)
        returns = np.diff(equity) / equity[:-1]
        return returns

    def calculate_sharpe_ratio(self, risk_free_rate: float = None) -> float:
        """Calculate Sharpe Ratio (>1.0 good, >2.0 excellent)."""
        if risk_free_rate is None:
            risk_free_rate = settings.RISK_FREE_RATE
        returns = self.calculate_returns()

        if len(returns) == 0:
            return 0.0

        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        sharpe = (avg_return - risk_free_rate / 252) / std_return * np.sqrt(252)
        return float(sharpe)

    def calculate_sortino_ratio(self, risk_free_rate: float = None) -> float:
        """Calculate Sortino Ratio (downside risk only)."""
        if risk_free_rate is None:
            risk_free_rate = settings.RISK_FREE_RATE
        returns = self.calculate_returns()

        if len(returns) == 0:
            return 0.0

        avg_return = np.mean(returns)
        negative_returns = returns[returns < 0]

        if len(negative_returns) == 0:
            return float("inf")

        downside_std = np.std(negative_returns)

        if downside_std == 0:
            return 0.0

        sortino = (avg_return - risk_free_rate / 252) / downside_std * np.sqrt(252)
        return float(sortino)

    def calculate_recovery_factor(
        self, net_profit: float, max_drawdown_value: float
    ) -> float:
        """Calculate Recovery Factor (Net Profit / Max Drawdown)."""
        if max_drawdown_value == 0:
            return float("inf") if net_profit > 0 else 0.0
        return net_profit / max_drawdown_value

    def calculate_max_drawdown(self) -> DrawdownInfo:
        """Calculate maximum drawdown (peak-to-trough decline)."""
        if len(self.equity_curve) < 2:
            return DrawdownInfo(
                max_dd_pct=0.0,
                max_dd_value=0.0,
                peak=self.initial_balance,
                trough=self.initial_balance,
            )

        equity = np.array(self.equity_curve)
        peak = equity[0]
        max_dd = 0.0
        max_dd_value = 0.0
        peak_value = peak
        trough_value = peak

        for current in equity:
            if current > peak:
                peak = current

            dd = (peak - current) / peak * 100
            if dd > max_dd:
                max_dd = dd
                max_dd_value = peak - current
                peak_value = peak
                trough_value = current

        return DrawdownInfo(
            max_dd_pct=max_dd,
            max_dd_value=max_dd_value,
            peak=peak_value,
            trough=trough_value,
        )

    def calculate_win_rate(self) -> float:
        if len(self.trades) == 0:
            return 0.0

        winning_trades = sum(1 for t in self.trades if t.profit > 0)
        return (winning_trades / len(self.trades)) * 100

    def calculate_profit_factor(self) -> float:
        """Calculate profit factor (>1.5 good, >2.0 excellent)."""
        if len(self.trades) == 0:
            return 0.0

        total_wins = sum(t.profit for t in self.trades if t.profit > 0)
        total_losses = abs(sum(t.profit for t in self.trades if t.profit < 0))

        if total_losses == 0:
            return float("inf") if total_wins > 0 else 0.0

        return total_wins / total_losses

    def calculate_average_trade(self) -> AverageTradeStats:
        if len(self.trades) == 0:
            return AverageTradeStats()

        wins = [t.profit for t in self.trades if t.profit > 0]
        losses = [t.profit for t in self.trades if t.profit < 0]

        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        avg_trade = np.mean([t.profit for t in self.trades])

        return AverageTradeStats(
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            avg_trade=float(avg_trade),
        )

    def get_current_drawdown(self) -> float:
        if len(self.equity_curve) < 2:
            return 0.0

        peak = max(self.equity_curve)
        current_dd = (peak - self.current_equity) / peak * 100
        return current_dd

    def generate_performance_report(self) -> PerformanceReport:
        if len(self.trades) == 0:
            return PerformanceReport(
                total_trades=0,
                net_profit=0.0,
                roi=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                recovery_factor=0.0,
                max_drawdown_pct=0.0,
                max_drawdown_value=0.0,
                current_drawdown=0.0,
                current_equity=self.initial_balance,
                avg_win=0.0,
                avg_loss=0.0,
                avg_trade=0.0,
            )

        dd_info = self.calculate_max_drawdown()
        avg_trades = self.calculate_average_trade()

        net_profit = self.current_equity - self.initial_balance
        roi = (net_profit / self.initial_balance) * 100

        return PerformanceReport(
            total_trades=len(self.trades),
            net_profit=net_profit,
            roi=roi,
            win_rate=self.calculate_win_rate(),
            profit_factor=self.calculate_profit_factor(),
            sharpe_ratio=self.calculate_sharpe_ratio(),
            sortino_ratio=self.calculate_sortino_ratio(),
            recovery_factor=self.calculate_recovery_factor(
                net_profit, dd_info.max_dd_value
            ),
            max_drawdown_pct=dd_info.max_dd_pct,
            max_drawdown_value=dd_info.max_dd_value,
            current_drawdown=self.get_current_drawdown(),
            current_equity=self.current_equity,
            avg_win=avg_trades.avg_win,
            avg_loss=avg_trades.avg_loss,
            avg_trade=avg_trades.avg_trade,
        )

    def run_monte_carlo(self, iterations: int = 1000) -> SimulationResults:
        """Run stress-testing simulation."""
        simulator = MonteCarloSimulator(
            iterations=iterations, initial_balance=self.initial_balance
        )
        return simulator.run(self.trades)

    def generate_charts(self) -> dict[str, any]:
        """Generate performance charts for reporting."""
        visualizer = PerformanceVisualizer()

        equity_chart = visualizer.plot_equity_curve(self.equity_curve)
        dd_chart = visualizer.plot_drawdown(self.equity_curve)

        return {"equity": equity_chart, "drawdown": dd_chart}
