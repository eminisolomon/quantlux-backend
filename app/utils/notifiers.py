"""Trade notification system using standard logging."""

from datetime import datetime

from app.core.enums import SignalAction
from app.utils.logger import logger


class TradeNotifier:
    """Log trade notifications via the standard logger."""

    def __init__(self):
        """Initialize notifier."""
        pass

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
        """Log when trade opens."""
        type_label = "BUY" if trade_type == SignalAction.BUY else "SELL"

        risk_reward = "N/A"
        if stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            if risk > 0:
                risk_reward = f"1:{reward / risk:.1f}"

        msg = (
            f"NEW POSITION OPENED | {type_label} {symbol} | "
            f"Vol: {volume} | Entry: {entry_price:.5f} | "
            f"SL: {stop_loss} | TP: {take_profit} | "
            f"Strategy: {strategy} | R:R: {risk_reward}"
        )
        if confidence:
            msg += f" | Confidence: {confidence:.0f}%"

        logger.info(msg)

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
        """Log when trade closes."""
        type_label = "BUY" if trade_type == SignalAction.BUY else "SELL"

        logger.info(
            f"POSITION CLOSED | {type_label} {symbol} | "
            f"Entry: {entry_price:.5f} -> Exit: {exit_price:.5f} | "
            f"Vol: {volume} | Pips: {pips:+.1f} | P&L: ${profit:+,.2f} | "
            f"Result: {result} | Duration: {duration}"
        )

    async def notify_milestone(
        self,
        milestone_type: str,
        message: str,
        current_value: float | None = None,
        target_value: float | None = None,
    ):
        """Log milestone notification."""
        msg = f"MILESTONE: {milestone_type} | {message}"
        if target_value and current_value:
            msg += f" | Target: ${target_value:,.2f} | Actual: ${current_value:,.2f}"
        logger.info(msg)

    async def notify_risk_warning(
        self, warning_type: str, message: str, severity: str = "WARNING"
    ):
        """Log risk warning notification."""
        log_msg = f"RISK {severity}: {warning_type} | {message}"
        if severity == "DANGER":
            logger.error(log_msg)
        else:
            logger.warning(log_msg)

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
        """Log daily summary."""
        logger.info(
            f"DAILY SUMMARY | Date: {date} | "
            f"Trades: {trades} ({wins}W/{losses}L) | "
            f"Win Rate: {win_rate:.1f}% | "
            f"Profit: ${profit:+,.2f} | "
            f"Best Trade: ${best_trade:+,.2f}"
        )


# Global instance
_notifier: TradeNotifier | None = None


def get_trade_notifier() -> TradeNotifier:
    """Get global trade notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = TradeNotifier()
    return _notifier
