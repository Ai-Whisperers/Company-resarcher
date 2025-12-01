# ARCH-005: Reliability & Error Handling Patterns

## Priority: High

## Category: Architecture / Reliability

## Status: Backlog

## Summary

Implement robust error handling patterns to ensure system resilience under failure conditions.

## Problem Areas

| Issue | Impact |
|-------|--------|
| No circuit breaker | Cascading failures from external services |
| Basic retry logic | Doesn't handle all failure modes |
| Missing error taxonomy | Inconsistent error handling |
| No graceful degradation | Single failure crashes pipeline |

## Implementation Tasks

### A. Circuit Breaker Pattern

- [ ] Create `src/core/circuit_breaker.py`
- [ ] Implement `CircuitState` enum (CLOSED, OPEN, HALF_OPEN)
- [ ] Add failure threshold configuration (default: 5)
- [ ] Implement recovery timeout (default: 60s)
- [ ] Create decorator for easy wrapping
- [ ] Add metrics for circuit state changes

```python
class CircuitBreaker:
    async def call(self, func: callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit breaker is open")
        # ... execution logic
```

### B. Enhanced Retry Strategy

- [ ] Create `src/core/retry_strategy.py`
- [ ] Implement exponential backoff with jitter
- [ ] Add per-exception-type retry policies
- [ ] Support retry budgets (max attempts + max time)
- [ ] Log retry attempts for debugging
- [ ] Handle transient vs permanent failures

### C. Graceful Degradation

- [ ] Implement fallback data sources per agent
- [ ] Continue pipeline when single agent fails
- [ ] Mark sections as "unavailable" vs failing entirely
- [ ] Provide partial results with quality indicators
- [ ] Alert on degraded operation mode

### D. Timeout Budget Management

- [ ] Create `src/core/timeout_budget.py`
- [ ] Track remaining time across pipeline stages
- [ ] Allocate budgets based on stage priority
- [ ] Raise `TimeoutBudgetExhaustedError` appropriately
- [ ] Allow budget extension for critical paths

## Related: Exception Hierarchy (ARCH-002)

Already implemented in `src/core/exceptions.py`:
- `CompanyResearcherError` (base)
- `AIError`, `NetworkError`, `ValidationError`, etc.

New exceptions to add:
- [ ] `CircuitOpenError`
- [ ] `TimeoutBudgetExhaustedError`
- [ ] `PartialResultError`

## Acceptance Criteria

- [ ] Circuit breaker prevents cascading failures
- [ ] System survives any single external service outage
- [ ] Retry logic handles rate limits gracefully
- [ ] Partial results returned when full results impossible
- [ ] All failure modes logged with context

## Technical Notes

- Integrate circuit breaker with search providers, AI clients
- Consider per-provider circuit breakers
- Use existing `AIRateLimitError.retry_after` for backoff hints
