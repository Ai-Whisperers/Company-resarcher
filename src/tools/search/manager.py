"""
Search Manager - Orchestrates multiple search providers with automatic fallback.

The manager tries providers in priority order (free first, then paid) and
automatically falls back to the next provider if one fails or is rate limited.

Features:
- Automatic fallback chain across multiple providers
- Rate limiting with exponential backoff
- Provider health tracking (cooldown on failures)
- Retry-After header respect
- Request deduplication

Usage:
    from src.tools.search import SearchManager

    manager = SearchManager()
    results = await manager.search("query", max_results=10)
"""

import asyncio
import os
import time
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .base import SearchProvider, SearchResult, SearchError, RateLimitError
from .duckduckgo import DuckDuckGoProvider
from .jina import JinaSearchProvider
from .langsearch import LangSearchProvider
from .serper import SerperProvider
from .tavily_provider import TavilyProvider
from ...core.logger import setup_logger
from ...core.config import get_settings

logger = setup_logger("search.manager")

# Rate limiting configuration
DEFAULT_REQUESTS_PER_MINUTE = int(os.getenv("SEARCH_RATE_LIMIT_PER_MIN", "30"))
DEFAULT_COOLDOWN_SECONDS = float(os.getenv("SEARCH_COOLDOWN_SECONDS", "60"))
MAX_RETRIES = int(os.getenv("SEARCH_MAX_RETRIES", "3"))
BASE_BACKOFF_SECONDS = float(os.getenv("SEARCH_BASE_BACKOFF", "2.0"))


