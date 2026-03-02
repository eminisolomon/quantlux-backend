"""AI-powered trade performance insights using Gemini."""

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import TRADE_JOURNAL_PROMPT, TRADE_JOURNAL_SYSTEM
from app.analytics.tracker import PerformanceTracker
from app.core.decorators import fallback_on_failure, require_feature
from app.models import Trade


def _format_recent_trades(trades: list[Trade], limit: int = 10) -> str:
    """Format the most recent trades for the prompt."""
    recent = trades[-limit:] if len(trades) > limit else trades
    if not recent:
        return "No recent trades available."

    lines = []
    for t in recent:
        profit_str = f"+${t.profit:.2f}" if t.profit >= 0 else f"-${abs(t.profit):.2f}"
        close_str = t.close_time.strftime("%Y-%m-%d %H:%M") if t.close_time else "N/A"
        lines.append(f"  {t.symbol} {t.type} | {profit_str} | {close_str}")

    return "\n".join(lines)


@require_feature(
    "ENABLE_AI_FEATURES", fallback_return="⚠️ AI features are disabled via settings."
)
@fallback_on_failure(default_return="⚠️ AI analysis error occurred.")
async def generate_performance_report(
    gemini: GeminiClient,
    tracker: PerformanceTracker,
) -> str | None:
    """Generate an AI-powered performance coaching report."""
    if not gemini.is_available:
        return "⚠️ AI features unavailable — GEMINI_API_KEY not configured."

    if not tracker.trades:
        return "📊 No trade history available for analysis yet."

    # Gather stats
    stats = tracker.get_stats()
    if not stats:
        return "📊 Insufficient data for AI analysis."

    sharpe = tracker.calculate_sharpe_ratio()
    sortino = tracker.calculate_sortino_ratio()
    max_dd = tracker.calculate_max_drawdown()
    profit_factor = tracker.calculate_profit_factor()
    current_dd = tracker.get_current_drawdown()
    current_dd = tracker.get_current_drawdown()

    recent_trades_text = _format_recent_trades(tracker.trades)

    prompt = TRADE_JOURNAL_PROMPT.format(
        total_trades=stats.total_trades,
        win_rate=stats.win_rate,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown=max_dd.max_dd_pct,
        avg_win=stats.avg_win,
        avg_loss=stats.avg_loss,
        largest_win=stats.largest_win,
        largest_loss=stats.largest_loss,
        current_drawdown=current_dd,
        recent_trades=recent_trades_text,
    )

    result = await gemini.generate(
        prompt=prompt,
        system_instruction=TRADE_JOURNAL_SYSTEM,
    )

    if result:
        return f"🤖 *AI Performance Coach*\n\n{result}"
    return "⚠️ AI analysis returned empty — please try again later."
