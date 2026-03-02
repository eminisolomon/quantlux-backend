"""Unit tests for AI adapter layer."""

from unittest.mock import patch

import pytest

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import (
    CHAT_CONTEXT_PROMPT,
    MARKET_ANALYSIS_PROMPT,
    RISK_GUARD_PROMPT,
    TRADE_JOURNAL_PROMPT,
)
from app.ai.sentiment import (
    CurrencySentiment,
    SentimentResult,
)
from app.risk.ai_guard import AIGuardResult, evaluate_trade


class TestGeminiClientInit:
    """Tests for GeminiClient initialization."""

    @patch("app.ai.gemini_client.settings")
    def test_init_without_api_key(self, mock_settings):
        """Client should be unavailable when no API key is set."""
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"

        client = GeminiClient(api_key=None, model=None)
        assert not client.is_available

    @patch("app.ai.gemini_client.genai")
    @patch("app.ai.gemini_client.settings")
    def test_init_with_api_key(self, mock_settings, mock_genai):
        """Client should be available when API key is set."""
        mock_settings.GEMINI_API_KEY = "test-key-123"
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"

        client = GeminiClient(api_key="test-key-123")
        assert client.is_available
        assert client.model == "gemini-2.0-flash"

    @patch("app.ai.gemini_client.settings")
    def test_custom_model(self, mock_settings):
        """Client should accept a custom model."""
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"

        client = GeminiClient(model="gemini-2.0-pro")
        assert client.model == "gemini-2.0-pro"


class TestGeminiClientGenerate:
    """Tests for GeminiClient.generate()."""

    @pytest.mark.asyncio
    @patch("app.ai.gemini_client.settings")
    async def test_generate_when_unavailable(self, mock_settings):
        """Generate should return None when client is unavailable."""
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"

        client = GeminiClient(api_key=None)
        result = await client.generate("test prompt")
        assert result is None

    @pytest.mark.asyncio
    @patch("app.ai.gemini_client.settings")
    async def test_generate_json_when_unavailable(self, mock_settings):
        """Generate JSON should return None when client is unavailable."""
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"

        client = GeminiClient(api_key=None)
        result = await client.generate_json("test prompt")
        assert result is None


class TestPromptTemplates:
    """Tests for prompt template formatting."""

    def test_market_analysis_prompt_formatting(self):
        """Market analysis prompt should format without errors."""
        result = MARKET_ANALYSIS_PROMPT.format(
            symbol="EURUSD",
            timeframe="H1",
            candle_count=30,
            candles="O:1.1 H:1.2 L:1.0 C:1.15",
            rsi="65.3",
            atr="0.00123",
            price="1.15000",
        )
        assert "EURUSD" in result
        assert "H1" in result

    def test_trade_journal_prompt_formatting(self):
        """Trade journal prompt should format without errors."""
        result = TRADE_JOURNAL_PROMPT.format(
            total_trades=100,
            win_rate=65.0,
            profit_factor=1.8,
            sharpe_ratio=1.5,
            sortino_ratio=2.1,
            max_drawdown=12.5,
            avg_win=150.0,
            avg_loss=80.0,
            largest_win=500.0,
            largest_loss=200.0,
            current_drawdown=3.2,
            recent_trades="EURUSD BUY +$50",
        )
        assert "100" in result
        assert "65.0" in result

    def test_risk_guard_prompt_formatting(self):
        """Risk guard prompt should format without errors."""
        result = RISK_GUARD_PROMPT.format(
            symbol="EURUSD",
            action="BUY",
            volume=0.1,
            balance=10000.0,
            equity=9800.0,
            drawdown=2.0,
            daily_dd=1.5,
            open_positions=2,
            correlated_pairs="GBPUSD",
            news_risk="LOW",
            time="2025-01-01 12:00 UTC",
        )
        assert "EURUSD" in result
        assert "BUY" in result

    def test_chat_context_prompt_formatting(self):
        """Chat context prompt should format without errors."""
        result = CHAT_CONTEXT_PROMPT.format(
            balance=10000.0,
            equity=9800.0,
            positions="EURUSD: $50",
            strategies="RSI",
            news_status="Active",
            user_message="How is my trade?",
        )
        assert "How is my trade?" in result


class TestSentimentResult:
    """Tests for SentimentResult data class."""

    def test_get_pair_sentiment(self):
        """Should calculate net sentiment for a currency pair."""
        result = SentimentResult(
            sentiments={
                "EUR": CurrencySentiment("EUR", 0.5, "Strong economy"),
                "USD": CurrencySentiment("USD", -0.3, "Rate concerns"),
            }
        )
        net = result.get_pair_sentiment("EURUSD")
        assert net == pytest.approx(0.8)

    def test_get_pair_sentiment_missing(self):
        """Should return 0 for missing currencies."""
        result = SentimentResult()
        net = result.get_pair_sentiment("EURUSD")
        assert net == 0.0

    def test_is_high_risk(self):
        """Should correctly identify high risk."""
        result = SentimentResult(overall_risk="HIGH")
        assert result.is_high_risk()

        result_low = SentimentResult(overall_risk="LOW")
        assert not result_low.is_high_risk()


class TestAIGuardFailOpen:
    """Tests for AI Risk Guard fail-open behavior."""

    @pytest.mark.asyncio
    @patch("app.core.settings.settings")
    @patch("app.ai.gemini_client.settings")
    async def test_fail_open_when_unavailable(
        self, mock_gemini_settings, mock_features_settings
    ):
        """Should approve trade when Gemini is unavailable."""
        mock_gemini_settings.GEMINI_API_KEY = None
        mock_gemini_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_features_settings.ENABLE_AI_RISK_GUARD = True

        client = GeminiClient(api_key=None)
        result = await evaluate_trade(
            gemini=client,
            symbol="EURUSD",
            action="BUY",
            volume=0.1,
            balance=10000,
            equity=9800,
            drawdown_pct=2.0,
            daily_dd_pct=1.0,
            open_positions=1,
        )
        assert result.approved is True
        assert "unavailable" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_ai_guard_result_defaults(self):
        """AIGuardResult defaults should be safe (approved)."""
        result = AIGuardResult()
        assert result.approved is True
        assert result.risk_level == "LOW"
        assert result.suggestions == []
