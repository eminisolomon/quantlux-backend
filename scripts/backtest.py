#!/usr/bin/env python3
"""
Command-line backtesting utility for QuantLux-FX

Usage:
    python -m scripts.backtest --symbol EURUSD --start 2023-01-01 --end 2024-01-01
    python -m scripts.backtest --help
"""

import argparse
import sys

from backtesting.engine import BacktestEngine, load_sample_data

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

    args = parser.parse_args()

    # Interactive Mode
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

        # Load historical data
        data = load_sample_data(symbol=args.symbol, start=args.start, end=args.end)

        if len(data) == 0:
            logger.error("No data loaded. Cannot run backtest.")
            return 1

        # Setup strategy parameters
        strategy_params = {
            "rsi_period": args.rsi_period,
            "rsi_oversold": args.rsi_oversold,
            "rsi_overbought": args.rsi_overbought,
            "stop_loss_pct": args.stop_loss,
            "take_profit_pct": args.take_profit,
        }

        logger.info(f"Strategy params: {strategy_params}")

        # Run backtest
        engine = BacktestEngine(initial_cash=args.cash)
        results = engine.run_backtest(
            data=data, strategy_params=strategy_params, commission=args.commission
        )

        # Print results
        engine.print_results(results)

        # Provide recommendations
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
