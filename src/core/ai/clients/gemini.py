"""
Google Gemini Client implementation.
"""

import logging
from typing import Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from ..base import BaseAIClient
from ...exceptions import AIProviderError, AIRateLimitError

logger = logging.getLogger(__name__)


class GeminiClient(BaseAIClient):
    """
    Google Gemini API client.

    Supports Gemini Pro, Gemini 1.5 Pro, and other Gemini models.
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro-latest"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key
            model: Model to use (default: gemini-1.5-pro-latest)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self._model_name = model
        logger.info(f"Initialized Gemini client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """Generate response using Gemini API."""
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type=(
                    "application/json" if response_format == "json" else "text/plain"
                ),
            )
            full_prompt = f"System: {system}\n\nUser: {prompt}" if system else prompt
            response = await self.model.generate_content_async(
                full_prompt, generation_config=generation_config
            )
            return response.text

        except google_exceptions.ResourceExhausted as e:
            raise AIRateLimitError("gemini") from e
        except Exception as e:
            # Check for rate limit errors in message
            error_str = str(e).lower()
            if any(
                p in error_str
                for p in [
                    "rate limit",
                    "ratelimit",
                    "429",
                    "quota",
                    "resource exhausted",
                ]
            ):
                raise AIRateLimitError("gemini") from e
            raise AIProviderError(str(e), "gemini") from e

    def get_provider_name(self) -> str:
        return "gemini"
