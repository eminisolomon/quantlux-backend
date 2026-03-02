"""Trade notification system for Telegram."""

from datetime import datetime

from app.core.enums import SignalAction
from app.utils.logger import logger


class TradeNotifier:
    """Send trade notifications via Telegram."""

    def __init__(self, telegram_bot=None):
        """Initialize notifier."""
        self.bot = telegram_bot

    def set_bot(self, bot):
        """Set Telegram bot instance."""
        self.bot = bot

    async def notify_trade_opened(
        self,
        symbol: str,
        trade_type: SignalAction,
        volume: float,
        entry_price: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        strategy: str = "Unknown",
        confidence: float | None = None,
    ):
        """Send notification when trade opens."""
        if not self.bot:
            logger.warning("Telegram bot not set, skipping notification")
            return

        type_emoji = "🟢" if trade_type == SignalAction.BUY else "🔴"

        # Calculate risk/reward
        risk_reward = "N/A"
        if stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            if risk > 0:
                risk_reward = f"1:{reward / risk:.1f}"

        msg = (
            f"🚀 *NEW POSITION OPENED*\n\n"
            f"Symbol: {type_emoji} *{symbol}*\n"
            f"Type: {trade_type.value}\n"
            f"Volume: {volume} lots\n"
            f"Entry: {entry_price:.5f}\n"
        )

        if stop_loss:
            pips_sl = abs(entry_price - stop_loss) * 10000
            msg += f"SL: {stop_loss:.5f} (-{pips_sl:.0f} pips)\n"

        if take_profit:
            pips_tp = abs(take_profit - entry_price) * 10000
            msg += f"TP: {take_profit:.5f} (+{pips_tp:.0f} pips)\n"

        msg += f"\nStrategy: {strategy}\n"
        msg += f"R:R = {risk_reward}\n"

        if confidence:
            msg += f"Confidence: {confidence:.0f}%\n"

        msg += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        try:
            await self.bot.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send trade open notification: {e}")

    async def notify_trade_closed(
        self,
        symbol: str,
        trade_type: SignalAction,
        entry_price: float,
        exit_price: float,
        volume: float,
        profit: float,
        pips: float,
        duration: str,
        result: str = "WIN",
    ):
        """Send notification when trade closes."""
        if not self.bot:
            logger.warning("Telegram bot not set, skipping notification")
            return

        type_emoji = "🟢" if trade_type == SignalAction.BUY else "🔴"
        result_emoji = "✅" if result == "WIN" else "❌"

        msg = (
            f"{result_emoji} *POSITION CLOSED*\n\n"
            f"Symbol: {type_emoji} *{symbol}*\n"
            f"Type: {trade_type.value}\n"
            f"Entry: {entry_price:.5f} → Exit: {exit_price:.5f}\n"
            f"Volume: {volume} lots\n"
            f"Duration: {duration}\n\n"
            f"Pips: {pips:+.1f}\n"
            f"P&L: ${profit:+,.2f}\n\n"
            f"Result: {result} {result_emoji}\n"
            f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            await self.bot.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send trade close notification: {e}")

    async def notify_milestone(
        self,
        milestone_type: str,
        message: str,
        current_value: float | None = None,
        target_value: float | None = None,
    ):
        """Send milestone notification."""
        if not self.bot:
            logger.warning("Telegram bot not set, skipping notification")
            return

        emoji_map = {
            "daily_profit": "🎯",
            "weekly_profit": "🏆",
            "balance": "💰",
            "trades": "📊",
        }

        emoji = emoji_map.get(milestone_type, "🎉")

        msg = f"{emoji} *MILESTONE ACHIEVED!*\n\n{message}\n"

        if target_value and current_value:
            msg += f"\nTarget: ${target_value:,.2f} ✅\n"
            msg += f"Actual: ${current_value:,.2f}\n"

        msg += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        try:
            await self.bot.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send milestone notification: {e}")

    async def notify_risk_warning(
        self, warning_type: str, message: str, severity: str = "WARNING"
    ):
        """Send risk warning notification."""
        if not self.bot:
            logger.warning("Telegram bot not set, skipping notification")
            return

        emoji_map = {"DANGER": "🔴", "WARNING": "⚠️", "INFO": "ℹ️"}

        emoji = emoji_map.get(severity, "⚠️")

        msg = (
            f"{emoji} *RISK {severity}*\n\n"
            f"{warning_type}\n\n"
            f"{message}\n"
            f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            await self.bot.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send risk warning: {e}")

    async def send_daily_summary(
        self,
        date: str,
        trades: int,
        wins: int,
        losses: int,
        profit: float,
        win_rate: float,
        best_trade: float,
    ):
        """Send daily summary."""
        if not self.bot:
            logger.warning("Telegram bot not set, skipping notification")
            return

        status_emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪"

        msg = (
            f"📊 *DAILY TRADING SUMMARY*\n"
            f"Date: {date}\n\n"
            f"⚡ QUICK STATS\n"
            f"Trades: {trades} ({wins}W/{losses}L)\n"
            f"Win Rate: {win_rate:.1f}%\n"
            f"Profit: ${profit:+,.2f} {status_emoji}\n"
            f"Best Trade: ${best_trade:+,.2f}\n\n"
            f"Status: {'EXCELLENT DAY!' if profit > 100 else 'GOOD DAY!' if profit > 0 else 'REVIEW NEEDED'} {status_emoji}"
        )

        try:
            await self.bot.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")


# Global instance
_notifier: TradeNotifier | None = None


def get_trade_notifier() -> TradeNotifier:
    """Get global trade notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = TradeNotifier()
    return _notifier
