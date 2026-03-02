"""AI-powered pre-trade risk evaluation using Gemini."""

from dataclasses import dataclass, field
from datetime import datetime

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import RISK_GUARD_PROMPT, RISK_GUARD_SYSTEM
from app.core import messages as msg
from app.core.decorators import fallback_on_failure, require_feature
from app.utils.logger import logger


@dataclass
class AIGuardResult:
    """Result of AI risk evaluation."""

    approved: bool = True
    reasoning: str = ""
    risk_level: str = "LOW"
    suggestions: list[str] = field(default_factory=list)


@require_feature(
    "ENABLE_AI_RISK_GUARD",
    fallback_return=AIGuardResult(approved=True, reasoning=msg.AI_GUARD_DISABLED),
)
@fallback_on_failure(
    default_return=AIGuardResult(approved=True, reasoning=msg.AI_GUARD_FAIL_OPEN)
)
async def evaluate_trade(
    gemini: GeminiClient,
    symbol: str,
    action: str,
    volume: float,
    balance: float,
    equity: float,
    drawdown_pct: float,
    daily_dd_pct: float,
    open_positions: int,
    correlated_pairs: str = "None",
    news_risk: str = "LOW",
) -> AIGuardResult:
    """Evaluate a proposed trade using Gemini AI (fail-open on error)."""
    # Fail-open if AI is unavailable
    if not gemini.is_available:
        return AIGuardResult(approved=True, reasoning=msg.AI_GUARD_UNAVAILABLE)

    prompt = RISK_GUARD_PROMPT.format(
        symbol=symbol,
        action=action,
        volume=volume,
        balance=balance,
        equity=equity,
        drawdown=drawdown_pct,
        daily_dd=daily_dd_pct,
        open_positions=open_positions,
        correlated_pairs=correlated_pairs,
        news_risk=news_risk,
        time=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )

    result = await gemini.generate_json(
        prompt=prompt,
        system_instruction=RISK_GUARD_SYSTEM,
    )

    if not result:
        logger.warning(msg.AI_GUARD_EMPTY)
        return AIGuardResult(approved=True, reasoning=msg.AI_GUARD_EMPTY)

    guard_result = AIGuardResult(
        approved=result.get("approved", True),
        reasoning=result.get("reasoning", ""),
        risk_level=result.get("risk_level", "LOW"),
        suggestions=result.get("suggestions", []),
    )

    if not guard_result.approved:
        logger.warning(
            msg.AI_GUARD_BLOCKED.format(
                action=action, symbol=symbol, reason=guard_result.reasoning
            )
        )
    else:
        logger.info(
            msg.AI_GUARD_APPROVED.format(
                action=action, symbol=symbol, level=guard_result.risk_level
            )
        )

    return guard_result
