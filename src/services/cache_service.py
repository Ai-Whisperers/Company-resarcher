"""
Cache Service - Unified caching abstraction for Company Researcher.

This module provides a high-level caching service that abstracts the underlying
cache implementation (currently file-based, with Redis support planned).

Features:
- Unified interface for all caching needs
- Support for multiple cache namespaces
- TTL (time-to-live) support
- Cache statistics and monitoring
- Thread-safe operations

Usage:
    from src.services.cache_service import CacheService, get_cache_service

    cache = get_cache_service()

    # Simple key-value caching
    cache.set("my_key", {"data": "value"}, ttl_seconds=3600)
    data = cache.get("my_key")

    # With namespace
    cache.set("user:123", user_data, namespace="users")

    # Check cache health
    stats = cache.get_stats()
"""

import hashlib
import json
import os
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic

from ..core.config import get_settings
from ..core.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Represents a cached value with metadata."""

    value: T
    created_at: float
    ttl_seconds: Optional[int] = None
    namespace: str = "default"

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        return time.time() > (self.created_at + self.ttl_seconds)


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    expirations: int = 0
    errors: int = 0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "expirations": self.expirations,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_rate_percent": round(self.hit_rate, 2),
        }


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from the cache."""
        pass

    @abstractmethod
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set a value in the cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass

    @abstractmethod
    def clear(self, namespace: Optional[str] = None) -> int:
        """Clear cache entries. Returns count of deleted entries."""
        pass

    @abstractmethod
    def keys(self, pattern: Optional[str] = None) -> list[str]:
        """List cache keys matching pattern."""
        pass


