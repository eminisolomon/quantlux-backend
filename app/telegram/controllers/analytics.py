"""Telegram commands for performance analytics and reporting."""

from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from app.core import messages as msg
from app.core.decorators import telegram_error_handler
from app.risk.drawdown import DrawdownManager
from app.services.account import AccountService
from app.telegram.views.formatters import MessageFormatter
from app.telegram.views.keyboards import KeyboardBuilder


class AnalyticsController:
    """Telegram controller for trading analytics and performance summary."""

    def __init__(
        self,
        account_service: "AccountService",
        performance_tracker: Any,
        drawdown: DrawdownManager,
    ):
        """Initialize with services."""
        self.account_service = account_service
        self.tracker = performance_tracker
        self.drawdown = drawdown

    async def performance_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Show trading performance metrics."""
        report_msg = self.tracker.format_report_for_telegram()
        await update.message.reply_text(report_msg, parse_mode="Markdown")

    async def drawdown_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Show current drawdown status."""
        summary_data = await self.account_service.get_account_summary()
        current_equity = summary_data.get("equity", 0.0)

        current_equity = await self.account_service.get_equity()
        summary_text = self.drawdown.get_status_summary(current_equity)
        await update.message.reply_text(summary_text, parse_mode="Markdown")

    @telegram_error_handler(msg.HISTORY_RETRIEVAL_ERROR)
    async def trades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent trade history from database."""
        # Get last 10 trades
        recent_trades = self.trade_storage.get_closed_trades(limit=10)

        if not recent_trades:
            await update.message.reply_text(
                msg.NO_CLOSED_TRADES,
                parse_mode="Markdown",
            )
            return

        # Format trades
        msg_text = f"{MessageFormatter.create_header('Recent Trades (Last 10)')}\n\n"
        for trade in recent_trades:
            profit_emoji = "🟢" if trade.profit > 0 else "🔴"
            close_time = (
                trade.close_time.strftime("%Y-%m-%d %H:%M")
                if trade.close_time
                else "N/A"
            )

            msg_text += f"{profit_emoji} *{trade.symbol}* {trade.trade_type}\n"
            msg_text += f"Profit: {MessageFormatter.format_pnl(trade.profit)} | Close: {close_time}\n\n"

        # Add statistics
        stats = self.trade_storage.get_statistics()
        msg_text += "━━━━━━━━━━━━━━━\n"
        msg_text += f"Total: {stats['closed_trades']} trades\n"
        msg_text += f"Win Rate: {MessageFormatter.format_percentage(stats['win_rate'], show_sign=False)}\n"
        msg_text += (
            f"Total Profit: {MessageFormatter.format_pnl(stats['total_profit'])}"
        )

        await update.message.reply_text(msg_text, parse_mode="Markdown")

    @telegram_error_handler("❌ Error retrieving risk data.")
    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show risk management dashboard."""
        if not self.account_service.is_connected():
            await update.message.reply_text(
                msg.MT_NOT_CONNECTED,
                parse_mode="Markdown",
            )
            return

        summary = await self.account_service.get_account_summary()
        if not summary:
            await update.message.reply_text("❌ Could not retrieve account info.")
            return

        acc = summary["account"]
        health = (
            "🟢 HEALTHY"
            if acc.marginLevel and acc.marginLevel > 150
            else (
                "🟡 CAUTION"
                if acc.marginLevel and acc.marginLevel > 100
                else "🔴 DANGER"
            )
        )

        content = [
            f"Health   {health}",
            f"Margin   {acc.marginLevel:.0f}%" if acc.marginLevel else "Margin   N/A",
            "",
            f"Balance  {MessageFormatter.format_currency(acc.balance, acc.currency)}",
            f"Equity   {MessageFormatter.format_currency(acc.equity, acc.currency)}",
            f"Open     {summary['positions_count']} positions",
        ]

        msg_text = MessageFormatter.create_box("RISK DASHBOARD", content)

        await update.message.reply_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_risk_keyboard(),
        )

    @telegram_error_handler("❌ Error displaying menu.")
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main interactive menu."""
        await update.message.reply_text(
            "🎛️ *MAIN MENU*\n\nSelect an option:",
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_main_menu(),
        )
