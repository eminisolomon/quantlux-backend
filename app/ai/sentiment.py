"""AI-powered news sentiment analysis using Gemini."""

from dataclasses import dataclass, field

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import NEWS_SENTIMENT_PROMPT, NEWS_SENTIMENT_SYSTEM
from app.utils.logger import logger


@dataclass
class CurrencySentiment:
    """Sentiment score for a single currency."""

    currency: str
    score: float  # -1.0 (bearish) to 1.0 (bullish)
    reasoning: str = ""


@dataclass
class SentimentResult:
    """Result of news sentiment analysis."""

    sentiments: dict[str, CurrencySentiment] = field(default_factory=dict)
    overall_risk: str = "LOW"
    recommendation: str = ""
    raw_events: list[str] = field(default_factory=list)

    def get_pair_sentiment(self, symbol: str) -> float | None:
        """
        Get net sentiment for a currency pair (e.g. EURUSD).

        Returns positive if base is bullish vs quote, negative if bearish.
        """
        if len(symbol) < 6:
            return None

        base = symbol[:3].upper()
        quote = symbol[3:6].upper()

        base_score = self.sentiments.get(base, CurrencySentiment(base, 0.0)).score
        quote_score = self.sentiments.get(quote, CurrencySentiment(quote, 0.0)).score

        return base_score - quote_score

    def is_high_risk(self) -> bool:
        """Check if overall market risk is high."""
        return self.overall_risk.upper() in ("HIGH", "CRITICAL")


async def analyze_sentiment(
    gemini: GeminiClient,
    events: list[str],
) -> SentimentResult | None:
    """Analyse news events and return sentiment scores per currency."""
    if not gemini.is_available:
        return None

    if not events:
        return SentimentResult(
            overall_risk="LOW", recommendation="No events — normal trading."
        )

    events_text = "\n".join(f"- {e}" for e in events)
    prompt = NEWS_SENTIMENT_PROMPT.format(events=events_text)

    try:
        result = await gemini.generate_json(
            prompt=prompt,
            system_instruction=NEWS_SENTIMENT_SYSTEM,
        )

        if not result:
            return None

        sentiments = {}
        for currency, data in result.get("sentiments", {}).items():
            sentiments[currency.upper()] = CurrencySentiment(
                currency=currency.upper(),
                score=float(data.get("score", 0.0)),
                reasoning=data.get("reasoning", ""),
            )

        return SentimentResult(
            sentiments=sentiments,
            overall_risk=result.get("overall_risk", "LOW"),
            recommendation=result.get("recommendation", ""),
            raw_events=events,
        )

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return None
