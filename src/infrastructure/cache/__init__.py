"""
Unified Cache Module.

Provides a consistent caching interface with multiple backend implementations:
- FileCache: JSON file-based caching (default)
- MemoryCache: In-memory LRU cache
- RedisCache: Redis-backed distributed cache

Usage:
    from src.core.cache import get_cache, CacheBackend

    # Get default cache (file-based)
    cache = get_cache()
    cache.set("key", {"data": "value"}, ttl=3600)
    data = cache.get("key")

    # Get specific backend
    memory_cache = get_cache(CacheBackend.MEMORY)
"""

from .base import BaseCache, CacheBackend, CacheEntry
from .file_cache import FileCache
from .memory_cache import MemoryCache
from .redis_cache import RedisCache, RedisCacheConfig
from .manager import CacheManager, get_cache, get_ai_cache, AICache
from .url_cache import URLFetchCache
from .cross_company_cache import (
    CrossCompanyURLCache,
    get_cross_company_cache,
    reset_cross_company_cache,
)

__all__ = [
    # Base
    "BaseCache",
    "CacheBackend",
    "CacheEntry",
    # Implementations
    "FileCache",
    "MemoryCache",
    "RedisCache",
    "RedisCacheConfig",
    "URLFetchCache",
    "CrossCompanyURLCache",
    "get_cross_company_cache",
    "reset_cross_company_cache",
    # Manager
    "CacheManager",
    "get_cache",
    "get_ai_cache",
    "AICache",
]
