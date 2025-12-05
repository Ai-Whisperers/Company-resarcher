"""
In-memory LRU Cache Implementation.

Fast, thread-safe caching with LRU eviction policy.
"""

import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

from .base import BaseCache, CacheEntry

logger = logging.getLogger(__name__)


class MemoryCache(BaseCache):
    """
    In-memory LRU cache implementation.

    Features:
    - LRU (Least Recently Used) eviction policy
    - Thread-safe operations
    - Automatic expiration checking
    - Configurable max size

    Usage:
        cache = MemoryCache(max_size=1000)
        cache.set("key", {"data": "value"}, ttl=3600)
        data = cache.get("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[int] = None,
    ):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries (LRU eviction when exceeded)
            default_ttl: Default TTL in seconds (None = no expiry)
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache is full."""
        while len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
            self._evictions += 1

    def _cleanup_expired(self) -> None:
        """Remove expired entries (called periodically)."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._hits += 1

            return entry.value

    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry with metadata."""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None

            self._cache.move_to_end(key)
            self._hits += 1

            return entry

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set a value in the cache."""
        with self._lock:
            # Calculate expiration
            effective_ttl = ttl if ttl is not None else self._default_ttl
            expires_at = None
            if effective_ttl is not None:
                expires_at = time.time() + effective_ttl

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Evict if needed
            self._evict_if_needed()

            # Add new entry
            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
                hits=0,
                metadata=metadata or {},
            )

            return True

    def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[key]
                return False
            return True

    def clear(self) -> int:
        """Clear all entries from the cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            return {
                "backend": "memory",
                "entries": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "default_ttl": self._default_ttl,
            }

    def __repr__(self) -> str:
        return f"<MemoryCache entries={len(self._cache)} max={self._max_size}>"
