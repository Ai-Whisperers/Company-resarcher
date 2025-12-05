"""
Cached AI Client - Wrapper to reduce API costs and improve response times.

Supports two caching modes:
1. Exact match caching (default) - Uses hash-based cache
2. Semantic caching (optional) - Uses fuzzy text matching for similar prompts

Semantic caching is especially effective for:
- Low-temperature (deterministic) prompts
- Research queries with slight variations
- Repeated similar questions
"""

import os
from typing import Optional

from src.infrastructure.ai import BaseAIClient
from src.infrastructure.cache import get_ai_cache
from src.infrastructure.logging import setup_logger

logger = setup_logger("cached_ai_client")

# Enable semantic caching via environment variable
ENABLE_SEMANTIC_CACHE = os.getenv("ENABLE_SEMANTIC_CACHE", "true").lower() == "true"
SEMANTIC_CACHE_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.85"))


class CachedAIClient(BaseAIClient):
    """
    Wrapper around any BaseAIClient that adds caching.
    Dramatically reduces API costs for repeated queries.

    Features:
    - Exact match caching for all requests
    - Optional semantic caching for similar prompts (when temperature < 0.3)
    - Cost savings tracking
    - Hit rate statistics
    """

    def __init__(
        self,
        client: BaseAIClient,
        enable_cache: bool = True,
        enable_semantic_cache: bool = ENABLE_SEMANTIC_CACHE,
    ):
        """
        Args:
            client: The underlying AI client to wrap
            enable_cache: Whether to use caching (useful for testing)
            enable_semantic_cache: Whether to use semantic similarity matching
        """
        self.client = client
        self.enable_cache = enable_cache
        self.enable_semantic_cache = enable_semantic_cache
        self.cache = get_ai_cache() if enable_cache else None
        self.hits = 0
        self.misses = 0
        self.semantic_hits = 0

        # Lazy-load semantic cache
        self._semantic_cache = None

    @property
    def semantic_cache(self):
        """Lazy-load semantic cache to avoid import overhead if not used."""
        if self._semantic_cache is None and self.enable_semantic_cache:
            try:
                from src.services.ai.semantic_cache import SemanticCache
                self._semantic_cache = SemanticCache(
                    similarity_threshold=SEMANTIC_CACHE_THRESHOLD
                )
                logger.debug("Semantic cache initialized")
            except Exception as e:
                logger.debug(f"Semantic cache not available: {e}")
                self.enable_semantic_cache = False
        return self._semantic_cache

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

        Uses exact match cache first, then semantic cache for low-temperature
        prompts if enabled.
        """
        if not self.enable_cache:
            return await self.client.generate(
                prompt, system, temperature, max_tokens, response_format
            )

        # 1. Check exact match cache first (fast)
        cached_response = self.cache.get(prompt, system, temperature, max_tokens)
        if cached_response:
            self.hits += 1
            logger.debug("Cache HIT (exact)")
            return cached_response

        # 2. Check semantic cache for low-temperature prompts
        # Only use semantic matching for deterministic prompts (temp < 0.3)
        if self.enable_semantic_cache and temperature < 0.3 and self.semantic_cache:
            try:
                semantic_hit = self.semantic_cache.get_semantic(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if semantic_hit:
                    self.semantic_hits += 1
                    self.hits += 1
                    logger.debug(
                        f"Cache HIT (semantic, similarity={semantic_hit.similarity:.2f})"
                    )
                    return semantic_hit.response
            except Exception as e:
                logger.debug(f"Semantic cache lookup failed: {e}")

        self.misses += 1
        logger.debug("Cache MISS")

        # Generate new response
        response = await self.client.generate(
            prompt, system, temperature, max_tokens, response_format
        )

        # Store in exact match cache
        self.cache.set(prompt, response, system, temperature, max_tokens)

        # Store in semantic cache for low-temperature prompts
        if self.enable_semantic_cache and temperature < 0.3 and self.semantic_cache:
            try:
                self.semantic_cache.set(
                    prompt=prompt,
                    response=response,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.debug(f"Semantic cache store failed: {e}")

        return response

    def get_provider_name(self) -> str:
        """Pass through to underlying client."""
        return f"Cached<{self.client.get_provider_name()}>"

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        exact_hits = self.hits - self.semantic_hits

        stats = {
            "hits": self.hits,
            "exact_hits": exact_hits,
            "semantic_hits": self.semantic_hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "semantic_cache_enabled": self.enable_semantic_cache,
            "estimated_savings_percent": round(hit_rate, 2),
        }

        # Add semantic cache detailed stats if available
        if self._semantic_cache:
            try:
                semantic_stats = self._semantic_cache.get_stats()
                stats["semantic_cache_stats"] = semantic_stats.to_dict()
            except Exception:
                pass

        return stats

    def reset_stats(self):
        """Reset cache statistics."""
        self.hits = 0
        self.misses = 0
        self.semantic_hits = 0
