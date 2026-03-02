"""Telegram handler for running backtests."""

from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from app.core import messages as msg
from app.core.decorators import telegram_error_handler
from backtesting import BacktestEngine, load_sample_data


@telegram_error_handler(msg.BACKTEST_FAILED)
async def backtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run a backtest for a specific symbol."""
    args = context.args

    # Default parameters
    symbol = "EURUSD"
    days = 30
    initial_cash = 10000.0  # Added initial_cash variable

    # Parse arguments
    if args:
        symbol = args[0].upper()
        if len(args) > 1:
            try:
                days = int(args[1])
            except (IndexError, ValueError):  # Changed exception type
                await update.message.reply_text(msg.BACKTEST_INVALID_DAYS)
                return

    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()
    start_str = start_date.strftime("%Y-%m-%d")  # Added start_str
    end_str = end_date.strftime("%Y-%m-%d")  # Added end_str

    await update.message.reply_text(
        msg.BACKTEST_START.format(  # Updated reference and format arguments
            symbol=symbol, start=start_str, end=end_str, days=days, cash=initial_cash
        ),
        parse_mode="Markdown",
    )

    # Load Data
    data = load_sample_data(
        symbol=symbol, start=start_str, end=end_str
    )  # Updated start and end

    if len(data) == 0:
        await update.message.reply_text(msg.BACKTEST_NO_DATA.format(symbol=symbol))
        return

    # Setup Strategy Params (Simplified for Telegram)
    strategy_params = {
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "stop_loss_pct": 2.0,
        "take_profit_pct": 4.0,
    }

    # Run Backtest
    engine = BacktestEngine(initial_cash=10000.0)
    results = engine.run_backtest(
        data=data, strategy_params=strategy_params, commission=0.0002
    )

    # Format Results
    profit_emoji = "✅" if results["total_return_pct"] > 0 else "❌"

    msg = f"*Backtest Results: {symbol}*\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"Return: {results['total_return_pct']:.2f}% {profit_emoji}\n"
    msg += f"Net Profit: ${results['net_profit']:.2f}\n"
    msg += f"Total Trades: {results['total_trades']}\n"
    msg += f"Win Rate: {results['win_rate']:.1f}%\n"
    msg += f"Profit Factor: {results['profit_factor']:.2f}\n"
    msg += f"Max Drawdown: {results['max_drawdown_pct']:.2f}%\n"
    msg += f"Sharpe Ratio: {results['sharpe_ratio']:.2f}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
