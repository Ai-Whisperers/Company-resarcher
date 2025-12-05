"""
Redis-backed persistence for circuit breakers and dead letter queues.

This module provides Redis implementations for distributed/persistent state management,
allowing circuit breaker state and failed messages to survive restarts and be shared
across multiple instances.

Example:
    # Use Redis circuit breaker
    breaker = RedisCircuitBreaker(
        name="openai",
        redis_client=redis.Redis(),
        failure_threshold=5
    )

    # Use Redis dead letter queue
    dlq = RedisDeadLetterQueue(redis_client=redis.Redis())
    await dlq.push(failed_message)
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, TypeVar, ParamSpec
from functools import wraps

from src.infrastructure.logging import setup_logger
from src.infrastructure.resilience.circuit_breaker import CircuitState, CircuitOpenError, CircuitBreakerStats

logger = setup_logger("redis_persistence")

P = ParamSpec("P")
T = TypeVar("T")


# =============================================================================
# Redis Circuit Breaker
# =============================================================================


@dataclass
class RedisCircuitBreaker:
    """
    Redis-backed circuit breaker for distributed state management.

    Stores circuit state in Redis, allowing multiple instances to share
    circuit breaker state and persist across restarts.

    Args:
        name: Identifier for this circuit
        redis_client: Redis client instance (sync or async)
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds to wait before half-open
        success_threshold: Successes needed to close from half-open
        key_prefix: Redis key prefix for namespacing

    Example:
        import redis
        client = redis.Redis(host='localhost', port=6379)
        breaker = RedisCircuitBreaker("openai", client)

        @breaker
        async def call_api():
            ...
    """

    name: str
    redis_client: Any  # redis.Redis or redis.asyncio.Redis
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    key_prefix: str = "circuit_breaker"
    excluded_exceptions: tuple[type[Exception], ...] = field(default_factory=tuple)

    # Local cache for performance (avoid Redis roundtrip on every check)
    _local_state: Optional[CircuitState] = field(default=None, init=False)
    _local_state_time: float = field(default=0.0, init=False)
    _cache_ttl: float = field(default=1.0, init=False)  # Cache for 1 second

    def __post_init__(self):
        """Initialize Redis keys."""
        self._state_key = f"{self.key_prefix}:{self.name}:state"
        self._failures_key = f"{self.key_prefix}:{self.name}:failures"
        self._successes_key = f"{self.key_prefix}:{self.name}:successes"
        self._last_failure_key = f"{self.key_prefix}:{self.name}:last_failure"
        self._stats_key = f"{self.key_prefix}:{self.name}:stats"

    def _get_redis_value(self, key: str) -> Optional[str]:
        """Get value from Redis (sync)."""
        try:
            value = self.redis_client.get(key)
            if value:
                return value.decode() if isinstance(value, bytes) else value
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            return None

    def _set_redis_value(self, key: str, value: str, ex: Optional[int] = None) -> None:
        """Set value in Redis (sync)."""
        try:
            self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")

    def _incr_redis(self, key: str) -> int:
        """Increment counter in Redis."""
        try:
            return self.redis_client.incr(key)
        except Exception as e:
            logger.warning(f"Redis incr failed for {key}: {e}")
            return 0

    def _reset_redis_counter(self, key: str) -> None:
        """Reset counter to 0."""
        try:
            self.redis_client.set(key, "0")
        except Exception as e:
            logger.warning(f"Redis reset failed for {key}: {e}")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state from Redis."""
        # Check local cache first
        now = time.monotonic()
        if self._local_state and (now - self._local_state_time) < self._cache_ttl:
            return self._local_state

        state_str = self._get_redis_value(self._state_key)
        if state_str:
            try:
                self._local_state = CircuitState(state_str)
            except ValueError:
                self._local_state = CircuitState.CLOSED
        else:
            self._local_state = CircuitState.CLOSED

        self._local_state_time = now
        return self._local_state

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state."""
        old_state = self.state
        if old_state != new_state:
            self._set_redis_value(self._state_key, new_state.value)
            self._local_state = new_state
            self._local_state_time = time.monotonic()
            logger.info(
                f"Circuit '{self.name}' transitioned: {old_state.value} -> {new_state.value}"
            )

    def _get_last_failure_time(self) -> Optional[float]:
        """Get last failure timestamp."""
        value = self._get_redis_value(self._last_failure_key)
        return float(value) if value else None

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            return True

        if current_state == CircuitState.OPEN:
            last_failure = self._get_last_failure_time()
            if last_failure:
                elapsed = time.time() - last_failure
                if elapsed >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._reset_redis_counter(self._successes_key)
                    return True
            return False

        # HALF_OPEN: allow limited requests
        return True

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        return self._should_allow_request()

    def time_until_retry(self) -> float:
        """Seconds until circuit might allow requests again."""
        if self.state != CircuitState.OPEN:
            return 0.0

        last_failure = self._get_last_failure_time()
        if not last_failure:
            return 0.0

        elapsed = time.time() - last_failure
        remaining = self.recovery_timeout - elapsed
        return max(0.0, remaining)

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        if not self._should_allow_request():
            retry_after = self.time_until_retry()
            raise CircuitOpenError(self.name, retry_after)

    def record_success(self) -> None:
        """Record a successful request."""
        self._reset_redis_counter(self._failures_key)
        success_count = self._incr_redis(self._successes_key)

        if self.state == CircuitState.HALF_OPEN:
            if success_count >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                logger.info(f"Circuit '{self.name}' recovered after {success_count} successes")

    def record_failure(self, exception: Optional[Exception] = None) -> None:
        """Record a failed request."""
        if exception and isinstance(exception, self.excluded_exceptions):
            return

        # Update last failure time
        self._set_redis_value(self._last_failure_key, str(time.time()))
        self._reset_redis_counter(self._successes_key)
        failure_count = self._incr_redis(self._failures_key)

        current_state = self.state

        if current_state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
            logger.warning(f"Circuit '{self.name}' reopened after failure in half-open state")

        elif current_state == CircuitState.CLOSED:
            if failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.warning(f"Circuit '{self.name}' opened after {failure_count} failures")

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._set_redis_value(self._state_key, CircuitState.CLOSED.value)
        self._reset_redis_counter(self._failures_key)
        self._reset_redis_counter(self._successes_key)
        self.redis_client.delete(self._last_failure_key)
        self._local_state = CircuitState.CLOSED
        self._local_state_time = time.monotonic()
        logger.info(f"Circuit '{self.name}' manually reset")

    async def __aenter__(self) -> "RedisCircuitBreaker":
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Async context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure(exc_val)
        return False

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        """Use as decorator for async functions."""

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            async with self:
                return await func(*args, **kwargs)

        return wrapper


# =============================================================================
# Redis Dead Letter Queue
# =============================================================================


@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue."""

    id: str
    payload: dict[str, Any]
    error: str
    error_type: str
    timestamp: float
    retry_count: int = 0
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "payload": self.payload,
            "error": self.error,
            "error_type": self.error_type,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeadLetterEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            payload=data["payload"],
            error=data["error"],
            error_type=data["error_type"],
            timestamp=data["timestamp"],
            retry_count=data.get("retry_count", 0),
            source=data.get("source", "unknown"),
            metadata=data.get("metadata", {}),
        )


