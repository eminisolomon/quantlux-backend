"""Async Gemini AI client for QuantLux."""

import json

from google import genai
from google.genai import types

from app.core.decorators import fallback_on_failure, retry_on_error
from app.core.settings import settings
from app.utils.logger import logger


class GeminiClient:
    """Wrapper around the Google GenAI SDK for QuantLux AI features."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialise the Gemini client."""
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set — AI features will be unavailable.")
            self._client = None
            return

        self._client = genai.Client(api_key=self.api_key)
        logger.info(f"GeminiClient initialised with model: {self.model}")

    @property
    def is_available(self) -> bool:
        """Check if the Gemini client is configured and ready."""
        return self._client is not None

    @fallback_on_failure(default_return=None)
    @retry_on_error(max_retries=3, backoff_factor=2)
    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
    ) -> str | None:
        """Generate a text completion from Gemini."""
        if not self.is_available:
            logger.warning("Gemini client unavailable — skipping generation.")
            return None

        target_model = model or self.model

        config = types.GenerateContentConfig(
            system_instruction=system_instruction if system_instruction else None,
            temperature=0.7,
            max_output_tokens=2048,
        )

        response = await self._client.aio.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config,
        )

        if response and response.text:
            return response.text.strip()

        logger.warning("Gemini returned empty response.")
        return None

    @fallback_on_failure(default_return=None)
    @retry_on_error(max_retries=3, backoff_factor=2)
    async def generate_json(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
    ) -> dict | None:
        """Generate a structured JSON response from Gemini."""
        if not self.is_available:
            logger.warning("Gemini client unavailable — skipping JSON generation.")
            return None

        target_model = model or self.model

        config = types.GenerateContentConfig(
            system_instruction=system_instruction if system_instruction else None,
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=2048,
        )

        response = await self._client.aio.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config,
        )

        if response and response.text:
            try:
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                return None

        logger.warning("Gemini returned empty JSON response.")
        return None