class FileCacheBackend(CacheBackend):
    """File-based cache backend for development and simple deployments.

    Stores cached values as JSON files in a configurable directory.
    Thread-safe for concurrent access.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        settings = get_settings()
        self.cache_dir = cache_dir or (settings.BASE_DIR / ".cache" / "service")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Hash the key to create a safe filename
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from the file cache."""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        try:
            with self._lock:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return CacheEntry(
                        value=data["value"],
                        created_at=data["created_at"],
                        ttl_seconds=data.get("ttl_seconds"),
                        namespace=data.get("namespace", "default"),
                    )
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning(f"Failed to read cache file for key {key[:16]}...: {e}")
            return None

    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set a value in the file cache."""
        file_path = self._get_file_path(key)

        try:
            data = {
                "key": key,
                "value": entry.value,
                "created_at": entry.created_at,
                "ttl_seconds": entry.ttl_seconds,
                "namespace": entry.namespace,
            }
            with self._lock:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, default=str)
            return True
        except (IOError, TypeError) as e:
            logger.warning(f"Failed to write cache file for key {key[:16]}...: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from the file cache."""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return False

        try:
            with self._lock:
                file_path.unlink()
            return True
        except IOError as e:
            logger.warning(f"Failed to delete cache file for key {key[:16]}...: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the file cache."""
        return self._get_file_path(key).exists()

    def clear(self, namespace: Optional[str] = None) -> int:
        """Clear cache files, optionally filtered by namespace."""
        deleted = 0

        try:
            with self._lock:
                for file_path in self.cache_dir.glob("*.json"):
                    try:
                        if namespace:
                            # Read file to check namespace
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                if data.get("namespace") != namespace:
                                    continue
                        file_path.unlink()
                        deleted += 1
                    except (IOError, json.JSONDecodeError):
                        continue
        except IOError as e:
            logger.warning(f"Failed to clear cache: {e}")

        return deleted

    def keys(self, pattern: Optional[str] = None) -> list[str]:
        """List cache keys (returns hashed filenames without pattern support)."""
        keys = []
        for file_path in self.cache_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    key = data.get("key", file_path.stem)
                    keys.append(key)
            except (IOError, json.JSONDecodeError):
                continue
        return keys


class CacheService:
    """High-level cache service with statistics and namespace support.

    Provides a unified interface for caching with features like:
    - Multiple namespaces for logical separation
    - TTL support with automatic expiration checking
    - Statistics tracking for monitoring
    - Pluggable backends (file-based, Redis planned)

    Configuration:
        Environment variables:
        - CACHE_ENABLED: "true"/"false" (default: true)
        - CACHE_DEFAULT_TTL: seconds (default: 3600)
        - CACHE_DIR: directory path (default: .cache/service)

    Example:
        cache = CacheService()

        # Store with TTL
        cache.set("api:response", data, ttl_seconds=300)

        # Retrieve
        if data := cache.get("api:response"):
            process(data)

        # Check stats
        print(cache.get_stats().to_dict())
    """

    def __init__(
        self,
        backend: Optional[CacheBackend] = None,
        enabled: Optional[bool] = None,
        default_ttl: Optional[int] = None,
    ):
        """Initialize the cache service.

        Args:
            backend: Cache backend to use (default: FileCacheBackend)
            enabled: Whether caching is enabled (default: from CACHE_ENABLED env)
            default_ttl: Default TTL in seconds (default: from CACHE_DEFAULT_TTL env)
        """
        # Configuration from environment
        self.enabled = enabled if enabled is not None else (
            os.getenv("CACHE_ENABLED", "true").lower() == "true"
        )
        self.default_ttl = default_ttl or int(os.getenv("CACHE_DEFAULT_TTL", "3600"))

        # Backend initialization
        self.backend = backend or FileCacheBackend()

        # Statistics
        self._stats = CacheStats()
        self._stats_lock = threading.Lock()

    def _make_key(self, key: str, namespace: str = "default") -> str:
        """Create a namespaced cache key."""
        return f"{namespace}:{key}"

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key
            namespace: Logical namespace for the key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None

        full_key = self._make_key(key, namespace)

        try:
            entry = self.backend.get(full_key)

            if entry is None:
                with self._stats_lock:
                    self._stats.misses += 1
                return None

            # Check expiration
            if entry.is_expired:
                with self._stats_lock:
                    self._stats.expirations += 1
                    self._stats.misses += 1
                self.backend.delete(full_key)
                return None

            with self._stats_lock:
                self._stats.hits += 1

            return entry.value

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            with self._stats_lock:
                self._stats.errors += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        namespace: str = "default",
    ) -> bool:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl_seconds: Time-to-live in seconds (default: service default_ttl)
            namespace: Logical namespace for the key

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        full_key = self._make_key(key, namespace)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        try:
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl,
                namespace=namespace,
            )

            success = self.backend.set(full_key, entry)

            if success:
                with self._stats_lock:
                    self._stats.sets += 1

            return success

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            with self._stats_lock:
                self._stats.errors += 1
            return False

    def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete a value from the cache.

        Args:
            key: Cache key
            namespace: Logical namespace for the key

        Returns:
            True if deleted, False if not found
        """
        if not self.enabled:
            return False

        full_key = self._make_key(key, namespace)

        try:
            success = self.backend.delete(full_key)

            if success:
                with self._stats_lock:
                    self._stats.deletes += 1

            return success

        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            with self._stats_lock:
                self._stats.errors += 1
            return False

    def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if a key exists and is not expired."""
        if not self.enabled:
            return False

        full_key = self._make_key(key, namespace)
        entry = self.backend.get(full_key)

        if entry is None:
            return False

        if entry.is_expired:
            self.backend.delete(full_key)
            return False

        return True

    def clear(self, namespace: Optional[str] = None) -> int:
        """Clear cache entries.

        Args:
            namespace: If provided, only clear entries in this namespace

        Returns:
            Number of entries deleted
        """
        if not self.enabled:
            return 0

        return self.backend.clear(namespace)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._stats_lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                sets=self._stats.sets,
                deletes=self._stats.deletes,
                expirations=self._stats.expirations,
                errors=self._stats.errors,
            )

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._stats_lock:
            self._stats = CacheStats()


# =============================================================================
# Singleton Access
# =============================================================================

_cache_service: Optional[CacheService] = None
_cache_service_lock = threading.Lock()


def get_cache_service() -> CacheService:
    """Get the singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        with _cache_service_lock:
            if _cache_service is None:
                _cache_service = CacheService()
    return _cache_service


def reset_cache_service() -> None:
    """Reset the singleton cache service (for testing)."""
    global _cache_service
    with _cache_service_lock:
        _cache_service = None


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Classes
    "CacheService",
    "CacheBackend",
    "FileCacheBackend",
    "CacheEntry",
    "CacheStats",
    # Functions
    "get_cache_service",
    "reset_cache_service",
]
