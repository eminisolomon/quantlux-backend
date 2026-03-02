from telegram import Update
from telegram.ext import ContextTypes

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import CHAT_CONTEXT_PROMPT, CHAT_SYSTEM
from app.analytics.ai_insights import generate_performance_report
from app.analytics.ai_market import analyze_market
from app.analytics.tracker import PerformanceTracker
from app.core import messages as msg
from app.core.decorators import require_feature, telegram_error_handler
from app.services.account import AccountService


class AIChatController:
    """Controller for AI-powered Telegram commands and natural language chat."""

    def __init__(
        self,
        gemini: GeminiClient,
        account_service: "AccountService",
        tracker: PerformanceTracker,
    ):
        """Initialize with services."""
        self.gemini = gemini
        self.account_service = account_service
        self.tracker = tracker

        pass

    @require_feature("ENABLE_AI_FEATURES", notify_telegram=True)
    @telegram_error_handler("❌ Error generating AI report.")
    async def ai_report_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handler for /ai_report — AI-powered performance coaching."""
        status_msg = await update.message.reply_text(
            msg.AI_REPORT_GENERATING, parse_mode="Markdown"
        )

        report = await generate_performance_report(self.gemini, self.tracker)
        if report:
            for chunk in _split_message(report):
                await update.message.reply_text(chunk, parse_mode="Markdown")
        if not report:
            await status_msg.edit_text(msg.AI_REPORT_FAILED, parse_mode="Markdown")
            return

    @require_feature("ENABLE_AI_FEATURES", notify_telegram=True)
    @telegram_error_handler("❌ Error analysing market.")
    async def ai_analyze_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handler for /ai_analyze — AI-powered market analysis.

        Usage: /ai_analyze EURUSD [H1|H4|D1]
        """
        args = context.args or []
        symbol = args[0].upper() if args else "EURUSD"
        timeframe = args[1].upper() if len(args) > 1 else "H1"

        await update.message.reply_text(
            f"🔄 Analysing {symbol} {timeframe}...", parse_mode="Markdown"
        )

        result = await analyze_market(
            self.gemini, self.account_service.metaapi, symbol, timeframe
        )

        if result:
            for chunk in _split_message(result):
                await update.message.reply_text(chunk, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "⚠️ Could not analyse market.", parse_mode="Markdown"
            )

    @require_feature("ENABLE_AI_FEATURES", notify_telegram=True)
    @telegram_error_handler("❌ AI chat error. Please try again.")
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle natural language messages via Gemini AI.

        This is a catch-all handler for non-command text messages.
        """
        if not update.message or not update.message.text:
            return

        user_message = update.message.text.strip()

        if not user_message or user_message.startswith("/"):
            return

        if not self.gemini.is_available:
            await update.message.reply_text(
                "⚠️ AI chat unavailable — GEMINI_API_KEY not configured."
            )
            return

        summary = await self.account_service.get_account_summary()
        if not summary:
            await update.message.reply_text("❌ Could not retrieve account info.")
            return

        acc = summary["account"]
        positions = await self.account_service.get_detailed_positions()

        balance = acc.balance
        equity = acc.equity

        positions_text = "None"
        if positions:
            pos_items = []
            for p in positions:
                sym = getattr(p, "symbol", None) or (
                    isinstance(p, dict) and p.get("symbol", "?")
                )
                profit = getattr(p, "profit", None) or (
                    isinstance(p, dict) and p.get("profit", 0)
                )
                pos_items.append(f"{sym}: ${profit:.2f}")
            positions_text = ", ".join(pos_items) if pos_items else "None"

        prompt = CHAT_CONTEXT_PROMPT.format(
            balance=balance,
            equity=equity,
            positions=positions_text,
            strategies="RSI, ICT, Mean Reversion",
            news_status="Active" if True else "Disabled",
            user_message=user_message,
        )

        response = await self.gemini.generate(
            prompt=prompt,
            system_instruction=CHAT_SYSTEM,
        )

        if response:
            for chunk in _split_message(response):
                await update.message.reply_text(chunk, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "🤔 I couldn't process that. Try again or use /help."
            )


def _split_message(text: str, max_length: int = 4000) -> list:
    """Split a long message into Telegram-safe chunks."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_idx = text.rfind("\n", 0, max_length)
        if split_idx == -1:
            split_idx = text.rfind(" ", 0, max_length)
        if split_idx == -1:
            split_idx = max_length

        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()

    return chunks
