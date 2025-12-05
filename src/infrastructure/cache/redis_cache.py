"""
Redis caching layer for Company Researcher.

Provides:
- RedisCache: General-purpose async Redis caching
- RedisDeadLetterQueue: Persistent dead letter queue
- RedisCircuitBreaker: Distributed circuit breaker state

Usage:
    from src.infrastructure.cache.redis_cache import get_redis_cache, RedisDeadLetterQueue

    # General caching
    cache = await get_redis_cache()
    await cache.set("key", {"data": "value"}, ttl=3600)
    data = await cache.get("key")

    # Dead letter queue
    dlq = RedisDeadLetterQueue(cache)
    await dlq.enqueue("failed_task", {"error": "timeout"})

    # Circuit breaker
    cb = RedisCircuitBreaker(cache, "api_service")
    if await cb.is_open():
        raise CircuitOpenError()
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

# Optional Redis support
try:
    import redis.asyncio as aioredis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    aioredis = None


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


def _get_redis_settings():
    """Lazy import to avoid circular dependency."""
    from src.core.config import get_settings

    return get_settings().redis


@dataclass
class RedisCacheConfig:
    """Redis cache configuration (ARCH-004: uses centralized settings)."""

    host: str = field(default_factory=lambda: _get_redis_settings().host)
    port: int = field(default_factory=lambda: _get_redis_settings().port)
    db: int = field(default_factory=lambda: _get_redis_settings().db)
    password: Optional[str] = field(
        default_factory=lambda: _get_redis_settings().password
    )
    ssl: bool = field(default_factory=lambda: _get_redis_settings().ssl)
    default_ttl: int = field(default_factory=lambda: _get_redis_settings().default_ttl)
    key_prefix: str = field(default_factory=lambda: _get_redis_settings().key_prefix)
    max_connections: int = field(
        default_factory=lambda: _get_redis_settings().max_connections
    )


# Backwards compatibility alias
CacheConfig = RedisCacheConfig


class RedisCache:
    """
    Async Redis cache client with connection pooling.

    Features:
    - JSON serialization for complex objects
    - Automatic key prefixing
    - TTL management
    - Connection pooling
    - Graceful degradation when Redis unavailable
    """

    def __init__(self, config: Optional[RedisCacheConfig] = None):
        self.config = config or RedisCacheConfig()
        self._pool: Optional[Any] = None
        self._connected = False

    async def connect(self) -> bool:
        """Establish connection to Redis."""
        if not HAS_REDIS:
            logger.warning(
                "Redis not installed. Install with: pip install redis[hiredis]"
            )
            return False

        if self._connected and self._pool:
            return True

        try:
            self._pool = aioredis.ConnectionPool.from_url(
                self._build_url(),
                max_connections=self.config.max_connections,
                decode_responses=True,
            )
            # Test connection
            client = aioredis.Redis(connection_pool=self._pool)
            await client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False

    def _build_url(self) -> str:
        """Build Redis connection URL."""
        protocol = "rediss" if self.config.ssl else "redis"
        auth = f":{self.config.password}@" if self.config.password else ""
        return (
            f"{protocol}://{auth}{self.config.host}:{self.config.port}/{self.config.db}"
        )

    def _get_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.config.key_prefix}{key}"

    async def _get_client(self) -> Optional[Any]:
        """Get Redis client, connecting if needed."""
        if not self._connected:
            await self.connect()
        if self._pool:
            return aioredis.Redis(connection_pool=self._pool)
        return None

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key doesn't exist

        Returns:
            Cached value or default
        """
        client = await self._get_client()
        if not client:
            return default

        try:
            prefixed_key = self._get_key(key)
            value = await client.get(prefixed_key)
            if value is None:
                return default
            return json.loads(value)
        except json.JSONDecodeError:
            return value  # Return raw string if not JSON
        except Exception as e:
            logger.error(f"Redis GET error for {key}: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (uses default if not specified)

        Returns:
            True if successful
        """
        client = await self._get_client()
        if not client:
            return False

        try:
            prefixed_key = self._get_key(key)
            serialized = json.dumps(value, default=str)
            ttl = ttl or self.config.default_ttl
            await client.set(prefixed_key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = await self._get_client()
        if not client:
            return False

        try:
            prefixed_key = self._get_key(key)
            await client.delete(prefixed_key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = await self._get_client()
        if not client:
            return False

        try:
            prefixed_key = self._get_key(key)
            return bool(await client.exists(prefixed_key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for {key}: {e}")
            return False

    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter."""
        client = await self._get_client()
        if not client:
            return None

        try:
            prefixed_key = self._get_key(key)
            return await client.incrby(prefixed_key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for {key}: {e}")
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key."""
        client = await self._get_client()
        if not client:
            return False

        try:
            prefixed_key = self._get_key(key)
            return bool(await client.expire(prefixed_key, ttl))
        except Exception as e:
            logger.error(f"Redis EXPIRE error for {key}: {e}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once."""
        client = await self._get_client()
        if not client:
            return {}

        try:
            prefixed_keys = [self._get_key(k) for k in keys]
            values = await client.mget(prefixed_keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Redis MGET error: {e}")
            return {}

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set multiple keys at once."""
        client = await self._get_client()
        if not client:
            return False

        try:
            ttl = ttl or self.config.default_ttl
            pipe = client.pipeline()
            for key, value in items.items():
                prefixed_key = self._get_key(key)
                serialized = json.dumps(value, default=str)
                pipe.set(prefixed_key, serialized, ex=ttl)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis MSET error: {e}")
            return False

    async def close(self):
        """Close Redis connection pool."""
        if self._pool:
            await self._pool.disconnect()
            self._connected = False
            logger.info("Redis connection closed")


class RedisDeadLetterQueue:
    """
    Persistent dead letter queue using Redis lists.

    Failed tasks are stored with metadata for later retry or analysis.
    """

    def __init__(
        self,
        cache: RedisCache,
        queue_name: str = "dlq",
        max_size: int = 1000,
    ):
        self.cache = cache
        self.queue_key = f"dlq:{queue_name}"
        self.max_size = max_size

    async def enqueue(
        self,
        task_id: str,
        error: Union[str, Exception],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add failed task to dead letter queue.

        Args:
            task_id: Unique task identifier
            error: Error message or exception
            context: Additional context about the failure
        """
        client = await self.cache._get_client()
        if not client:
            logger.warning(f"DLQ unavailable, task {task_id} not queued")
            return False

        try:
            item = {
                "task_id": task_id,
                "error": str(error),
                "context": context or {},
                "timestamp": time.time(),
                "retry_count": 0,
            }

            prefixed_key = self.cache._get_key(self.queue_key)
            await client.lpush(prefixed_key, json.dumps(item, default=str))

            # Trim to max size
            await client.ltrim(prefixed_key, 0, self.max_size - 1)

            logger.info(f"Task {task_id} added to DLQ")
            return True
        except Exception as e:
            logger.error(f"DLQ enqueue error: {e}")
            return False

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Remove and return oldest item from queue."""
        client = await self.cache._get_client()
        if not client:
            return None

        try:
            prefixed_key = self.cache._get_key(self.queue_key)
            item = await client.rpop(prefixed_key)
            if item:
                return json.loads(item)
            return None
        except Exception as e:
            logger.error(f"DLQ dequeue error: {e}")
            return None

    async def peek(self, count: int = 10) -> List[Dict[str, Any]]:
        """View items without removing them."""
        client = await self.cache._get_client()
        if not client:
            return []

        try:
            prefixed_key = self.cache._get_key(self.queue_key)
            items = await client.lrange(prefixed_key, 0, count - 1)
            return [json.loads(item) for item in items]
        except Exception as e:
            logger.error(f"DLQ peek error: {e}")
            return []

    async def size(self) -> int:
        """Get number of items in queue."""
        client = await self.cache._get_client()
        if not client:
            return 0

        try:
            prefixed_key = self.cache._get_key(self.queue_key)
            return await client.llen(prefixed_key)
        except Exception as e:
            logger.error(f"DLQ size error: {e}")
            return 0

    async def clear(self) -> bool:
        """Clear all items from queue."""
        return await self.cache.delete(self.queue_key)


class RedisCircuitBreaker:
    """
    Distributed circuit breaker using Redis for state.

    Allows multiple instances to share circuit breaker state,
    preventing cascading failures across distributed systems.
    """

    def __init__(
        self,
        cache: RedisCache,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_requests: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            cache: Redis cache instance
            service_name: Name of the service being protected
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            half_open_requests: Number of test requests in half-open state
        """
        self.cache = cache
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        # Redis keys
        self.state_key = f"cb:{service_name}:state"
        self.failures_key = f"cb:{service_name}:failures"
        self.last_failure_key = f"cb:{service_name}:last_failure"
        self.half_open_count_key = f"cb:{service_name}:half_open_count"

    async def get_state(self) -> CircuitState:
        """Get current circuit state."""
        state = await self.cache.get(self.state_key, CircuitState.CLOSED.value)
        return CircuitState(state)

    async def is_open(self) -> bool:
        """Check if circuit is open (should reject requests)."""
        state = await self.get_state()

        if state == CircuitState.CLOSED:
            return False

        if state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            last_failure = await self.cache.get(self.last_failure_key, 0)
            if time.time() - last_failure >= self.recovery_timeout:
                # Transition to half-open
                await self._set_state(CircuitState.HALF_OPEN)
                await self.cache.set(self.half_open_count_key, 0)
                return False
            return True

        # Half-open: allow limited requests
        return False

    async def record_success(self):
        """Record a successful request."""
        state = await self.get_state()

        if state == CircuitState.HALF_OPEN:
            count = await self.cache.incr(self.half_open_count_key) or 1
            if count >= self.half_open_requests:
                # Service recovered, close circuit
                await self._set_state(CircuitState.CLOSED)
                await self.cache.delete(self.failures_key)
                logger.info(f"Circuit breaker for {self.service_name} CLOSED")
        elif state == CircuitState.CLOSED:
            # Reset failure count on success
            await self.cache.set(self.failures_key, 0)

    async def record_failure(self):
        """Record a failed request."""
        state = await self.get_state()

        if state == CircuitState.HALF_OPEN:
            # Failure in half-open, back to open
            await self._set_state(CircuitState.OPEN)
            await self.cache.set(self.last_failure_key, time.time())
            logger.warning(
                f"Circuit breaker for {self.service_name} OPEN (half-open failure)"
            )
            return

        # Increment failure count
        failures = await self.cache.incr(self.failures_key) or 1
        await self.cache.set(self.last_failure_key, time.time())

        if failures >= self.failure_threshold:
            await self._set_state(CircuitState.OPEN)
            logger.warning(
                f"Circuit breaker for {self.service_name} OPEN "
                f"(threshold {self.failure_threshold} reached)"
            )

    async def _set_state(self, state: CircuitState):
        """Set circuit state."""
        await self.cache.set(self.state_key, state.value, ttl=86400)  # 24h TTL

    async def reset(self):
        """Manually reset circuit breaker to closed state."""
        await self._set_state(CircuitState.CLOSED)
        await self.cache.delete(self.failures_key)
        await self.cache.delete(self.last_failure_key)
        await self.cache.delete(self.half_open_count_key)
        logger.info(f"Circuit breaker for {self.service_name} manually RESET")

    async def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "service": self.service_name,
            "state": (await self.get_state()).value,
            "failures": await self.cache.get(self.failures_key, 0),
            "last_failure": await self.cache.get(self.last_failure_key, 0),
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


# Singleton instance
_redis_cache: Optional[RedisCache] = None


async def get_redis_cache() -> RedisCache:
    """Get or create singleton Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
        await _redis_cache.connect()
    return _redis_cache


async def close_redis_cache():
    """Close singleton Redis cache instance."""
    global _redis_cache
    if _redis_cache:
        await _redis_cache.close()
        _redis_cache = None


# Utility functions for common caching patterns
async def cache_research_result(
    company_name: str,
    phase: str,
    result: Dict[str, Any],
    ttl: int = 86400,  # 24 hours default
) -> bool:
    """Cache a research phase result."""
    cache = await get_redis_cache()
    key = f"research:{company_name.lower().replace(' ', '_')}:{phase}"
    return await cache.set(key, result, ttl=ttl)


async def get_cached_research(
    company_name: str,
    phase: str,
) -> Optional[Dict[str, Any]]:
    """Get cached research phase result."""
    cache = await get_redis_cache()
    key = f"research:{company_name.lower().replace(' ', '_')}:{phase}"
    return await cache.get(key)


async def cache_search_results(
    query: str,
    results: List[Dict[str, Any]],
    ttl: int = 3600,  # 1 hour default
) -> bool:
    """Cache search results."""
    cache = await get_redis_cache()
    # Use hash of query as key to handle special characters
    import hashlib

    query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
    key = f"search:{query_hash}"
    return await cache.set(key, results, ttl=ttl)


async def get_cached_search(query: str) -> Optional[List[Dict[str, Any]]]:
    """Get cached search results."""
    cache = await get_redis_cache()
    import hashlib

    query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
    key = f"search:{query_hash}"
    return await cache.get(key)
