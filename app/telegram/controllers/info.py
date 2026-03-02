from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from app.core import messages as msg
from app.core.decorators import telegram_error_handler
from app.core.exceptions import QuantLuxError
from app.core.settings import settings
from app.services.account import AccountService
from app.telegram.views.formatters import MessageFormatter
from app.telegram.views.messages import (
    get_help_message,
    get_welcome_message,
)


class InfoController:
    """Controller for account and system information commands."""

    def __init__(self, account_service: AccountService):
        self.account_service = account_service

    @telegram_error_handler()
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(get_welcome_message(), parse_mode="Markdown")

    @telegram_error_handler()
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await update.message.reply_text(get_help_message(), parse_mode="Markdown")

    @telegram_error_handler()
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command with rich formatting."""
        if not self.account_service.is_connected():
            raise QuantLuxError(message_key="MT_NOT_CONNECTED")

        summary = await self.account_service.get_account_summary()
        if not summary:
            raise QuantLuxError(message_key="ACC_INFO_FAILED")

        acc = summary["account"]
        msg_text = MessageFormatter.format_status_box(
            connected=True,
            balance=acc.balance,
            equity=acc.equity,
            currency=acc.currency,
            auto_trading=settings.ENABLE_AUTO_TRADING,
        )

        await update.message.reply_text(msg_text, parse_mode="Markdown")

    @telegram_error_handler()
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command with rich formatting."""
        if not self.account_service.is_connected():
            raise QuantLuxError(message_key="MT_NOT_CONNECTED")

        summary = await self.account_service.get_account_summary()
        if not summary:
            raise QuantLuxError(message_key="ACC_INFO_FAILED")

        acc = summary["account"]
        msg_text = MessageFormatter.format_status_box(
            connected=True,
            balance=acc.balance,
            equity=acc.equity,
            currency=acc.currency,
            auto_trading=settings.ENABLE_AUTO_TRADING,
        )

        await update.message.reply_text(msg_text, parse_mode="Markdown")

    @telegram_error_handler()
    async def positions_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /positions command with rich formatting."""
        if not self.account_service.is_connected():
            raise QuantLuxError(message_key="MT_NOT_CONNECTED")

        positions = await self.account_service.get_detailed_positions()
        summary = await self.account_service.get_account_summary()
        currency = summary.get("account").currency if summary else "USD"

        raw_positions = [
            p.model_dump() if hasattr(p, "model_dump") else p.__dict__
            for p in positions
        ]
        msg_text = MessageFormatter.format_positions_summary(raw_positions, currency)
        await update.message.reply_text(msg_text, parse_mode="Markdown")

    @telegram_error_handler()
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command - List pending orders."""
        if not self.account_service.is_connected():
            raise QuantLuxError(message_key="MT_NOT_CONNECTED")

        orders = await self.account_service.get_detailed_orders()
        if not orders:
            await update.message.reply_text(
                msg.NO_PENDING_ORDERS, parse_mode="Markdown"
            )
            return

        msg_text = f"{MessageFormatter.create_header('Pending Orders', '⏳')}\n\n"
        for order in orders:
            msg_text += f"• {order.symbol} {order.volumeInitial} @ {order.openPrice}\n"

        await update.message.reply_text(msg_text, parse_mode="Markdown")

    @telegram_error_handler()
    async def connect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /connect command - Check detailed connection state."""
        if await self.account_service.ensure_connected():
            msg_str = msg.CONNECT_SUCCESS.format(
                account_id=self.account_service.metaapi.account_id
            )
        else:
            msg_str = msg.CONNECT_FAILED

        await update.message.reply_text(msg_str, parse_mode="Markdown")

    @telegram_error_handler()
    async def summary_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /summary command."""
        if not self.account_service.is_connected():
            raise QuantLuxError(message_key="MT_NOT_CONNECTED")

        summary = await self.account_service.get_account_summary()
        if not summary:
            raise QuantLuxError(message_key="ACC_INFO_FAILED")

        acc = summary["account"]
        msg_text = (
            f"{MessageFormatter.create_header('Daily Summary')}\n\n"
            f"Balance  {MessageFormatter.format_currency(acc.balance, acc.currency)}\n"
            f"Equity   {MessageFormatter.format_currency(acc.equity, acc.currency)}\n"
            f"Open Positions: {summary['positions_count']}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d')}"
        )
        await update.message.reply_text(msg_text, parse_mode="Markdown")
