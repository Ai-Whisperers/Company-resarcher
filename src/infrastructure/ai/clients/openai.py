"""
OpenAI Client implementation.
"""

import logging
from typing import Optional

from openai import (
    AsyncOpenAI,
    APIError as OpenAIAPIError,
    RateLimitError as OpenAIRateLimitError,
)

from src.infrastructure.ai.base import BaseAIClient
from src.core.exceptions import AIProviderError, AIRateLimitError

logger = logging.getLogger(__name__)


class OpenAIClient(BaseAIClient):
    """
    OpenAI API client.

    Supports GPT-4, GPT-4-turbo, GPT-3.5-turbo, and other OpenAI models.
    """

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4-turbo-preview)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized OpenAI client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """Generate response using OpenAI API."""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except OpenAIRateLimitError as e:
            raise AIRateLimitError("openai") from e
        except OpenAIAPIError as e:
            raise AIProviderError(str(e), "openai") from e
        except Exception as e:
            raise AIProviderError(str(e), "openai") from e

    def get_provider_name(self) -> str:
        return "openai"
