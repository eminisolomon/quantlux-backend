import os
import signal

from telegram import Update
from telegram.ext import ContextTypes

from app.core import messages as msg
from app.core.decorators import telegram_error_handler
from app.core.settings import settings
from app.utils.logger import logger


@telegram_error_handler("❌ Error enabling Auto Trading.")
async def enable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /enable command - Enable auto trading."""
    settings.ENABLE_AUTO_TRADING = True
    logger.info("User enabled Auto Trading via Telegram")
    await update.message.reply_text(msg.AUTO_TRADING_ENABLED, parse_mode="Markdown")


@telegram_error_handler("❌ Error disabling Auto Trading.")
async def disable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /disable command - Disable auto trading."""
    settings.ENABLE_AUTO_TRADING = False
    logger.info("User disabled Auto Trading via Telegram")
    await update.message.reply_text(msg.AUTO_TRADING_DISABLED, parse_mode="Markdown")


@telegram_error_handler("❌ Error stopping bot.")
async def stop_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - Stop the bot execution."""
    trading_bot = context.bot_data.get("trading_bot")

    if not trading_bot:
        await update.message.reply_text(
            "❌ TradingBot not injected. Cannot stop.", parse_mode="Markdown"
        )
        return

    await update.message.reply_text(msg.BOT_STOPPED, parse_mode="Markdown")
    logger.warning("Stop command received from Telegram. Shutting down...")

    os.kill(os.getpid(), signal.SIGTERM)
