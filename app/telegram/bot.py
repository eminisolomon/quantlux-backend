from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core.exceptions import ConfigurationError
from app.core.settings import settings
from app.telegram.controllers.ai_chat import AIChatController
from app.telegram.controllers.analytics import AnalyticsController
from app.telegram.controllers.backtesting import (
    backtest_command,
)
from app.telegram.controllers.callbacks import CallbacksController
from app.telegram.controllers.control import (
    disable_command,
    enable_command,
    stop_bot_command,
)
from app.telegram.controllers.info import InfoController
from app.utils.logger import logger
from app.utils.notifiers import get_trade_notifier


class TelegramBot:
    """Telegram bot for managing the trading system."""

    def __init__(
        self,
        analytics_controller: AnalyticsController,
        callbacks_controller: CallbacksController,
        info_controller: InfoController,
        ai_chat_controller: AIChatController = None,
    ):
        """Initialize bot configuration and validate settings."""
        self.logger = logger
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.application: Application | None = None
        self.trading_bot: Any = None

        self.analytics_controller = analytics_controller
        self.callbacks_controller = callbacks_controller
        self.info_controller = info_controller
        self.ai_chat_controller = ai_chat_controller

        if not self.bot_token:
            raise ConfigurationError("TELEGRAM_BOT_TOKEN is not set")
        if not self.chat_id:
            raise ConfigurationError("TELEGRAM_CHAT_ID is not set")

    async def _error_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log errors occurred during update processing."""
        self.logger.error(f"Update {update} caused error {context.error}")

    def _register_info_handlers(self, app: Application):
        """Register command handlers for account and system information."""
        app.add_handler(CommandHandler("start", self.info_controller.start_command))
        app.add_handler(CommandHandler("help", self.info_controller.help_command))
        app.add_handler(CommandHandler("status", self.info_controller.status_command))
        app.add_handler(CommandHandler("balance", self.info_controller.balance_command))
        app.add_handler(
            CommandHandler("positions", self.info_controller.positions_command)
        )
        app.add_handler(CommandHandler("orders", self.info_controller.orders_command))
        app.add_handler(CommandHandler("summary", self.info_controller.summary_command))
        app.add_handler(CommandHandler("connect", self.info_controller.connect_command))

    def _register_analysis_handlers(self, app: Application):
        """Register command handlers for performance and risk analytics."""
        app.add_handler(
            CommandHandler("performance", self.analytics_controller.performance_command)
        )
        app.add_handler(
            CommandHandler("drawdown", self.analytics_controller.drawdown_command)
        )
        app.add_handler(
            CommandHandler("trades", self.analytics_controller.trades_command)
        )
        app.add_handler(CommandHandler("backtest", backtest_command))
        app.add_handler(CommandHandler("risk", self.analytics_controller.risk_command))
        app.add_handler(CommandHandler("menu", self.analytics_controller.menu_command))

    def _register_control_handlers(self, app: Application):
        """Register command handlers for bot execution control."""
        app.add_handler(CommandHandler("enable", enable_command))
        app.add_handler(CommandHandler("disable", disable_command))
        app.add_handler(CommandHandler("stop", stop_bot_command))

    def _register_ai_handlers(self, app: Application):
        """Register AI-powered command and message handlers."""
        if not self.ai_chat_controller:
            return

        app.add_handler(
            CommandHandler("ai_report", self.ai_chat_controller.ai_report_command)
        )
        app.add_handler(
            CommandHandler("ai_analyze", self.ai_chat_controller.ai_analyze_command)
        )

        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.ai_chat_controller.handle_message,
            )
        )

    def setup_handlers(self, application: Application):
        """Configure all command and callback handlers for the application."""
        application.bot_data["trading_bot"] = self.trading_bot

        notifier = get_trade_notifier()
        notifier.set_bot(self)

        self._register_info_handlers(application)
        self._register_analysis_handlers(application)
        self._register_control_handlers(application)
        self._register_ai_handlers(application)

        application.add_handler(
            CallbackQueryHandler(self.callbacks_controller.handle_callback_query)
        )
        application.add_error_handler(self._error_handler)

    async def start(self):
        """Initialize, start, and begin polling for the Telegram bot."""
        self.logger.info("Starting Telegram bot...")
        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers(self.application)

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        self.logger.info("Telegram bot started successfully!")

    async def stop(self):
        """Shut down the Telegram bot application cleanly."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        self.logger.info("Telegram bot stopped.")

    async def send_message(self, message: str, parse_mode: str | None = "Markdown"):
        """Send a message to the configured notification chat."""
        if not self.application:
            self.logger.warning("Bot not started, cannot send message")
            return

        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode=parse_mode
            )
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
