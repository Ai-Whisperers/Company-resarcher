"""
Cache Context Manager (IMP-001: Unified Caching Layer).

Provides a context manager for wrapping expensive operations with caching.
Inspired by crawl4ai's CacheContext pattern.

Usage:
    from src.core.cache.cache_context import CacheContext, CacheMode

    # Basic usage - cache fetch results
    async with CacheContext(url, mode=CacheMode.ENABLED) as cache:
        if cache.hit:
            return cache.result  # Return cached data

        result = await fetch_data(url)
        cache.result = result  # Will be cached on context exit

    # Force fresh fetch, bypass cache read
    async with CacheContext(key, mode=CacheMode.BYPASS) as cache:
        result = await expensive_operation()
        cache.result = result  # Still saves to cache

    # Disable caching entirely
    async with CacheContext(key, mode=CacheMode.DISABLED) as cache:
        result = await operation()  # No cache interaction
"""

import hashlib
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Dict

from ...services.data import get_cache_service, CacheService
from ..logging import setup_logger

logger = setup_logger("cache_context")


class CacheMode(str, Enum):
    """Cache operation modes."""

    ENABLED = "enabled"  # Normal caching - read and write
    DISABLED = "disabled"  # No caching at all
    BYPASS = "bypass"  # Skip read, but still write
    READ_ONLY = "read_only"  # Only read from cache, don't write
    WRITE_ONLY = "write_only"  # Only write to cache, don't read


@dataclass
class CacheResult:
    """Result container for cache operations."""

    hit: bool = False
    result: Any = None
    cached_at: Optional[float] = None
    age_seconds: Optional[float] = None
    key: str = ""
    namespace: str = "default"

    @property
    def is_stale(self) -> bool:
        """Check if cached data is older than 1 hour."""
        if self.age_seconds is None:
            return False
        return self.age_seconds > 3600


@dataclass
class CacheContext:
    """
    Context manager for unified cache operations.

    Wraps expensive operations with automatic caching based on a key.
    Supports multiple cache modes for different use cases.
    """

    key: str
    mode: CacheMode = CacheMode.ENABLED
    ttl_seconds: int = 3600  # 1 hour default
    namespace: str = "default"
    cache_service: Optional[CacheService] = None

    # Internal state
    _result: Any = field(default=None, repr=False)
    _hit: bool = field(default=False, repr=False)
    _cached_at: Optional[float] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize cache service if not provided."""
        if self.cache_service is None:
            self.cache_service = get_cache_service()

    @property
    def cache_key(self) -> str:
        """Generate a unique cache key."""
        # If key looks like a URL or long string, hash it
        if len(self.key) > 100 or "/" in self.key or ":" in self.key:
            return hashlib.sha256(self.key.encode()).hexdigest()[:32]
        return self.key

    def should_read(self) -> bool:
        """Check if we should attempt to read from cache."""
        return self.mode in (CacheMode.ENABLED, CacheMode.READ_ONLY)

    def should_write(self) -> bool:
        """Check if we should write to cache."""
        return self.mode in (CacheMode.ENABLED, CacheMode.BYPASS, CacheMode.WRITE_ONLY)

    @property
    def hit(self) -> bool:
        """Whether cache was hit."""
        return self._hit

    @property
    def result(self) -> Any:
        """Get the cached or computed result."""
        return self._result

    @result.setter
    def result(self, value: Any):
        """Set the result to be cached."""
        self._result = value

    @property
    def age_seconds(self) -> Optional[float]:
        """Get age of cached data in seconds."""
        if self._cached_at is None:
            return None
        return time.time() - self._cached_at

    async def __aenter__(self) -> "CacheContext":
        """Enter cache context - attempt to read from cache."""
        if self.mode == CacheMode.DISABLED:
            return self

        if self.should_read():
            try:
                cached = self.cache_service.get(
                    self.cache_key, namespace=self.namespace
                )
                if cached is not None:
                    # Parse cache metadata if available
                    if isinstance(cached, dict) and "_cache_meta" in cached:
                        self._result = cached.get("data")
                        self._cached_at = cached.get("_cache_meta", {}).get(
                            "cached_at"
                        )
                    else:
                        self._result = cached
                        self._cached_at = time.time()  # Unknown, assume fresh

                    self._hit = True
                    logger.debug(
                        f"Cache HIT for {self.namespace}:{self.cache_key[:16]}..."
                    )
            except Exception as e:
                logger.debug(f"Cache read error (non-fatal): {e}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit cache context - write to cache if applicable."""
        if self.mode == CacheMode.DISABLED:
            return

        # Don't cache if there was an exception
        if exc_type is not None:
            return

        # Don't cache if we got a hit (no new data to cache)
        if self._hit:
            return

        if self.should_write() and self._result is not None:
            try:
                # Wrap result with cache metadata
                cache_data = {
                    "data": self._result,
                    "_cache_meta": {
                        "cached_at": time.time(),
                        "key": self.key,
                        "namespace": self.namespace,
                    },
                }
                self.cache_service.set(
                    self.cache_key,
                    cache_data,
                    ttl_seconds=self.ttl_seconds,
                    namespace=self.namespace,
                )
                logger.debug(
                    f"Cache SET for {self.namespace}:{self.cache_key[:16]}... "
                    f"(TTL: {self.ttl_seconds}s)"
                )
            except Exception as e:
                logger.debug(f"Cache write error (non-fatal): {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for this context."""
        return {
            "key": self.cache_key,
            "namespace": self.namespace,
            "mode": self.mode.value,
            "hit": self._hit,
            "age_seconds": self.age_seconds,
            "has_result": self._result is not None,
        }


@asynccontextmanager
async def cache_context(
    key: str,
    mode: CacheMode = CacheMode.ENABLED,
    ttl_seconds: int = 3600,
    namespace: str = "default",
):
    """
    Functional async context manager for caching.

    Example:
        async with cache_context("my_key") as cache:
            if cache.hit:
                return cache.result
            result = await expensive_operation()
            cache.result = result
    """
    ctx = CacheContext(
        key=key, mode=mode, ttl_seconds=ttl_seconds, namespace=namespace
    )
    async with ctx:
        yield ctx


def cache_key_for_url(url: str, params: Optional[Dict] = None) -> str:
    """Generate a cache key for a URL with optional parameters."""
    key_parts = [url]
    if params:
        # Sort params for consistent hashing
        sorted_params = sorted(params.items())
        key_parts.append(str(sorted_params))
    return hashlib.sha256(":".join(key_parts).encode()).hexdigest()[:32]


def cache_key_for_query(query: str, source: str = "default") -> str:
    """Generate a cache key for a search query."""
    key = f"{source}:{query.lower().strip()}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


__all__ = [
    "CacheContext",
    "CacheMode",
    "CacheResult",
    "cache_context",
    "cache_key_for_url",
    "cache_key_for_query",
]
