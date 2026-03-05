"""Backtest Runner Engine."""

import backtrader as bt
import pandas as pd

from app.utils.logger import logger
from backtesting.strategy import QuantLuxStrategy


class BacktestEngine:
    """Main backtesting engine."""

    def __init__(self, initial_cash: float = 10000.0):
        self.initial_cash = initial_cash
        self.cerebro = None

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy_class: object | None = None,
        strategy_params: dict | None = None,
        commission: float = 0.0002,
        slippage_perc: float = 0.001,
    ) -> dict:
        """Run backtest on historical data."""
        logger.info(f"Starting backtest with ${self.initial_cash:.2f} initial cash")

        self.cerebro = bt.Cerebro()

        strat_cls = strategy_class if strategy_class else QuantLuxStrategy

        if strategy_params:
            self.cerebro.addstrategy(strat_cls, **strategy_params)
        else:
            self.cerebro.addstrategy(strat_cls)

        bt_data = bt.feeds.PandasData(dataname=data)
        self.cerebro.adddata(bt_data)

        self.cerebro.broker.setcash(self.initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        self.cerebro.broker.set_slippage_perc(slippage_perc)

        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

        logger.info("Running backtest...")
        starting_value = self.cerebro.broker.getvalue()

        results = self.cerebro.run()

        final_value = self.cerebro.broker.getvalue()

        strat = results[0]

        sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio", None)
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()

        net_profit = final_value - starting_value
        roi = (net_profit / starting_value) * 100

        total_trades = trades.get("total", {}).get("total", 0)
        won_trades = trades.get("won", {}).get("total", 0)
        lost_trades = trades.get("lost", {}).get("total", 0)

        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

        gross_profit = trades.get("won", {}).get("pnl", {}).get("total", 0)
        gross_loss = abs(trades.get("lost", {}).get("pnl", {}).get("total", 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        result_summary = {
            "starting_value": starting_value,
            "final_value": final_value,
            "net_profit": net_profit,
            "roi": roi,
            "sharpe_ratio": sharpe if sharpe else 0,
            "max_drawdown_pct": drawdown.get("max", {}).get("drawdown", 0),
            "total_trades": total_trades,
            "won_trades": won_trades,
            "lost_trades": lost_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
        }

        logger.success(f"Backtest complete! Final value: ${final_value:.2f}")
        logger.info(f"ROI: {roi:.2f}%, Win Rate: {win_rate:.1f}%, Sharpe: {sharpe}")

        return result_summary

    def print_results(self, results: dict):
        """Print formatted backtest results."""
        print("\n" + "=" * 50)
        print(" BACKTEST RESULTS")
        print("=" * 50)
        print("\n💰 Profitability:")
        print(f"  Starting Value: ${results['starting_value']:.2f}")
        print(f"  Final Value:    ${results['final_value']:.2f}")
        print(f"  Net Profit:     ${results['net_profit']:.2f}")
        print(f"  ROI:            {results['roi']:.2f}%")

        print("\n📊 Trade Statistics:")
        print(f"  Total Trades:   {results['total_trades']}")
        print(f"  Won:            {results['won_trades']}")
        print(f"  Lost:           {results['lost_trades']}")
        print(f"  Win Rate:       {results['win_rate']:.1f}%")
        print(f"  Profit Factor:  {results['profit_factor']:.2f}")

        print("\n⚡ Risk Metrics:")
        print(f"  Sharpe Ratio:   {results['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown:   {results['max_drawdown_pct']:.2f}%")

        print("\n💵 P&L:")
        print(f"  Gross Profit:   ${results['gross_profit']:.2f}")
        print(f"  Gross Loss:     ${results['gross_loss']:.2f}")
        print("=" * 50 + "\n")
