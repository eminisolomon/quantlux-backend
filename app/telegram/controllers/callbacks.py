"""Callback handlers for interactive buttons."""

from telegram import Update
from telegram.ext import ContextTypes

from app.analytics.tracker import PerformanceTracker
from app.core import messages as msg
from app.core.decorators import telegram_error_handler
from app.core.exceptions import QuantLuxError
from app.core.settings import settings
from app.services.account import AccountService
from app.telegram.views.formatters import MessageFormatter
from app.telegram.views.keyboards import KeyboardBuilder


class CallbacksController:
    """Controller for handling callback queries."""

    def __init__(self, tracker: PerformanceTracker, account_service: AccountService):
        self.tracker = tracker
        self.account_service = account_service

    @telegram_error_handler(msg.MENU_ERROR)
    async def handle_callback_query(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == "status":
            await self._show_status(query)
        elif callback_data == "balance":
            await self._show_balance(query)
        elif callback_data == "positions":
            await self._show_positions(query)
        elif callback_data == "orders":
            await self._show_orders(query)
        elif callback_data == "performance":
            await self._show_performance(query)
        elif callback_data == "risk":
            await self._show_risk(query)
        elif callback_data == "menu":
            await self._show_menu(query)
        elif callback_data == "close":
            await query.message.delete()
        elif callback_data.startswith("perf_"):
            await self._show_performance_period(query, callback_data)

    async def _show_status(self, query):
        if not self.account_service.is_connected():
            await query.edit_message_text(
                msg.MT_NOT_CONNECTED,
                parse_mode="Markdown",
            )
            return

        summary = await self.account_service.get_account_summary()
        if not summary:
            await query.edit_message_text(
                msg.ACC_INFO_FAILED,
                parse_mode="Markdown",
            )
            return

        acc = summary["account"]
        msg_text = MessageFormatter.format_status_box(
            connected=True,
            balance=acc.balance,
            equity=acc.equity,
            currency=acc.currency,
            auto_trading=settings.ENABLE_AUTO_TRADING,
        )

        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_status_keyboard(),
        )

    async def _show_balance(self, query):
        if not self.account_service.is_connected():
            await query.edit_message_text(msg.MT_NOT_CONNECTED, parse_mode="Markdown")
            return

        summary = await self.account_service.get_account_summary()
        if not summary:
            await query.edit_message_text(
                msg.ACC_INFO_FAILED,
                parse_mode="Markdown",
            )
            return

        acc = summary["account"]
        msg_text = (
            f"💰 *BALANCE*\n\n"
            f"Balance: {MessageFormatter.format_currency(acc.balance, acc.currency)}\n"
            f"Equity: {MessageFormatter.format_currency(acc.equity, acc.currency)}\n"
            f"P&L: {MessageFormatter.format_pnl(acc.pnl, acc.currency)}\n"
            f"Return: {MessageFormatter.format_percentage(acc.pnl_pct)}"
        )

        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_status_keyboard(),
        )

    async def _show_positions(self, query):
        if not self.account_service.is_connected():
            await query.edit_message_text(msg.MT_NOT_CONNECTED, parse_mode="Markdown")
            return

        positions = await self.metaapi.get_positions()
        acc = await self.metaapi.get_account_info()
        currency = acc.currency if acc else "USD"

        raw_positions = [
            p.dict() if hasattr(p, "dict") else p.__dict__ for p in positions
        ]

        msg_text = MessageFormatter.format_positions_summary(raw_positions, currency)
        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_positions_keyboard(),
        )

    async def _show_orders(self, query):
        if not self.account_service.is_connected():
            await query.edit_message_text(msg.MT_NOT_CONNECTED, parse_mode="Markdown")
            return

        orders = await self.metaapi.get_orders()

        if not orders:
            msg_text = "⏳ *PENDING ORDERS*\n\nNo pending orders."
        else:
            msg_text = "⏳ *PENDING ORDERS*\n\n"
            for order in orders:
                symbol = order.symbol
                volume = order.volume
                price = order.open_price
                msg_text += f"• {symbol} {volume} @ {price}\n"

        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_status_keyboard(),
        )

    async def _show_performance(self, query):
        stats = self.tracker.get_stats(days=7)  # Last 7 days

        msg_text = (
            f"📈 *PERFORMANCE (7 DAYS)*\n\n"
            f"Trades: {stats.total_trades} ({stats.winning_trades}W / {stats.losing_trades}L)\n"
            f"Win Rate: {stats.win_rate:.1f}%\n"
            f"Profit Factor: {stats.profit_factor:.2f}\n\n"
            f"Avg Win: ${stats.avg_win:.2f}\n"
            f"Avg Loss: ${stats.avg_loss:.2f}\n\n"
            f"Best Trade: +${stats.largest_win:.2f}\n"
            f"Worst Trade: -${stats.largest_loss:.2f}\n\n"
            f"Max Drawdown: ${stats.max_drawdown:.2f}"
        )

        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_performance_keyboard(),
        )

    async def _show_risk(self, query):
        if not self.account_service.is_connected():
            await query.edit_message_text(
                msg.MT_NOT_CONNECTED,
                parse_mode="Markdown",
            )
            return

        summary = await self.account_service.get_account_summary()
        if not summary:
            raise QuantLuxError(message_key="ACC_INFO_FAILED")

        acc = summary["account"]
        health = (
            msg.RISK_HEALTHY
            if acc.marginLevel and acc.marginLevel > 150
            else (
                msg.RISK_CAUTION
                if acc.marginLevel and acc.marginLevel > 100
                else msg.RISK_DANGER
            )
        )

        msg_text = (
            f"{msg.RISK_DASHBOARD_TITLE}\n\n"
            f"Account Health: {health}\n"
            f"Margin Level: {acc.marginLevel:.0f}% if acc.marginLevel else 'N/A'\n\n"
            f"Balance: ${acc.balance:,.2f}\n"
            f"Equity: ${acc.equity:,.2f}\n"
            f"Margin Used: ${acc.margin:,.2f}\n"
            f"Free Margin: ${acc.freeMargin:,.2f}\n\n"
            f"Open Positions: {summary['positions_count']}\n"
            f"Exposure: {(abs(summary['total_profit']) / acc.balance * 100) if acc.balance > 0 else 0:.1f}%"
        )

        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_risk_keyboard(),
        )

    async def _show_menu(self, query):
        msg_text = msg.MAIN_MENU

        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_main_menu(),
        )

    async def _show_performance_period(self, query, callback_data):
        period_map = {
            "perf_today": (1, "TODAY"),
            "perf_week": (7, "WEEK"),
            "perf_month": (30, "MONTH"),
        }

        days, label = period_map.get(callback_data, (7, "WEEK"))
        stats = self.tracker.get_stats(days=days)

        msg_text = (
            f"📈 *PERFORMANCE ({label})*\n\n"
            f"Trades: {stats.total_trades} ({stats.winning_trades}W / {stats.losing_trades}L)\n"
            f"Win Rate: {stats.win_rate:.1f}%\n"
            f"Profit Factor: {stats.profit_factor:.2f}\n\n"
            f"Total P&L: ${stats.total_profit - stats.total_loss:.2f}\n"
            f"Avg Win: ${stats.avg_win:.2f}\n"
            f"Avg Loss: ${stats.avg_loss:.2f}\n\n"
            f"Best: +${stats.largest_win:.2f}\n"
            f"Worst: -${stats.largest_loss:.2f}\n\n"
            f"Drawdown: ${stats.current_drawdown:.2f}\n"
            f"Max DD: ${stats.max_drawdown:.2f}"
        )

        await query.edit_message_text(
            msg_text,
            parse_mode="Markdown",
            reply_markup=KeyboardBuilder.create_performance_keyboard(),
        )
