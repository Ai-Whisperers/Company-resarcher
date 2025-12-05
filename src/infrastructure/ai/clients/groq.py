"""
Groq Client implementation.
"""

import logging
from typing import Optional

from src.infrastructure.ai.base import BaseAIClient
from src.core.exceptions import AIProviderError, AIRateLimitError

logger = logging.getLogger(__name__)


class GroqClient(BaseAIClient):
    """
    Groq API client.

    Supports Llama, Mixtral, and other models running on Groq's LPU.
    Very fast inference but limited rate limits.
    """

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key
            model: Model to use (default: llama-3.1-8b-instant)
        """
        from groq import AsyncGroq

        self.client = AsyncGroq(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Groq client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """Generate response using Groq API."""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            # Check for rate limit errors
            error_str = str(e).lower()
            if any(
                p in error_str
                for p in [
                    "rate limit",
                    "ratelimit",
                    "429",
                    "quota",
                    "too many requests",
                ]
            ):
                raise AIRateLimitError("groq") from e
            raise AIProviderError(str(e), "groq") from e

    def get_provider_name(self) -> str:
        return "groq"
