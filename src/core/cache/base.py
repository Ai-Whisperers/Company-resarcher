"""
Base Cache Interface.

Defines the abstract interface that all cache implementations must follow.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Dict, TypeVar, Generic

T = TypeVar("T")


class CacheBackend(str, Enum):
    """Available cache backend types."""
    FILE = "file"
    MEMORY = "memory"
    REDIS = "redis"


@dataclass
class CacheEntry(Generic[T]):
    """
    A cache entry with metadata.

    Attributes:
        value: The cached value
        created_at: Unix timestamp when entry was created
        expires_at: Unix timestamp when entry expires (None = never)
        hits: Number of times this entry was accessed
        metadata: Optional additional metadata
    """
    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    hits: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> Optional[float]:
        """Get remaining TTL in seconds, or None if no expiry."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return max(0, remaining)

    @property
    def age(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at


class BaseCache(ABC):
    """
    Abstract base class for cache implementations.

    All cache backends must implement these methods to ensure
    consistent behavior across the application.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (None = use default)
            metadata: Optional metadata to store with entry

        Returns:
            True if successfully cached, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired
        """
        pass

    @abstractmethod
    def clear(self) -> int:
        """
        Clear all entries from the cache.

        Returns:
            Number of entries cleared
        """
        pass

    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """
        Get a cache entry with metadata.

        Default implementation wraps get() - override for better performance.

        Args:
            key: Cache key

        Returns:
            CacheEntry or None if not found
        """
        value = self.get(key)
        if value is not None:
            return CacheEntry(value=value)
        return None

    def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """
        Get multiple values from the cache.

        Default implementation calls get() for each key.
        Override for better performance with batch operations.

        Args:
            keys: List of cache keys

        Returns:
            Dict mapping keys to values (missing keys omitted)
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> int:
        """
        Set multiple values in the cache.

        Default implementation calls set() for each item.
        Override for better performance with batch operations.

        Args:
            items: Dict mapping keys to values
            ttl: Time-to-live in seconds

        Returns:
            Number of items successfully cached
        """
        count = 0
        for key, value in items.items():
            if self.set(key, value, ttl):
                count += 1
        return count

    def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple keys from the cache.

        Default implementation calls delete() for each key.

        Args:
            keys: List of cache keys

        Returns:
            Number of keys deleted
        """
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with stats like hits, misses, size, etc.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
