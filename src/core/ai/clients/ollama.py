"""
Ollama Client implementation.
"""

import asyncio
import logging
from typing import Optional

from ..base import BaseAIClient
from ...exceptions import AIProviderError

logger = logging.getLogger(__name__)


class OllamaClient(BaseAIClient):
    """
    Ollama client for local LLM inference.

    Uses the async API for better performance with fallback to sync.
    No API key required - runs locally.
    """

    def __init__(self, model: str = "llama3.1:8b"):
        """
        Initialize Ollama client.

        Args:
            model: Model to use (default: llama3.1:8b)
        """
        self.model = model
        self._async_client = None
        self._sync_client = None

        # Try to use async client for better performance
        try:
            from ollama import AsyncClient

            self._async_client = AsyncClient()
            logger.info(f"Initialized Ollama async client with model: {model}")
        except ImportError:
            # Fall back to sync client
            import ollama

            self._sync_client = ollama
            logger.warning(
                f"Ollama AsyncClient not available, using sync client with model: {model}"
            )

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """Generate response using Ollama."""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            options = {"temperature": temperature, "num_predict": max_tokens}

            if self._async_client:
                # Use native async client for better performance
                response = await self._async_client.chat(
                    model=self.model,
                    messages=messages,
                    options=options,
                )
            else:
                # Fall back to sync client in thread pool
                response = await asyncio.to_thread(
                    self._sync_client.chat,
                    model=self.model,
                    messages=messages,
                    options=options,
                )

            return response["message"]["content"]

        except Exception as e:
            raise AIProviderError(str(e), "ollama") from e

    def get_provider_name(self) -> str:
        return "ollama"
