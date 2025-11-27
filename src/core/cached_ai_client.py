"""
Cached AI Client - Wrapper to reduce API costs and improve response times.
"""

import hashlib
import json
from typing import Optional
from .ai_client import BaseAIClient
from .cache import get_ai_cache
from .logger import setup_logger

logger = setup_logger("cached_ai_client")


class CachedAIClient(BaseAIClient):
    """
    Wrapper around any BaseAIClient that adds caching.
    Dramatically reduces API costs for repeated queries.
    """

    def __init__(self, client: BaseAIClient, enable_cache: bool = True):
        """
        Args:
            client: The underlying AI client to wrap
            enable_cache: Whether to use caching (useful for testing)
        """
        self.client = client
        self.enable_cache = enable_cache
        self.cache = get_ai_cache() if enable_cache else None
        self.hits = 0
        self.misses = 0

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """
        Generate response with caching.
        Cache key includes all parameters to ensure correctness.
        """
        if not self.enable_cache:
            return await self.client.generate(
                prompt, system, temperature, max_tokens, response_format
            )

        # Check cache
        cached_response = self.cache.get(prompt, system, temperature, max_tokens)
        if cached_response:
            self.hits += 1
            logger.info("Cache HIT")
            return cached_response

        self.misses += 1
        logger.info("Cache MISS")

        # Generate
        response = await self.client.generate(
            prompt, system, temperature, max_tokens, response_format
        )

        # Store in cache
        self.cache.set(prompt, response, system, temperature, max_tokens)

        return response

    def get_provider_name(self) -> str:
        """Pass through to underlying client."""
        return f"Cached<{self.client.get_provider_name()}>"

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "estimated_savings_percent": round(hit_rate, 2),  # 1:1 for now
        }

    def reset_stats(self):
        """Reset cache statistics."""
        self.hits = 0
        self.misses = 0
