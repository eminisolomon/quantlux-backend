import io
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


class PerformanceVisualizer:
    """Generates professional trading performance charts."""

    def __init__(self, style: str = "dark_background"):
        plt.style.use(style)
        self.primary_color = "#00ffcc"
        self.secondary_color = "#ff3366"
        self.grid_color = "#333333"

    def plot_equity_curve(
        self, equity_curve: list[float], times: list[datetime] | None = None
    ) -> io.BytesIO:
        """Plot equity curve over time."""
        fig, ax = plt.subplots(figsize=(10, 6))

        if times and len(times) == len(equity_curve):
            ax.plot(
                times,
                equity_curve,
                color=self.primary_color,
                linewidth=2,
                label="Equity",
            )
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
            plt.xticks(rotation=45)
        else:
            ax.plot(equity_curve, color=self.primary_color, linewidth=2, label="Equity")
            ax.set_xlabel("Trade Number")

        ax.set_title("Equity Growth", fontsize=14, fontweight="bold", pad=20)
        ax.set_ylabel("Balance ($)")
        ax.grid(True, color=self.grid_color, linestyle="--", alpha=0.5)
        ax.fill_between(
            range(len(equity_curve)) if not times else times,
            equity_curve,
            min(equity_curve),
            color=self.primary_color,
            alpha=0.1,
        )

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        plt.close(fig)
        return buf

    def plot_drawdown(self, equity_curve: list[float]) -> io.BytesIO:
        """Plot drawdown 'underwater' chart."""
        fig, ax = plt.subplots(figsize=(10, 4))

        import numpy as np

        equity = np.array(equity_curve)
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak * 100

        ax.fill_between(
            range(len(drawdown)), drawdown, 0, color=self.secondary_color, alpha=0.3
        )
        ax.plot(drawdown, color=self.secondary_color, linewidth=1.5)

        ax.set_title("Drawdown % (Underwater Chart)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Drawdown %")
        ax.set_ylim(None, 0.5)
        ax.grid(True, color=self.grid_color, linestyle="--", alpha=0.5)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        plt.close(fig)
        return buf
