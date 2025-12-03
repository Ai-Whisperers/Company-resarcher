"""
Anthropic Claude Client implementation.
"""

import logging
from typing import Optional

from anthropic import (
    AsyncAnthropic,
    APIError,
    RateLimitError as AnthropicRateLimitError,
)

from ..base import BaseAIClient
from ...exceptions import AIProviderError, AIRateLimitError

logger = logging.getLogger(__name__)


class AnthropicClient(BaseAIClient):
    """
    Anthropic Claude API client.

    Supports Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-sonnet-4-20250514)
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Anthropic client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """Generate response using Anthropic API."""
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            response = await self.client.messages.create(**kwargs)
            return response.content[0].text

        except AnthropicRateLimitError as e:
            raise AIRateLimitError("anthropic") from e
        except APIError as e:
            raise AIProviderError(str(e), "anthropic") from e
        except Exception as e:
            raise AIProviderError(str(e), "anthropic") from e

    def get_provider_name(self) -> str:
        return "anthropic"
