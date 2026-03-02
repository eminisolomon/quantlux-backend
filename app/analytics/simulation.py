import numpy as np
from pydantic import BaseModel

from app.schemas.analytics import Trade


class SimulationResults(BaseModel):
    """Results of a Monte Carlo simulation run."""

    prob_max_dd_gt_10: float
    median_final_balance: float
    top_5_percentile: float
    bottom_5_percentile: float
    risk_of_ruin: float


class MonteCarloSimulator:
    """Stress-tests a strategy's returns using probabilistic shuffling."""

    def __init__(self, iterations: int = 1000, initial_balance: float = 10000.0):
        self.iterations = iterations
        self.initial_balance = initial_balance

    def run(self, trades: list[Trade]) -> SimulationResults:
        """Run simulations based on historical trade profits."""
        if not trades:
            return SimulationResults(
                prob_max_dd_gt_10=0.0,
                median_final_balance=self.initial_balance,
                top_5_percentile=self.initial_balance,
                bottom_5_percentile=self.initial_balance,
                risk_of_ruin=0.0,
            )

        profits = np.array([t.profit for t in trades])
        final_balances = []
        max_drawdowns = []
        ruined_count = 0

        for _ in range(self.iterations):
            # Shuffle returns to simulate different sequences
            sim_profits = np.random.choice(profits, size=len(profits), replace=True)
            equity_curve = self.initial_balance + np.cumsum(sim_profits)

            # Final balance
            final_balances.append(equity_curve[-1])

            # Ruin check (e.g., balance < 20% of initial)
            if np.any(equity_curve < (self.initial_balance * 0.2)):
                ruined_count += 1

            # Max DD calculation
            peak = np.maximum.accumulate(equity_curve)
            dd = (peak - equity_curve) / peak * 100
            max_drawdowns.append(np.max(dd))

        max_drawdowns = np.array(max_drawdowns)
        final_balances = np.sort(final_balances)

        return SimulationResults(
            prob_max_dd_gt_10=float(np.mean(max_drawdowns > 10.0)),
            median_final_balance=float(np.median(final_balances)),
            top_5_percentile=float(np.percentile(final_balances, 95)),
            bottom_5_percentile=float(np.percentile(final_balances, 5)),
            risk_of_ruin=float(ruined_count / self.iterations),
        )
