"""
Cache Manager.

Provides a centralized interface for accessing cache instances.
"""

import hashlib
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from .base import BaseCache, CacheBackend
from .file_cache import FileCache
from .memory_cache import MemoryCache

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Centralized cache manager.

    Provides factory methods for creating cache instances and
    manages the default cache configuration.

    Usage:
        manager = CacheManager()
        cache = manager.get_cache("my_cache")
        cache.set("key", "value")
    """

    _instance: Optional["CacheManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if not self._initialized:
                self._caches: Dict[str, BaseCache] = {}
                self._default_backend = CacheBackend.FILE
                self._base_dir: Optional[Path] = None
                self._initialized = True

    def configure(
        self,
        base_dir: Optional[Path] = None,
        default_backend: CacheBackend = CacheBackend.FILE,
    ) -> None:
        """
        Configure the cache manager.

        Args:
            base_dir: Base directory for file caches
            default_backend: Default cache backend type
        """
        self._base_dir = base_dir
        self._default_backend = default_backend

    def _get_base_dir(self) -> Path:
        """Get the base cache directory."""
        if self._base_dir:
            return self._base_dir

        # Try to get from settings
        try:
            from ..config import get_settings
            settings = get_settings()
            return settings.get_cache_dir()
        except Exception:
            # Fallback to default
            return Path(".cache")

    def get_cache(
        self,
        name: str,
        backend: Optional[CacheBackend] = None,
        **kwargs,
    ) -> BaseCache:
        """
        Get or create a named cache instance.

        Args:
            name: Cache name (used for directory/namespace)
            backend: Cache backend type (default: configured default)
            **kwargs: Additional arguments for cache constructor

        Returns:
            Cache instance
        """
        cache_key = f"{name}:{backend or self._default_backend}"

        if cache_key not in self._caches:
            backend = backend or self._default_backend

            if backend == CacheBackend.FILE:
                cache_dir = self._get_base_dir() / name
                self._caches[cache_key] = FileCache(cache_dir, **kwargs)

            elif backend == CacheBackend.MEMORY:
                self._caches[cache_key] = MemoryCache(**kwargs)

            elif backend == CacheBackend.REDIS:
                # Redis cache would be implemented separately
                raise NotImplementedError("Redis cache not yet implemented")

            else:
                raise ValueError(f"Unknown cache backend: {backend}")

        return self._caches[cache_key]

    def clear_all(self) -> Dict[str, int]:
        """
        Clear all managed caches.

        Returns:
            Dict mapping cache names to entries cleared
        """
        results = {}
        for name, cache in self._caches.items():
            results[name] = cache.clear()
        return results

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all managed caches.

        Returns:
            Dict mapping cache names to their stats
        """
        return {name: cache.get_stats() for name, cache in self._caches.items()}


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_cache(
    name: str = "default",
    backend: Optional[CacheBackend] = None,
    **kwargs,
) -> BaseCache:
    """
    Get a cache instance by name.

    Convenience function that wraps CacheManager.get_cache().

    Args:
        name: Cache name
        backend: Cache backend type
        **kwargs: Additional cache configuration

    Returns:
        Cache instance
    """
    return get_cache_manager().get_cache(name, backend, **kwargs)


# =============================================================================
# AI Cache - Specialized cache for AI responses
# =============================================================================


class AICache:
    """
    Specialized cache for AI responses.

    Provides a convenient interface for caching AI model responses
    with automatic key generation from request parameters.

    This is a wrapper around the base cache that handles
    key generation for AI request/response pairs.
    """

    _instance: Optional["AICache"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if not self._initialized:
                self._cache = get_cache("ai_responses")
                self._initialized = True

    def _get_cache_key(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate a unique key for the request."""
        key_data = {
            "prompt": prompt,
            "system": system,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """Get cached response for an AI request."""
        key = self._get_cache_key(prompt, system, temperature, max_tokens)
        entry = self._cache.get(key)
        if entry and isinstance(entry, dict):
            return entry.get("response")
        return entry

    def set(
        self,
        prompt: str,
        response: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> bool:
        """Cache an AI response."""
        key = self._get_cache_key(prompt, system, temperature, max_tokens)
        return self._cache.set(key, {
            "prompt": prompt,
            "system": system,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response": response,
        })

    def clear(self) -> int:
        """Clear the AI response cache."""
        return self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()


# Global AI cache instance
_ai_cache: Optional[AICache] = None


def get_ai_cache() -> AICache:
    """Get the global AI cache instance."""
    global _ai_cache
    if _ai_cache is None:
        _ai_cache = AICache()
    return _ai_cache
