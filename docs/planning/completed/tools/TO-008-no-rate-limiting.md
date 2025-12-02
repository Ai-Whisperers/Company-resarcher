# TO-008: No Rate Limiting Implementation

## Status: COMPLETED

## Priority: High

## Description

Tools do not implement rate limiting for external API calls, risking API key bans and service disruption.

## Location

- **File**: `src/tools/*.py`

## Recommended Fix

```python
from asyncio import Semaphore
from ratelimit import limits, sleep_and_retry

class RateLimitedTool:
    def __init__(self, requests_per_minute: int = 60):
        self.semaphore = Semaphore(requests_per_minute)

    @sleep_and_retry
    @limits(calls=60, period=60)
    async def call_api(self, url: str):
        async with self.semaphore:
            return await self._request(url)
```

## Impact

- **Severity**: High
- **Risk**: API bans, service disruption

## Resolution

**Implemented**: 2024-11-28

Rate limiting infrastructure has been added:

1. **Existing**: `src/core/rate_limited_client.py` - Rate limiting for AI API calls using `aiolimiter`
2. **Existing**: `src/tools/browser.py` - Semaphore-based concurrency limiting (`max_concurrent=5`)
3. **New**: `src/core/rate_limiter.py` - Generic token bucket rate limiter with:
   - `TokenBucketRateLimiter` class for flexible rate limiting
   - `RateLimiterRegistry` singleton for managing multiple limiters
   - `@rate_limited` decorator for easy application to async functions

Tools can now use the rate limiter via:

```python
from src.core.rate_limiter import rate_limited

@rate_limited("api_name", rate=1.0, bucket_size=10)
async def call_api(self, ...):
    ...
```
