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
from .providers.duckduckgo import DuckDuckGoProvider
from .providers.jina import JinaSearchProvider
from .providers.langsearch import LangSearchProvider
from .providers.serper import SerperProvider
from .providers.tavily_provider import TavilyProvider
from .providers.brave import BraveSearchProvider
from .providers.bing import BingSearchProvider
from src.core.logging import setup_logger
from src.core.config import get_settings

from src.lib.resilience.rate_limiting import rate_limiter_manager, RateLimitConfig

logger = setup_logger("search.manager")

# Rate limiting configuration
# Global limit: 360 RPM (6 RPS) with large burst for parallelism
# Individual providers have their own limits (DuckDuckGo: 30 RPM, Jina: 200 RPM, etc.)
DEFAULT_REQUESTS_PER_MINUTE = int(os.getenv("SEARCH_RATE_LIMIT_PER_MIN", "360"))
DEFAULT_BURST_SIZE = int(os.getenv("SEARCH_BURST_SIZE", "120"))  # Allow 120 concurrent requests
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

    def record_failure(
        self, is_rate_limit: bool = False, retry_after: Optional[float] = None
    ) -> None:
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
            "rate_limited": self.rate_limited_until is not None
            and time.monotonic() < self.rate_limited_until,
            "time_until_available": self.time_until_available(),
            "total_requests": self.total_requests,
            "success_rate": (
                (self.successful_requests / self.total_requests * 100)
                if self.total_requests > 0
                else 100.0
            ),
            "rate_limit_hits": self.rate_limit_hits,
        }


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
    3. Brave (2K free/month) - Priority 3
    4. Serper.dev (Google via API) - Priority 4
    4. Bing (1K free/month) - Priority 4
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

        # Configure global search rate limiter with high burst for parallelism
        # The global limiter prevents total overload, while individual providers
        # have their own limits (DuckDuckGo: 30 RPM, Jina: 200 RPM, Serper: 300 RPM, etc.)
        self._limiter_name = "search_global"
        rate_limiter_manager.get_limiter(
            self._limiter_name,
            RateLimitConfig(
                rate=requests_per_minute / 60.0, burst=DEFAULT_BURST_SIZE
            ),
        )

        if providers:
            self.providers = sorted(providers, key=lambda p: p.priority)
        else:
            self._init_default_providers()

        # Initialize health tracking and per-provider rate limiters
        for provider in self.providers:
            self._provider_health[provider.name] = ProviderHealth(name=provider.name)
            # Initialize per-provider rate limiter from api_limits.py
            # The rate_limiter_manager auto-configures from api_limits
            rate_limiter_manager.get_limiter(provider.name)

    def _init_default_providers(self):
        """Initialize default providers in priority order."""
        settings = get_settings()

        # Always add free providers first
        self.providers.append(DuckDuckGoProvider())
        self.providers.append(JinaSearchProvider())

        # Add LangSearch (FREE but requires API key)
        self.providers.append(LangSearchProvider())

        # Add Brave Search (2,000 free/month)
        self.providers.append(BraveSearchProvider())

        # Add paid providers if configured
        serper_key = getattr(settings, "SERPER_API_KEY", None)
        if serper_key:
            self.providers.append(SerperProvider())

        # Add Bing (1,000 free/month via Azure)
        self.providers.append(BingSearchProvider())

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
                # Apply per-provider rate limiting (uses limits from api_limits.py)
                # Each provider has its own limits: DuckDuckGo 30 RPM, Jina 200 RPM, Serper 300 RPM, etc.
                if not await rate_limiter_manager.acquire(
                    provider.name, timeout=5.0
                ):
                    logger.debug(f"{provider.name} rate limit reached, waiting...")
                    await asyncio.sleep(0.5)
                    if not await rate_limiter_manager.acquire(
                        provider.name, timeout=10.0
                    ):
                        logger.warning(f"{provider.name} rate limit timeout, trying next provider")
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
                health.record_failure(is_rate_limit=True, retry_after=e.retry_after)
                self._record_stat(provider.name, "rate_limit")

                if attempt < MAX_RETRIES and e.retry_after and e.retry_after < 10:
                    # Short retry-after, wait and retry same provider
                    backoff = e.retry_after or self._calculate_backoff(attempt)
                    logger.info(
                        f"Rate limited by {provider.name}, retrying in {backoff:.1f}s (attempt {attempt}/{MAX_RETRIES})"
                    )
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
                    logger.info(
                        f"Retrying {provider.name} in {backoff:.1f}s (attempt {attempt}/{MAX_RETRIES})"
                    )
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
                logger.debug(
                    f"Skipping {provider.name} - in cooldown ({wait_time:.1f}s remaining)"
                )
                errors.append(
                    (provider.name, "cooldown", f"Rate limited for {wait_time:.1f}s")
                )
                continue

            logger.info(f"Searching with {provider.name}: '{query[:50]}...'")
            results = await self._search_with_retry(provider, query, max_results)

            if results:
                logger.info(f"Got {len(results)} results from {provider.name}")
                return results

            # Record that this provider returned no results (BUG-053 fix)
            health = self._get_health(provider.name)
            if not health.is_healthy or health.rate_limit_hits > 0:
                errors.append((provider.name, "error", "Failed or rate limited"))
            else:
                errors.append((provider.name, "empty", "No results"))

            # Continue to next provider if fallback enabled
            if not self.enable_fallback:
                logger.warning(f"Fallback disabled, stopping after {provider.name}")
                break

        # All providers failed
        if errors:
            error_summary = "; ".join([f"{p}: {t}" for p, t, _ in errors])
            logger.error(f"All search providers failed (BUG-053): {error_summary}")
            raise SearchError(
                f"All providers failed: {error_summary}", "manager", query
            )

        # No providers available (all skipped due to missing API keys)
        available = [p.name for p in self.providers if p.is_available()]
        logger.error(
            f"No search providers available. Checked: {[p.name for p in self.providers]}, Available: {available}"
        )
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
                        query,
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
            1
            for h in self._provider_health.values()
            if h.rate_limited_until and time.monotonic() < h.rate_limited_until
        )
        return {
            "total_providers": len(self.providers),
            "healthy_providers": healthy_count,
            "rate_limited_providers": rate_limited_count,
            "providers": {
                name: health.to_dict() for name, health in self._provider_health.items()
            },
        }

    def reset_provider_health(self, provider_name: Optional[str] = None) -> None:
        """Reset health status for a provider or all providers."""
        if provider_name:
            if provider_name in self._provider_health:
                self._provider_health[provider_name] = ProviderHealth(
                    name=provider_name
                )
        else:
            for name in self._provider_health:
                self._provider_health[name] = ProviderHealth(name=name)

    async def search_parallel(
        self,
        query: str,
        max_results: int = 10,
        providers: Optional[List[str]] = None,
        timeout_seconds: float = 30.0,
        min_providers_for_success: int = 1,
    ) -> List[SearchResult]:
        """
        Execute search across multiple engines in parallel and combine results.

        This method queries all available search engines simultaneously instead of
        sequentially, significantly reducing search time (especially when DuckDuckGo
        is slow with its 60s timeout).

        Args:
            query: The search query
            max_results: Maximum total results to return (deduplicated)
            providers: Optional list of provider names to use (uses all available if None)
            timeout_seconds: Timeout for the entire parallel search operation
            min_providers_for_success: Minimum providers that must succeed (default 1)

        Returns:
            Combined, deduplicated list of SearchResult objects

        Features:
        - Runs DuckDuckGo, Jina, Tavily, etc. in parallel
        - Combines results and deduplicates by URL
        - Returns as soon as min_providers_for_success respond
        - Falls back to sequential if all parallel calls fail
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        # Determine which providers to use
        available = []
        for provider in self.providers:
            if providers and provider.name not in providers:
                continue
            if not provider.is_available():
                continue
            health = self._get_health(provider.name)
            if not health.is_available():
                continue
            available.append(provider)

        if not available:
            logger.warning("No search providers available for parallel search")
            return await self.search(query, max_results)  # Fall back to sequential

        logger.info(
            f"Parallel search with {len(available)} providers: {[p.name for p in available]}"
        )

        # Create search tasks for all providers
        async def search_provider(provider: SearchProvider) -> tuple:
            """Search with a single provider, return (provider_name, results_or_error)."""
            try:
                results = await provider.search(query, max_results)
                health = self._get_health(provider.name)
                health.record_success()
                self._record_stat(provider.name, "success")
                return (provider.name, results)
            except RateLimitError as e:
                health = self._get_health(provider.name)
                health.record_failure(is_rate_limit=True, retry_after=e.retry_after)
                self._record_stat(provider.name, "rate_limit")
                return (provider.name, e)
            except Exception as e:
                health = self._get_health(provider.name)
                health.record_failure()
                self._record_stat(provider.name, "failure")
                logger.debug(f"{provider.name} parallel search failed: {e}")
                return (provider.name, e)

        # Run all searches in parallel with timeout using asyncio.wait for partial results
        tasks = [asyncio.create_task(search_provider(p)) for p in available]
        done, pending = await asyncio.wait(
            tasks, timeout=timeout_seconds, return_when=asyncio.ALL_COMPLETED
        )

        # Cancel any pending tasks
        for task in pending:
            task.cancel()

        # Collect results from completed tasks
        results_list = []
        for task in done:
            try:
                result = task.result()
                results_list.append(result)
            except Exception as e:
                logger.debug(f"Task failed: {e}")

        if pending:
            logger.info(
                f"Parallel search: {len(done)} providers completed, {len(pending)} timed out"
            )

        # Process results
        all_results = []
        successful_providers = []
        seen_urls = set()

        for item in results_list:
            if isinstance(item, BaseException):
                continue
            provider_name, provider_results = item
            if isinstance(provider_results, Exception):
                continue
            if provider_results:
                successful_providers.append(provider_name)
                for result in provider_results:
                    # Deduplicate by URL
                    if result.url not in seen_urls:
                        seen_urls.add(result.url)
                        all_results.append(result)

        # Check if we met minimum provider threshold
        if len(successful_providers) < min_providers_for_success:
            logger.warning(
                f"Only {len(successful_providers)} providers succeeded "
                f"(need {min_providers_for_success}), falling back to sequential"
            )
            return await self.search(query, max_results)

        # Trim to max_results
        all_results = all_results[:max_results]

        logger.info(
            f"Parallel search complete: {len(all_results)} results from "
            f"{len(successful_providers)} providers ({successful_providers})"
        )
        return all_results

    async def search_distributed(
        self,
        queries: List[str],
        max_results_per_query: int = 5,
        timeout_seconds: float = 60.0,
    ) -> Dict[str, List[SearchResult]]:
        """
        Execute MULTIPLE queries using a queue-based pull architecture.

        This method uses a central queue that provider workers pull from:
        - All queries go into a shared asyncio.Queue
        - Each provider has a worker that pulls queries when ready
        - Faster providers (Serper 3000 RPM) naturally handle more queries
        - Slower providers (DuckDuckGo 30 RPM) handle fewer but still contribute
        - Failed queries are requeued for retry by a different provider

        This is much more efficient than round-robin because:
        1. Fast providers aren't waiting while slow ones process
        2. Rate limits are respected per-provider
        3. Load balancing is automatic based on actual throughput

        Real Provider Limits (from api_limits.py):
        - Serper: 3000 RPM, 50 concurrent (FASTEST)
        - Jina: 200 RPM, 10 concurrent
        - Tavily: 100 RPM, 10 concurrent
        - Brave: 60 RPM, 5 concurrent
        - DuckDuckGo: 30 RPM, 3 concurrent
        - LangSearch: 30 RPM, 5 concurrent

        Args:
            queries: List of search queries to execute
            max_results_per_query: Results per query (default 5)
            timeout_seconds: Timeout for entire operation

        Returns:
            Dict mapping query -> list of SearchResult

        Example:
            results = await manager.search_distributed([
                "company funding history",
                "company CEO background",
                "company competitors",
                "company news 2024",
            ])
            # Queries distributed based on provider availability
        """
        if not queries:
            return {}

        # Get available providers sorted by priority (fastest first)
        available = []
        for provider in self.providers:
            if not provider.is_available():
                continue
            health = self._get_health(provider.name)
            if not health.is_available():
                continue
            available.append(provider)

        if not available:
            logger.warning("No providers available for distributed search")
            # Fall back to sequential
            results = {}
            for query in queries:
                try:
                    results[query] = await self.search(query, max_results_per_query)
                except Exception as e:
                    logger.error(f"Sequential fallback failed for '{query}': {e}")
                    results[query] = []
            return results

        logger.info(
            f"Queue-based distributed search: {len(queries)} queries across "
            f"{len(available)} providers: {[p.name for p in available]}"
        )

        # Create the central query queue (CQ-107: bounded to prevent memory exhaustion)
        # maxsize = queries + buffer for retries (2x queries)
        queue_maxsize = max(len(queries) * 2, 100)
        query_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_maxsize)
        for query in queries:
            await query_queue.put((query, 0))  # (query, retry_count)

        # Results storage (thread-safe via asyncio)
        results: Dict[str, List[SearchResult]] = {}
        results_lock = asyncio.Lock()

        # Track which providers processed which queries (for stats)
        provider_stats: Dict[str, int] = {p.name: 0 for p in available}

        # Retry queue for failed queries (CQ-107: bounded)
        retry_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_maxsize)

        async def safe_retry_put(query: str, retry_count: int) -> bool:
            """Safely put query in retry queue with timeout (CQ-107)."""
            try:
                await asyncio.wait_for(
                    retry_queue.put((query, retry_count)),
                    timeout=1.0
                )
                return True
            except asyncio.TimeoutError:
                logger.warning(f"Retry queue full, dropping query: {query[:30]}...")
                return False

        async def provider_worker(provider: SearchProvider) -> None:
            """Worker that pulls queries from queue and processes them."""
            while True:
                try:
                    # Try to get a query (non-blocking check for shutdown)
                    try:
                        query, retry_count = query_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        # Check retry queue
                        try:
                            query, retry_count = retry_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            # No work available, exit
                            return

                    # Skip if query already has results (from another provider)
                    async with results_lock:
                        if query in results and results[query]:
                            query_queue.task_done()
                            continue

                    # Apply rate limiting for this provider
                    if not await rate_limiter_manager.acquire(provider.name, timeout=2.0):
                        # Rate limited - put query back for another provider
                        await safe_retry_put(query, retry_count)
                        query_queue.task_done()
                        await asyncio.sleep(0.1)  # Brief pause before next attempt
                        continue

                    # Execute search
                    try:
                        search_results = await provider.search(query, max_results_per_query)

                        if search_results:
                            async with results_lock:
                                results[query] = search_results
                            health = self._get_health(provider.name)
                            health.record_success()
                            self._record_stat(provider.name, "success")
                            provider_stats[provider.name] += 1
                            logger.debug(f"{provider.name} completed: '{query[:30]}...'")
                        else:
                            # Empty results - try another provider if retries left
                            if retry_count < 2:
                                await safe_retry_put(query, retry_count + 1)
                            else:
                                async with results_lock:
                                    results[query] = []

                    except RateLimitError as e:
                        health = self._get_health(provider.name)
                        health.record_failure(is_rate_limit=True, retry_after=e.retry_after)
                        self._record_stat(provider.name, "rate_limit")
                        # Requeue for different provider
                        if retry_count < 2:
                            await safe_retry_put(query, retry_count + 1)
                        else:
                            async with results_lock:
                                results[query] = []

                    except Exception as e:
                        health = self._get_health(provider.name)
                        health.record_failure()
                        self._record_stat(provider.name, "failure")
                        logger.debug(f"{provider.name} failed for '{query[:30]}...': {e}")
                        # Requeue for different provider
                        if retry_count < 2:
                            await safe_retry_put(query, retry_count + 1)
                        else:
                            async with results_lock:
                                results[query] = []

                    query_queue.task_done()

                except asyncio.CancelledError:
                    return
                except Exception as e:
                    logger.error(f"Worker error for {provider.name}: {e}")
                    return

        # Create worker tasks for all providers
        # Faster providers get more workers based on their concurrent limit
        worker_tasks = []
        for provider in available:
            # Get concurrent limit from rate limiter config
            from src.core.config.api_limits import get_provider_limits
            limits = get_provider_limits(provider.name)
            num_workers = min(limits.concurrent_requests if limits else 3, 10)  # Cap at 10 workers

            for _ in range(num_workers):
                task = asyncio.create_task(provider_worker(provider))
                worker_tasks.append(task)

        logger.info(f"Started {len(worker_tasks)} workers across {len(available)} providers")

        # Wait for all queries to be processed or timeout
        try:
            # Wait for main queue to empty
            await asyncio.wait_for(
                query_queue.join(),
                timeout=timeout_seconds
            )
            # Also wait for retry queue
            await asyncio.wait_for(
                retry_queue.join(),
                timeout=5.0  # Short timeout for retries
            )
        except asyncio.TimeoutError:
            logger.warning(f"Distributed search timed out after {timeout_seconds}s")
        finally:
            # Cancel all workers
            for task in worker_tasks:
                task.cancel()

            # Wait for workers to finish
            await asyncio.gather(*worker_tasks, return_exceptions=True)

        # Ensure all queries have an entry (even if empty)
        for query in queries:
            if query not in results:
                results[query] = []

        # Log statistics
        successful = sum(1 for r in results.values() if r)
        logger.info(
            f"Queue-based search complete: {successful}/{len(queries)} queries successful"
        )
        logger.info(f"Provider distribution: {provider_stats}")

        return results

    async def search_paginated(
        self,
        query: str,
        results_per_page: int = 10,
        max_pages: int = 3,
        page_delay_seconds: float = 1.0,
        preferred_provider: Optional[str] = None,
        deduplicate: bool = True,
    ) -> List[SearchResult]:
        """
        Execute a paginated search across multiple pages (TECH-003).

        Simulates pagination by making multiple search requests with
        increasing result counts and deduplicating results.

        Args:
            query: The search query
            results_per_page: Results to fetch per page
            max_pages: Maximum number of pages to fetch
            page_delay_seconds: Delay between page requests
            preferred_provider: Force a specific provider
            deduplicate: Remove duplicate URLs (default True)

        Returns:
            Combined list of SearchResult objects from all pages

        Note:
            Many search providers don't support true pagination.
            This implementation requests larger result sets to simulate
            pagination behavior.
        """
        settings = get_settings()
        page_delay = page_delay_seconds or settings.search.page_delay_seconds

        all_results: List[SearchResult] = []
        seen_urls: set = set()

        for page in range(max_pages):
            try:
                # Calculate how many results to request
                # Each page requests more results to get "deeper" in search
                total_to_fetch = results_per_page * (page + 1)

                logger.info(
                    f"Fetching page {page + 1}/{max_pages} for '{query[:30]}...' (requesting {total_to_fetch} results)"
                )

                results = await self.search(
                    query,
                    max_results=total_to_fetch,
                    preferred_provider=preferred_provider,
                )

                # Extract new results (skip ones we already have)
                new_results = []
                for result in results:
                    if deduplicate:
                        if result.url not in seen_urls:
                            seen_urls.add(result.url)
                            new_results.append(result)
                    else:
                        new_results.append(result)

                # Only add results beyond what we already have
                start_idx = len(all_results)
                all_results.extend(new_results[start_idx:])

                logger.info(
                    f"Page {page + 1}: got {len(new_results)} new results (total: {len(all_results)})"
                )

                # If no new results, stop pagination
                if len(new_results) <= len(all_results) - results_per_page:
                    logger.info(
                        f"No new results on page {page + 1}, stopping pagination"
                    )
                    break

                # Rate limiting between pages
                if page < max_pages - 1:
                    await asyncio.sleep(page_delay)

            except SearchError as e:
                logger.warning(f"Failed to fetch page {page + 1}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching page {page + 1}: {e}")
                break

        logger.info(
            f"Paginated search complete: {len(all_results)} total results from {max_pages} pages"
        )
        return all_results


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
