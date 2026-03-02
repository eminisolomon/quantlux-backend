"""Parameter Optimizer and Walk-Forward Analysis."""

from datetime import timedelta
import backtrader as bt
import pandas as pd

from app.utils.logger import logger
from backtesting.runner import BacktestEngine
from backtesting.strategy import QuantLuxStrategy


class ParameterOptimizer:
    """Optimizer for strategy parameters using Grid Search and WFA."""

    def __init__(self, initial_cash: float = 10000.0):
        self.initial_cash = initial_cash

    def run_grid_search(
        self,
        data: pd.DataFrame,
        strategy_class: type[bt.Strategy],
        param_grid: dict,
        commission: float = 0.0002,
        slippage_perc: float = 0.001,
        optimize_metric: str = "net_profit",
    ) -> dict:
        """Run grid search on historical data to find best parameters."""
        logger.info("Starting Grid Search Optimization")

        cerebro = bt.Cerebro(optreturn=False, maxcpus=1)

        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        # Add strategy with param grid
        cerebro.optstrategy(strategy_class, **param_grid)

        bt_data = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(bt_data)

        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=commission)
        cerebro.broker.set_slippage_perc(slippage_perc)

        results = cerebro.run()

        best_params = None
        best_metric_value = -float("inf")
        best_result_summary = None

        logger.info(
            f"Optimization completed. Evaluating {len(results)} parameter combinations."
        )

        for run in results:
            strat = run[0]
            params = strat.params._getkwargs()

            # Parse analyzer results
            sharpe_analysis = strat.analyzers.sharpe.get_analysis()
            sharpe = sharpe_analysis.get("sharperatio", 0) if sharpe_analysis else 0
            if sharpe is None:
                sharpe = 0

            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.trades.get_analysis()

            # Metrics
            final_value = strat.broker.getvalue()
            net_profit = final_value - self.initial_cash
            roi = (net_profit / self.initial_cash) * 100

            total_trades = trades.get("total", {}).get("total", 0)
            won_trades = trades.get("won", {}).get("total", 0)
            lost_trades = trades.get("lost", {}).get("total", 0)
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

            gross_profit = trades.get("won", {}).get("pnl", {}).get("total", 0)
            gross_loss = abs(trades.get("lost", {}).get("pnl", {}).get("total", 0))
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

            max_drawdown_pct = drawdown.get("max", {}).get("drawdown", 0)

            result_summary = {
                "params": params,
                "net_profit": net_profit,
                "roi": roi,
                "sharpe_ratio": sharpe,
                "max_drawdown_pct": max_drawdown_pct,
                "total_trades": total_trades,
                "won_trades": won_trades,
                "lost_trades": lost_trades,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
            }

            # Select the metric to optimize
            metric_value = result_summary.get(optimize_metric, -float("inf"))

            if metric_value > best_metric_value:
                best_metric_value = metric_value
                best_params = params
                best_result_summary = result_summary

        logger.success(
            f"Best parameters found: {best_params} (Metric: {best_metric_value:.2f})"
        )
        return {
            "best_params": best_params,
            "best_metrics": best_result_summary,
            "metric_optimized": optimize_metric,
        }

    def walk_forward_analysis(
        self,
        data: pd.DataFrame,
        strategy_class: type[bt.Strategy],
        param_grid: dict,
        train_days: int = 180,
        test_days: int = 30,
        commission: float = 0.0002,
        slippage_perc: float = 0.001,
        optimize_metric: str = "net_profit",
    ) -> dict:
        """Run Walk-Forward Analysis (WFA) pipeline."""
        logger.info(
            f"Starting Walk-Forward Analysis (Train: {train_days}d, Test: {test_days}d)"
        )

        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        start_date = data.index.min()
        end_date = data.index.max()

        current_date = start_date
        windows = []

        total_net_profit = 0.0
        total_trades = 0
        total_won = 0
        total_gross_profit = 0.0
        total_gross_loss = 0.0

        wfa_results = []
        engine = BacktestEngine(initial_cash=self.initial_cash)

        while current_date + timedelta(days=train_days + test_days) <= end_date:
            train_end = current_date + timedelta(days=train_days)
            test_end = train_end + timedelta(days=test_days)

            # Split data
            train_data = data[(data.index >= current_date) & (data.index < train_end)]
            test_data = data[(data.index >= train_end) & (data.index < test_end)]

            logger.info(
                f"WFA Window | Train: {current_date.date()} to {train_end.date()} | Test: {train_end.date()} to {test_end.date()}"
            )

            # 1. Optimize on Train Data
            opt_result = self.run_grid_search(
                data=train_data,
                strategy_class=strategy_class,
                param_grid=param_grid,
                commission=commission,
                slippage_perc=slippage_perc,
                optimize_metric=optimize_metric,
            )

            best_params = opt_result.get("best_params") or {}

            # 2. Forward Test on Out-of-Sample (Test) Data using best params
            test_result = engine.run_backtest(
                data=test_data,
                strategy_class=strategy_class,
                strategy_params=best_params,
                commission=commission,
                slippage_perc=slippage_perc,
            )

            wfa_results.append(
                {
                    "window_start": current_date,
                    "train_end": train_end,
                    "test_end": test_end,
                    "best_params": best_params,
                    "test_metrics": test_result,
                }
            )

            # Accumulate overall WFA metrics
            total_net_profit += test_result.get("net_profit", 0)
            total_trades += test_result.get("total_trades", 0)
            total_won += test_result.get("won_trades", 0)
            total_gross_profit += test_result.get("gross_profit", 0)
            total_gross_loss += test_result.get("gross_loss", 0)

            # Shift window forward by test_days
            current_date += timedelta(days=test_days)

        # Calculate final aggregated WFA metrics
        overall_win_rate = (total_won / total_trades * 100) if total_trades > 0 else 0
        overall_profit_factor = (
            (total_gross_profit / total_gross_loss) if total_gross_loss > 0 else 0
        )
        overall_roi = (total_net_profit / self.initial_cash) * 100

        logger.success(
            f"WFA Completed. Overall Net Profit: ${total_net_profit:.2f}, ROI: {overall_roi:.2f}%"
        )

        return {
            "windows": wfa_results,
            "overall_metrics": {
                "net_profit": total_net_profit,
                "roi": overall_roi,
                "total_trades": total_trades,
                "win_rate": overall_win_rate,
                "profit_factor": overall_profit_factor,
            },
        }
