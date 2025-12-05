# [RESOLVED] FEAT: Graph Persistence with Redis

**Status**: RESOLVED
**Original File**: backlog/03-features.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Move "Dead Letter Queue" and "Circuit Breaker" state from memory to Redis.

**Acceptance Criteria:**
- [x] Implement `RedisDeadLetterQueue`.
- [x] Implement `RedisCircuitBreaker`.
- [x] Update `GraphBuilder` to use these implementations if Redis is available.

## Resolution

Implemented Redis-backed persistence layer for circuit breakers and dead letter queues.

### Implementation Details

**File:** `src/core/redis_persistence.py`

#### RedisCircuitBreaker

Redis-backed circuit breaker with distributed state management:

```python
from src.core.redis_persistence import RedisCircuitBreaker, create_redis_circuit_breaker

# Create with factory (handles fallback gracefully)
breaker = create_redis_circuit_breaker(
    name="openai",
    redis_url="redis://localhost:6379",
    failure_threshold=5,
    recovery_timeout=60.0
)

# Use as decorator
@breaker
async def call_api():
    return await openai_client.generate(...)

# Or as context manager
async with breaker:
    result = await api_call()
```

Features:
- Distributed state across multiple instances
- Persists across restarts
- Local caching (1s TTL) for performance
- Same interface as in-memory CircuitBreaker
- Graceful fallback to None if Redis unavailable

Redis Keys:
- `circuit_breaker:{name}:state` - Current state (closed/open/half_open)
- `circuit_breaker:{name}:failures` - Failure counter
- `circuit_breaker:{name}:successes` - Success counter
- `circuit_breaker:{name}:last_failure` - Timestamp of last failure

#### RedisDeadLetterQueue

Redis-backed dead letter queue for failed messages:

```python
from src.core.redis_persistence import RedisDeadLetterQueue, DeadLetterEntry, create_redis_dlq

# Create DLQ
dlq = create_redis_dlq(
    redis_url="redis://localhost:6379",
    queue_name="research",
    max_entries=1000,
    ttl_seconds=604800  # 7 days
)

# Push failed entry
await dlq.push(DeadLetterEntry(
    id="msg-123",
    payload={"query": "company info", "company": "Acme Corp"},
    error="API timeout after 30s",
    error_type="TimeoutError",
    timestamp=time.time(),
    source="search_agent"
))

# Get all entries
entries = await dlq.get_all(limit=50)

# Retry with handler
await dlq.retry("msg-123", async_handler_func)

# Count entries
count = await dlq.count()
```

Features:
- Sorted by timestamp (newest first)
- Configurable max entries (auto-pruning)
- TTL support for automatic cleanup
- Retry mechanism with handler callback
- Full CRUD operations (push, pop, get, get_all, clear)

Redis Keys:
- `dlq:{queue_name}:list` - Sorted set of entry IDs by timestamp
- `dlq:{queue_name}:entries` - Hash map of entry ID -> JSON data

#### DeadLetterEntry

Data class for DLQ entries:

```python
@dataclass
class DeadLetterEntry:
    id: str              # Unique identifier
    payload: dict        # Original message payload
    error: str           # Error message
    error_type: str      # Exception type name
    timestamp: float     # When it failed
    retry_count: int     # Number of retry attempts
    source: str          # Component that failed
    metadata: dict       # Additional context
```

### Factory Functions

Graceful creation with fallback handling:

```python
# Returns None if Redis unavailable
breaker = create_redis_circuit_breaker("openai", redis_url="redis://localhost:6379")
dlq = create_redis_dlq(redis_url="redis://localhost:6379", queue_name="research")

# Check availability
if breaker:
    # Use Redis-backed breaker
else:
    # Fall back to in-memory breaker
    from src.core.circuit_breaker import CircuitBreaker
    breaker = CircuitBreaker("openai")
```

### Integration Example

```python
from src.core.redis_persistence import create_redis_circuit_breaker, create_redis_dlq
from src.core.circuit_breaker import CircuitBreaker

# Try Redis, fall back to in-memory
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

breaker = create_redis_circuit_breaker("search", redis_url) or CircuitBreaker("search")
dlq = create_redis_dlq(redis_url, "failed_searches")

@breaker
async def perform_search(query: str):
    try:
        return await search_api.search(query)
    except Exception as e:
        if dlq:
            await dlq.push(DeadLetterEntry(
                id=f"search-{uuid.uuid4()}",
                payload={"query": query},
                error=str(e),
                error_type=type(e).__name__,
                timestamp=time.time(),
            ))
        raise
```

### Configuration

```bash
# Environment variables
REDIS_URL=redis://localhost:6379
REDIS_DLQ_TTL=604800  # 7 days in seconds
REDIS_DLQ_MAX_ENTRIES=1000
```

## Files Created

- `src/core/redis_persistence.py` - Full implementation (~400 lines)

## Dependencies

Uses existing `redis>=5.0.0` dependency from `pyproject.toml`.