class RedisDeadLetterQueue:
    """
    Redis-backed dead letter queue for failed messages.

    Stores failed messages in Redis for later inspection, retry, or manual handling.
    Supports TTL for automatic expiration of old entries.

    Args:
        redis_client: Redis client instance
        queue_name: Name of the queue
        key_prefix: Redis key prefix
        max_entries: Maximum entries to keep (oldest removed first)
        ttl_seconds: TTL for entries (None for no expiration)

    Example:
        dlq = RedisDeadLetterQueue(redis_client, queue_name="research")

        # Add failed message
        await dlq.push(DeadLetterEntry(
            id="msg-123",
            payload={"query": "company info"},
            error="API timeout",
            error_type="TimeoutError",
            timestamp=time.time(),
        ))

        # Get all entries
        entries = await dlq.get_all()

        # Retry an entry
        entry = await dlq.pop("msg-123")
    """

    def __init__(
        self,
        redis_client: Any,
        queue_name: str = "default",
        key_prefix: str = "dlq",
        max_entries: int = 1000,
        ttl_seconds: Optional[int] = 86400 * 7,  # 7 days default
    ):
        self.redis_client = redis_client
        self.queue_name = queue_name
        self.key_prefix = key_prefix
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._list_key = f"{key_prefix}:{queue_name}:list"
        self._hash_key = f"{key_prefix}:{queue_name}:entries"

    async def push(self, entry: DeadLetterEntry) -> None:
        """Add entry to the dead letter queue."""
        try:
            # Store entry data in hash
            entry_json = json.dumps(entry.to_dict())
            self.redis_client.hset(self._hash_key, entry.id, entry_json)

            # Add to sorted set with timestamp for ordering
            self.redis_client.zadd(self._list_key, {entry.id: entry.timestamp})

            # Trim to max entries (remove oldest)
            current_count = self.redis_client.zcard(self._list_key)
            if current_count > self.max_entries:
                remove_count = current_count - self.max_entries
                oldest_ids = self.redis_client.zrange(self._list_key, 0, remove_count - 1)
                if oldest_ids:
                    self.redis_client.zrem(self._list_key, *oldest_ids)
                    self.redis_client.hdel(self._hash_key, *oldest_ids)

            # Set TTL on hash key if specified
            if self.ttl_seconds:
                self.redis_client.expire(self._hash_key, self.ttl_seconds)
                self.redis_client.expire(self._list_key, self.ttl_seconds)

            logger.debug(f"Added entry {entry.id} to DLQ {self.queue_name}")

        except Exception as e:
            logger.error(f"Failed to push to DLQ: {e}")

    async def pop(self, entry_id: str) -> Optional[DeadLetterEntry]:
        """Remove and return an entry by ID."""
        try:
            entry_json = self.redis_client.hget(self._hash_key, entry_id)
            if entry_json:
                entry_data = json.loads(
                    entry_json.decode() if isinstance(entry_json, bytes) else entry_json
                )
                self.redis_client.hdel(self._hash_key, entry_id)
                self.redis_client.zrem(self._list_key, entry_id)
                return DeadLetterEntry.from_dict(entry_data)
            return None
        except Exception as e:
            logger.error(f"Failed to pop from DLQ: {e}")
            return None

    async def get(self, entry_id: str) -> Optional[DeadLetterEntry]:
        """Get entry by ID without removing."""
        try:
            entry_json = self.redis_client.hget(self._hash_key, entry_id)
            if entry_json:
                entry_data = json.loads(
                    entry_json.decode() if isinstance(entry_json, bytes) else entry_json
                )
                return DeadLetterEntry.from_dict(entry_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get from DLQ: {e}")
            return None

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DeadLetterEntry]:
        """Get all entries, ordered by timestamp (newest first)."""
        try:
            # Get IDs from sorted set (reverse order for newest first)
            ids = self.redis_client.zrevrange(
                self._list_key, offset, offset + limit - 1
            )

            if not ids:
                return []

            # Get all entry data
            entries = []
            for entry_id in ids:
                entry_id_str = (
                    entry_id.decode() if isinstance(entry_id, bytes) else entry_id
                )
                entry = await self.get(entry_id_str)
                if entry:
                    entries.append(entry)

            return entries

        except Exception as e:
            logger.error(f"Failed to get all from DLQ: {e}")
            return []

    async def count(self) -> int:
        """Get number of entries in queue."""
        try:
            return self.redis_client.zcard(self._list_key)
        except Exception as e:
            logger.error(f"Failed to count DLQ: {e}")
            return 0

    async def clear(self) -> int:
        """Clear all entries from queue. Returns number cleared."""
        try:
            count = await self.count()
            self.redis_client.delete(self._list_key)
            self.redis_client.delete(self._hash_key)
            logger.info(f"Cleared {count} entries from DLQ {self.queue_name}")
            return count
        except Exception as e:
            logger.error(f"Failed to clear DLQ: {e}")
            return 0

    async def retry(
        self,
        entry_id: str,
        handler: Callable[[DeadLetterEntry], Any],
    ) -> bool:
        """
        Retry processing an entry.

        Args:
            entry_id: ID of entry to retry
            handler: Async function to process the entry

        Returns:
            True if retry succeeded, False otherwise
        """
        entry = await self.pop(entry_id)
        if not entry:
            return False

        try:
            entry.retry_count += 1
            await handler(entry)
            logger.info(f"Successfully retried DLQ entry {entry_id}")
            return True
        except Exception as e:
            # Put back in queue with incremented retry count
            entry.error = str(e)
            entry.error_type = type(e).__name__
            entry.timestamp = time.time()
            await self.push(entry)
            logger.warning(f"Retry failed for DLQ entry {entry_id}: {e}")
            return False


