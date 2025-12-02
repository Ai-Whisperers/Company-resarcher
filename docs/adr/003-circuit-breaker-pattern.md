# ADR-003: Circuit Breaker Pattern for External Services

## Status

Accepted

## Context

External services (AI providers, search engines, websites) can fail in various ways:
- **Timeouts:** Slow responses that waste time
- **Rate limits:** 429 errors requiring backoff
- **Outages:** Service completely unavailable
- **Errors:** Invalid responses, server errors

Without protection, these failures can:
- Cascade through the system
- Waste resources on doomed requests
- Degrade user experience with long waits

## Decision

We implemented the **Circuit Breaker pattern** with three states:

```
CLOSED ──(failures >= threshold)──> OPEN
   ▲                                  │
   │                                  │
   └──(successes >= threshold)── HALF_OPEN ◄──(timeout elapsed)
```

**Implementation details:**

1. **CircuitBreaker class:** Tracks state and manages transitions
   - Configurable failure threshold (default: 5)
   - Recovery timeout (default: 60s)
   - Success threshold for recovery (default: 2)

2. **Per-provider breakers:** Each AI provider has its own circuit
   - Prevents one provider's issues from blocking others
   - Enables independent recovery

3. **Integration points:**
   - AI client wraps all calls with circuit breaker
   - Fallback to next provider when circuit opens

## Consequences

### Positive

- **Fail fast:** No waiting for doomed requests
- **Resource protection:** Don't overwhelm failing services
- **Automatic recovery:** System heals without intervention
- **Visibility:** Circuit state is observable

### Negative

- **Complexity:** Additional state to manage
- **False positives:** Good requests may be blocked during recovery
- **Tuning required:** Thresholds need adjustment per service

### Neutral

- Circuit state is not persisted across restarts
- Statistics available via `/health/detailed`

## References

- `src/core/circuit_breaker.py` - Implementation
- `src/core/ai_client.py` - Integration with AI providers
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