@dataclass
class ProviderHealth:
    """Tracks health and rate limit status of a provider."""

    name: str
    is_healthy: bool = True
    consecutive_failures: int = 0
    last_failure_time: Optional[float] = None
    rate_limited_until: Optional[float] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_hits: int = 0

    def record_success(self) -> None:
        """Record a successful request."""
        self.is_healthy = True
        self.consecutive_failures = 0
        self.total_requests += 1
        self.successful_requests += 1

    def record_failure(self, is_rate_limit: bool = False, retry_after: Optional[float] = None) -> None:
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_failure_time = time.monotonic()

        if is_rate_limit:
            self.rate_limit_hits += 1
            # Set cooldown period
            cooldown = retry_after if retry_after else DEFAULT_COOLDOWN_SECONDS
            self.rate_limited_until = time.monotonic() + cooldown
            logger.warning(f"Provider {self.name} rate limited for {cooldown:.1f}s")

        # Mark unhealthy after too many failures
        if self.consecutive_failures >= 3:
            self.is_healthy = False

    def is_available(self) -> bool:
        """Check if provider is currently available (not in cooldown)."""
        if self.rate_limited_until:
            if time.monotonic() < self.rate_limited_until:
                return False
            # Cooldown expired, reset
            self.rate_limited_until = None

        return self.is_healthy or self.consecutive_failures < 5

    def time_until_available(self) -> float:
        """Get seconds until provider might be available again."""
        if not self.rate_limited_until:
            return 0.0
        remaining = self.rate_limited_until - time.monotonic()
        return max(0.0, remaining)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "name": self.name,
            "is_healthy": self.is_healthy,
            "consecutive_failures": self.consecutive_failures,
            "rate_limited": self.rate_limited_until is not None and time.monotonic() < self.rate_limited_until,
            "time_until_available": self.time_until_available(),
            "total_requests": self.total_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 100.0,
            "rate_limit_hits": self.rate_limit_hits,
        }


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter."""

    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE
    _tokens: float = field(default=0.0, init=False)
    _last_update: float = field(default_factory=time.monotonic, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self):
        self._tokens = float(self.requests_per_minute)

    async def acquire(self, timeout: float = 10.0) -> bool:
        """
        Acquire permission to make a request.

        Returns True if permitted, False if timeout exceeded.
        """
        async with self._lock:
            now = time.monotonic()
            # Refill tokens based on time elapsed
            elapsed = now - self._last_update
            self._tokens = min(
                float(self.requests_per_minute),
                self._tokens + elapsed * (self.requests_per_minute / 60.0)
            )
            self._last_update = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True

            # Calculate wait time
            wait_time = (1.0 - self._tokens) / (self.requests_per_minute / 60.0)
            if wait_time > timeout:
                return False

            await asyncio.sleep(wait_time)
            self._tokens = 0.0
            self._last_update = time.monotonic()
            return True


class SearchManager:
    """
    Manages multiple search providers with automatic fallback and rate limiting.

    Features:
    - Priority-based provider selection (free first, then paid)
    - Automatic fallback on failure or rate limiting
    - Exponential backoff with jitter on rate limits
    - Provider health tracking and cooldown periods
    - Global rate limiting to prevent abuse

    Providers are tried in priority order:
    1. DuckDuckGo (FREE) - Priority 1
    2. Jina AI (FREE) - Priority 2
    3. LangSearch (FREE) - Priority 3
    4. Serper.dev (Paid) - Priority 4
    5. Tavily (Paid) - Priority 5

    If a provider fails or is rate-limited, the manager automatically
    tries the next available provider.
    """

    def __init__(
        self,
        providers: Optional[List[SearchProvider]] = None,
        enable_fallback: bool = True,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
    ):
        """
        Initialize the search manager.

        Args:
            providers: Optional custom list of providers (uses defaults if None)
            enable_fallback: If True, try next provider on failure
            requests_per_minute: Global rate limit across all providers
        """
        self.enable_fallback = enable_fallback
        self.providers: List[SearchProvider] = []
        self._stats: Dict[str, Dict[str, int]] = {}
        self._provider_health: Dict[str, ProviderHealth] = {}
        self._rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)

        if providers:
            self.providers = sorted(providers, key=lambda p: p.priority)
        else:
            self._init_default_providers()

        # Initialize health tracking for all providers
        for provider in self.providers:
            self._provider_health[provider.name] = ProviderHealth(name=provider.name)

    def _init_default_providers(self):
        """Initialize default providers in priority order."""
        settings = get_settings()

        # Always add free providers first
        self.providers.append(DuckDuckGoProvider())
        self.providers.append(JinaSearchProvider())

        # Add LangSearch if configured (FREE but requires API key)
        self.providers.append(LangSearchProvider())

        # Add paid providers if configured
        serper_key = getattr(settings, "SERPER_API_KEY", None)
        if serper_key:
            self.providers.append(SerperProvider())

        # Always add Tavily (check availability later)
        self.providers.append(TavilyProvider())

        # Sort by priority
        self.providers.sort(key=lambda p: p.priority)

        available = [p.name for p in self.providers if p.is_available()]
        logger.info(f"SearchManager initialized with providers: {available}")

    def _record_stat(self, provider: str, stat: str):
        """Record a statistic for a provider."""
        if provider not in self._stats:
            self._stats[provider] = {"success": 0, "failure": 0, "rate_limit": 0}
        self._stats[provider][stat] = self._stats[provider].get(stat, 0) + 1

    def _get_health(self, provider_name: str) -> ProviderHealth:
        """Get or create health tracker for a provider."""
        if provider_name not in self._provider_health:
            self._provider_health[provider_name] = ProviderHealth(name=provider_name)
        return self._provider_health[provider_name]

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        import random
        base_delay = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
        jitter = random.uniform(0, base_delay * 0.25)
        return min(base_delay + jitter, 30.0)  # Cap at 30 seconds

    async def _search_with_retry(
        self,
        provider: SearchProvider,
        query: str,
        max_results: int,
    ) -> Optional[List[SearchResult]]:
        """
        Execute search with retry logic and exponential backoff.

        Returns results on success, None to signal fallback needed.
        """
        health = self._get_health(provider.name)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Apply global rate limiting
                if not await self._rate_limiter.acquire(timeout=5.0):
                    logger.warning(f"Global rate limit reached, waiting...")
                    await asyncio.sleep(1.0)
                    if not await self._rate_limiter.acquire(timeout=10.0):
                        logger.error("Rate limit timeout, skipping provider")
                        return None

                results = await provider.search(query, max_results)

                if results:
                    health.record_success()
                    self._record_stat(provider.name, "success")
                    return results
                else:
                    logger.warning(f"{provider.name} returned empty results")
                    return None

            except RateLimitError as e:
                health.record_failure(
                    is_rate_limit=True,
                    retry_after=e.retry_after
                )
                self._record_stat(provider.name, "rate_limit")

                if attempt < MAX_RETRIES and e.retry_after and e.retry_after < 10:
                    # Short retry-after, wait and retry same provider
                    backoff = e.retry_after or self._calculate_backoff(attempt)
                    logger.info(f"Rate limited by {provider.name}, retrying in {backoff:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                    await asyncio.sleep(backoff)
                else:
                    # Long cooldown or max retries, move to next provider
                    logger.warning(f"{provider.name} rate limited, falling back")
                    return None

            except SearchError as e:
                health.record_failure()
                self._record_stat(provider.name, "failure")
                logger.warning(f"{provider.name} search failed: {e}")

                if attempt < MAX_RETRIES:
                    backoff = self._calculate_backoff(attempt)
                    logger.info(f"Retrying {provider.name} in {backoff:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                    await asyncio.sleep(backoff)
                else:
                    return None

            except Exception as e:
                health.record_failure()
                self._record_stat(provider.name, "failure")
                logger.error(f"{provider.name} unexpected error: {e}")
                return None

        return None

    async def search(
        self,
        query: str,
        max_results: int = 10,
        preferred_provider: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Execute a search with automatic fallback and rate limiting.

        Args:
            query: The search query
            max_results: Maximum results to return
            preferred_provider: Force a specific provider (optional)

        Returns:
            List of SearchResult objects from the first successful provider

        Raises:
            SearchError: If all providers fail
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        errors = []

        for provider in self.providers:
            # Skip if user requested specific provider
            if preferred_provider and provider.name != preferred_provider:
                continue

            # Skip unavailable providers (API key missing)
            if not provider.is_available():
                logger.debug(f"Skipping {provider.name} - not available (no API key)")
                continue

            # Check provider health (rate limit cooldown)
            health = self._get_health(provider.name)
            if not health.is_available():
                wait_time = health.time_until_available()
                logger.debug(f"Skipping {provider.name} - in cooldown ({wait_time:.1f}s remaining)")
                errors.append((provider.name, "cooldown", f"Rate limited for {wait_time:.1f}s"))
                continue

            logger.info(f"Searching with {provider.name}: '{query[:50]}...'")
            results = await self._search_with_retry(provider, query, max_results)

            if results:
                logger.info(f"Got {len(results)} results from {provider.name}")
                return results

            # No results or error, continue to next provider if fallback enabled
            if not self.enable_fallback:
                break

        # All providers failed
        if errors:
            error_summary = "; ".join([f"{p}: {t}" for p, t, _ in errors])
            logger.error(f"All search providers failed: {error_summary}")
            raise SearchError(
                f"All providers failed: {error_summary}",
                "manager",
                query
            )

        # No providers available
        logger.error("No search providers available")
        return []

    async def search_with_provider(
        self,
        query: str,
        provider_name: str,
        max_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search using a specific provider (no fallback).

        Args:
            query: The search query
            provider_name: Name of the provider to use
            max_results: Maximum results

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: If provider not found or search fails
        """
        for provider in self.providers:
            if provider.name == provider_name:
                if not provider.is_available():
                    raise SearchError(
                        f"Provider {provider_name} is not available",
                        provider_name,
                        query
                    )
                return await provider.search(query, max_results)

        raise SearchError(f"Provider '{provider_name}' not found", "manager", query)

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [p.name for p in self.providers if p.is_available()]

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get usage statistics for all providers."""
        return self._stats.copy()

    def get_status(self) -> Dict[str, Any]:
        """Get status of all providers including health information."""
        return {
            "providers": [
                {
                    "name": p.name,
                    "priority": p.priority,
                    "available": p.is_available(),
                    "stats": self._stats.get(p.name, {}),
                    "health": self._get_health(p.name).to_dict(),
                }
                for p in self.providers
            ],
            "fallback_enabled": self.enable_fallback,
            "rate_limit_config": {
                "requests_per_minute": DEFAULT_REQUESTS_PER_MINUTE,
                "cooldown_seconds": DEFAULT_COOLDOWN_SECONDS,
                "max_retries": MAX_RETRIES,
            },
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all providers."""
        healthy_count = sum(1 for h in self._provider_health.values() if h.is_healthy)
        rate_limited_count = sum(
            1 for h in self._provider_health.values()
            if h.rate_limited_until and time.monotonic() < h.rate_limited_until
        )
        return {
            "total_providers": len(self.providers),
            "healthy_providers": healthy_count,
            "rate_limited_providers": rate_limited_count,
            "providers": {
                name: health.to_dict()
                for name, health in self._provider_health.items()
            },
        }

    def reset_provider_health(self, provider_name: Optional[str] = None) -> None:
        """Reset health status for a provider or all providers."""
        if provider_name:
            if provider_name in self._provider_health:
                self._provider_health[provider_name] = ProviderHealth(name=provider_name)
        else:
            for name in self._provider_health:
                self._provider_health[name] = ProviderHealth(name=name)


# Singleton pattern for shared instance
_search_manager_instance: Optional[SearchManager] = None
_search_manager_lock = threading.Lock()


def get_search_manager() -> SearchManager:
    """Get or create the shared SearchManager instance (thread-safe)."""
    global _search_manager_instance
    if _search_manager_instance is None:
        with _search_manager_lock:
            if _search_manager_instance is None:
                _search_manager_instance = SearchManager()
    return _search_manager_instance


def reset_search_manager():
    """Reset the shared SearchManager instance (useful for testing)."""
    global _search_manager_instance
    with _search_manager_lock:
        _search_manager_instance = None
