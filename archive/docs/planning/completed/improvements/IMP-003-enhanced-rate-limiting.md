# IMP-003: Enhanced Rate Limiting System

## Problem Statement

We risk getting banned by target sites if we crawl too fast. Simple fixed delays are often insufficient or inefficient.

## Proposed Solution

Implement a robust `RateLimiter` that supports:

- Base delay (randomized range)
- Max retries
- Exponential backoff on errors (429/503)
- Domain-specific limits

## Implementation Steps

1.  Create `RateLimiter` class.
2.  Implement `wait_for_domain(domain)` method.
3.  Integrate into the `Crawl4AITool` or `Dispatcher`.
4.  Handle `429 Too Many Requests` by increasing delay automatically.

## Code Example

```python
class RateLimiter:
    async def wait(self, domain):
        delay = random.uniform(*self.base_delay)
        await asyncio.sleep(delay)
```

## Acceptance Criteria

- [ ] No "429 Too Many Requests" errors during standard crawls.
- [ ] Crawling speed is optimized (not too slow, not too fast).
- [ ] Different domains are rate-limited independently.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/async_dispatcher.py`
