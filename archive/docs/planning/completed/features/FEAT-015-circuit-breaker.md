# [RESOLVED] FEAT-015: Circuit Breaker Pattern

**Status**: RESOLVED
**Original File**: backlog/features/FEAT-015-circuit-breaker.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Low
**Description:** No circuit breaker pattern for external API calls.

**Acceptance Criteria:**
- [x] Implement circuit breaker for LLM calls
- [x] Implement for search API calls
- [x] Add circuit breaker configuration
- [x] Add circuit state metrics

## Resolution

Full circuit breaker implementation in `src/core/circuit_breaker.py` (399 lines).

### Implementation Details

**States:**
- `CLOSED` - Normal operation, requests pass through
- `OPEN` - Circuit tripped, requests fail immediately with `CircuitOpenError`
- `HALF_OPEN` - Testing recovery, limited requests allowed

**Classes:**
- `CircuitBreaker` - Main class with configurable thresholds
- `CircuitBreakerStats` - Metrics (success/failure rates, state changes)
- `CircuitBreakerRegistry` - Central registry for multiple breakers
- `CircuitOpenError` - Exception when circuit is open

### Configuration

```python
CircuitBreaker(
    name="openai",
    failure_threshold=5,      # Failures before opening
    recovery_timeout=60.0,    # Seconds before half-open
    success_threshold=2,      # Successes to close from half-open
    excluded_exceptions=(...) # Exceptions that don't count as failures
)
```

### Usage

**As Decorator:**
```python
from src.core.circuit_breaker import circuit_breaker

@circuit_breaker("openai")
async def call_openai():
    return await client.generate(...)
```

**As Context Manager:**
```python
breaker = CircuitBreaker("search")
async with breaker:
    result = await search_api.query(...)
```

**With Registry:**
```python
from src.core.circuit_breaker import get_circuit_registry

registry = get_circuit_registry()
breaker = registry.get_or_create("openai", failure_threshold=5)

# Get all stats
stats = registry.get_all_stats()
# Get open circuits
open_circuits = registry.get_open_circuits()
```

### Metrics Available

```python
stats = breaker.stats
{
    "total_requests": 100,
    "successful": 95,
    "failed": 5,
    "rejected": 3,
    "failure_rate": "5.0%",
    "state": "closed",
    "consecutive_failures": 0,
    "consecutive_successes": 10,
    "state_changes": 2
}
```

## Files

- `src/core/circuit_breaker.py` - Full implementation (399 lines)
