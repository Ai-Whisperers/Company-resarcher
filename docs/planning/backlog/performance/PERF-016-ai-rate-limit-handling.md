# PERF-016: Improved AI Rate Limit Handling

## Problem

When AI providers hit rate limits, the system falls back correctly but the circuit breaker recovery is slow, causing repeated failures and warnings.

## Evidence from Logs

```
22:22:51 - ai_client - WARNING - Provider groq failed: [groq] Rate limit exceeded
22:22:53 - ai_client - WARNING - Provider openai failed: [openai] Rate limit exceeded
22:22:53 - ai_client - WARNING - Provider gemini failed: [gemini] Rate limit exceeded
22:23:15 - ai_client - WARNING - Circuit open for groq, skipping (retry in 35.9s)
22:23:15 - ai_client - WARNING - Circuit open for openai, skipping (retry in 38.2s)
22:23:15 - ai_client - WARNING - Circuit open for gemini, skipping (retry in 38.5s)
```

All 3 fast providers (Groq, OpenAI, Gemini) hit rate limits simultaneously, leaving only Anthropic.

## Impact

- Research slows significantly when only 1 provider works
- Log spam with repeated circuit open warnings
- No proactive rate limit management

## Proposed Solution

### 1. Proactive Rate Limit Tracking

Track API usage and slow down before hitting limits:

```python
class RateLimitTracker:
    def __init__(self):
        self.request_counts: Dict[str, List[float]] = {}  # provider -> timestamps
        self.rate_limits = {
            "groq": {"requests_per_minute": 30, "requests_per_day": 1000},
            "openai": {"requests_per_minute": 60, "requests_per_day": 10000},
            "gemini": {"requests_per_minute": 60, "requests_per_day": 1500},
            "anthropic": {"requests_per_minute": 60, "requests_per_day": 10000},
        }

    def should_throttle(self, provider: str) -> bool:
        now = time.time()
        timestamps = self.request_counts.get(provider, [])

        # Count requests in last minute
        recent = [t for t in timestamps if now - t < 60]
        limit = self.rate_limits[provider]["requests_per_minute"]

        # Throttle if at 80% of limit
        return len(recent) >= limit * 0.8

    async def wait_if_needed(self, provider: str):
        if self.should_throttle(provider):
            logger.info(f"Throttling {provider} to avoid rate limit")
            await asyncio.sleep(5)
```

### 2. Balanced Provider Distribution

Distribute requests across providers instead of always trying Groq first:

```python
class BalancedProviderSelector:
    def __init__(self, providers: List[str]):
        self.providers = providers
        self.usage_counts: Dict[str, int] = {p: 0 for p in providers}

    def get_next_provider(self) -> str:
        """Get least-used provider that isn't rate-limited."""
        available = [p for p in self.providers if not self.is_limited(p)]
        if not available:
            return self.providers[0]  # Fallback

        return min(available, key=lambda p: self.usage_counts[p])
```

### 3. Quiet Circuit Breaker Logging

Reduce log spam when circuits are open:

```python
class QuietCircuitBreaker:
    def __init__(self):
        self._last_log_time: Dict[str, float] = {}
        self._log_interval = 60  # Log once per minute per circuit

    def should_log_skip(self, circuit_name: str) -> bool:
        now = time.time()
        last = self._last_log_time.get(circuit_name, 0)

        if now - last >= self._log_interval:
            self._last_log_time[circuit_name] = now
            return True
        return False
```

### 4. Rate Limit Recovery Strategy

When rate limited, calculate optimal wait time:

```python
def calculate_wait_time(self, provider: str, error: Exception) -> int:
    """Parse rate limit headers or estimate wait time."""
    # Try to extract from error message
    if "retry after" in str(error).lower():
        match = re.search(r'retry after (\d+)', str(error).lower())
        if match:
            return int(match.group(1))

    # Default backoff based on provider
    defaults = {
        "groq": 60,      # Groq has strict limits
        "openai": 30,
        "gemini": 30,
        "anthropic": 30,
    }
    return defaults.get(provider, 30)
```

## Files to Modify

- `src/core/ai_client.py`
- `src/core/circuit_breaker.py`
- New: `src/core/rate_limiter.py`

## Acceptance Criteria

- [ ] Proactive throttling before hitting rate limits
- [ ] Balanced distribution across providers
- [ ] Reduced log spam for circuit breaker states
- [ ] Smarter recovery timing based on rate limit headers
- [ ] Dashboard/log showing provider usage distribution

## Priority

**MEDIUM** - Improves reliability and reduces log noise.

## Estimate

3-4 hours implementation + testing