# =============================================================================
# Factory Functions
# =============================================================================


def create_redis_circuit_breaker(
    name: str,
    redis_url: str = "redis://localhost:6379",
    **kwargs,
) -> Optional[RedisCircuitBreaker]:
    """
    Create a Redis circuit breaker if Redis is available.

    Falls back to None if Redis connection fails.

    Args:
        name: Circuit breaker name
        redis_url: Redis connection URL
        **kwargs: Additional CircuitBreaker arguments

    Returns:
        RedisCircuitBreaker or None if Redis unavailable
    """
    try:
        import redis

        client = redis.from_url(redis_url)
        client.ping()  # Test connection
        return RedisCircuitBreaker(name=name, redis_client=client, **kwargs)
    except ImportError:
        logger.warning("redis package not installed, falling back to in-memory")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}, falling back to in-memory")
        return None


def create_redis_dlq(
    redis_url: str = "redis://localhost:6379",
    queue_name: str = "default",
    **kwargs,
) -> Optional[RedisDeadLetterQueue]:
    """
    Create a Redis dead letter queue if Redis is available.

    Args:
        redis_url: Redis connection URL
        queue_name: Queue name
        **kwargs: Additional DLQ arguments

    Returns:
        RedisDeadLetterQueue or None if Redis unavailable
    """
    try:
        import redis

        client = redis.from_url(redis_url)
        client.ping()
        return RedisDeadLetterQueue(redis_client=client, queue_name=queue_name, **kwargs)
    except ImportError:
        logger.warning("redis package not installed")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        return None


__all__ = [
    "RedisCircuitBreaker",
    "RedisDeadLetterQueue",
    "DeadLetterEntry",
    "create_redis_circuit_breaker",
    "create_redis_dlq",
]
