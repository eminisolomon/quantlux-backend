"""
Command-line backtesting utility for QuantLux-FX

Usage:
    python -m scripts.backtest --symbol EURUSD --start 2023-01-01 --end 2024-01-01
    python -m scripts.backtest --help
"""

import argparse
import sys

from backtesting import (
    BacktestEngine,
    load_sample_data,
    QuantLuxStrategy,
    ParameterOptimizer,
)

from app.utils.logger import logger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backtest QuantLux-FX trading strategies"
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Currency pair to backtest",
    )

    parser.add_argument(
        "--start", type=str, default=None, help="Start date (YYYY-MM-DD)"
    )

    parser.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")

    parser.add_argument(
        "--cash", type=float, default=10000.0, help="Initial cash (default: 10000)"
    )

    parser.add_argument(
        "--rsi-period", type=int, default=14, help="RSI period (default: 14)"
    )

    parser.add_argument(
        "--rsi-oversold", type=int, default=30, help="RSI oversold level (default: 30)"
    )

    parser.add_argument(
        "--rsi-overbought",
        type=int,
        default=70,
        help="RSI overbought level (default: 70)",
    )

    parser.add_argument(
        "--stop-loss",
        type=float,
        default=2.0,
        help="Stop loss percentage (default: 2.0)",
    )

    parser.add_argument(
        "--take-profit",
        type=float,
        default=4.0,
        help="Take profit percentage (default: 4.0)",
    )

    parser.add_argument(
        "--commission",
        type=float,
        default=0.0002,
        help="Commission as fraction (default: 0.0002 = 2 pips)",
    )

    parser.add_argument(
        "--optimize", action="store_true", help="Run Grid Search Optimization"
    )

    parser.add_argument("--wfa", action="store_true", help="Run Walk-Forward Analysis")

    args = parser.parse_args()

    if not args.symbol:
        try:
            from app.core.symbols import get_symbol_manager

            manager = get_symbol_manager()
            symbols = manager.get_enabled_symbols()

            print("\nAvailable Symbols:")
            for i, sym in enumerate(symbols, 1):
                print(f"  {i}. {sym}")

            selection = input(
                "\nSelect symbol (number) or enter name [EURUSD]: "
            ).strip()

            if not selection:
                args.symbol = "EURUSD"
            elif selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(symbols):
                    args.symbol = symbols[idx]
                else:
                    print("Invalid selection. Using default EURUSD.")
                    args.symbol = "EURUSD"
            else:
                args.symbol = selection.upper()
        except ImportError:
            args.symbol = input("\nEnter symbol [EURUSD]: ").strip().upper() or "EURUSD"

    if not args.start:
        args.start = input("Enter start date [2023-01-01]: ").strip() or "2023-01-01"

    if not args.end:
        args.end = input("Enter end date [2024-01-01]: ").strip() or "2024-01-01"

    try:
        logger.info(f"Starting backtest for {args.symbol}")
        logger.info(f"Period: {args.start} to {args.end}")
        logger.info(f"Initial cash: ${args.cash:.2f}")

        data = load_sample_data(symbol=args.symbol, start=args.start, end=args.end)

        if len(data) == 0:
            logger.error("No data loaded. Cannot run backtest.")
            return 1

        if args.wfa or args.optimize:
            optimizer = ParameterOptimizer(initial_cash=args.cash)
            param_grid = {
                "rsi_period": range(10, 18, 2),
                "rsi_oversold": range(25, 35, 5),
                "rsi_overbought": range(65, 75, 5),
            }
            if args.wfa:
                logger.info("Running Walk-Forward Analysis...")
                results = optimizer.walk_forward_analysis(
                    data=data,
                    strategy_class=QuantLuxStrategy,
                    param_grid=param_grid,
                    commission=args.commission,
                )
                print("\n" + "=" * 50)
                print(" WALK-FORWARD ANALYSIS RESULTS")
                print("=" * 50)
                metrics = results["overall_metrics"]
                print(f"  Overall Net Profit: ${metrics['net_profit']:.2f}")
                print(f"  Overall ROI:        {metrics['roi']:.2f}%")
                print(f"  Total Trades:       {metrics['total_trades']}")
                print(f"  Overall Win Rate:   {metrics['win_rate']:.1f}%")
                print(f"  Profit Factor:      {metrics['profit_factor']:.2f}")
                print("=" * 50 + "\n")
            else:
                logger.info("Running Grid Search Optimization...")
                results = optimizer.run_grid_search(
                    data=data,
                    strategy_class=QuantLuxStrategy,
                    param_grid=param_grid,
                    commission=args.commission,
                )
                print("\n" + "=" * 50)
                print(" OPTIMIZATION RESULTS")
                print("=" * 50)
                print(f"  Best Params: {results['best_params']}")
                best_metrics = results["best_metrics"]
                if best_metrics:
                    print(f"  Best Net Profit: ${best_metrics['net_profit']:.2f}")
                    print(f"  Best ROI: {best_metrics['roi']:.2f}%")
                print("=" * 50 + "\n")
            return 0

        strategy_params = {
            "rsi_period": args.rsi_period,
            "rsi_oversold": args.rsi_oversold,
            "rsi_overbought": args.rsi_overbought,
            "stop_loss_pct": args.stop_loss,
            "take_profit_pct": args.take_profit,
        }

        logger.info(f"Strategy params: {strategy_params}")

        engine = BacktestEngine(initial_cash=args.cash)
        results = engine.run_backtest(
            data=data,
            strategy_class=QuantLuxStrategy,
            strategy_params=strategy_params,
            commission=args.commission,
        )

        engine.print_results(results)

        print("📝 Analysis:")
        if results["sharpe_ratio"] > 1.5:
            print("  ✅ Excellent risk-adjusted returns (Sharpe > 1.5)")
        elif results["sharpe_ratio"] > 1.0:
            print("  ✅ Good risk-adjusted returns (Sharpe > 1.0)")
        else:
            print("  ⚠️  Poor risk-adjusted returns (Sharpe < 1.0)")

        if results["profit_factor"] > 1.5:
            print("  ✅ Strong profit factor (> 1.5)")
        elif results["profit_factor"] > 1.0:
            print("  ⚠️  Marginal profit factor (> 1.0)")
        else:
            print("  ❌ Losing strategy (profit factor < 1.0)")

        if results["max_drawdown_pct"] < 10:
            print("  ✅ Low drawdown (< 10%)")
        elif results["max_drawdown_pct"] < 20:
            print("  ⚠️  Moderate drawdown (< 20%)")
        else:
            print("  ❌ High drawdown (> 20%) - risky!")

        return 0

    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
