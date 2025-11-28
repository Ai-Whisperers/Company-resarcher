# HIGH: Semaphore Initialization Race in Browser

## Issue #018
## Severity: 🟠 High
## Category: Concurrency
## File: `src/tools/browser.py:28-29`

## Problem

`_semaphore` initialized lazily without lock:

```python
@property
def semaphore(self) -> asyncio.Semaphore:
    if self._semaphore is None:
        self._semaphore = asyncio.Semaphore(self.max_concurrent)  # Race!
    return self._semaphore
```

## Impact

- Multiple semaphores created
- Rate limiting ineffective
- Resource exhaustion

## Solution

Initialize in `__init__()` or use lock:

```python
def __init__(self, max_concurrent: int = 5):
    self.max_concurrent = max_concurrent
    self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)
    self._browser: Optional[Browser] = None

# Or with lock for lazy init:
_semaphore_lock = asyncio.Lock()

@property
async def semaphore(self) -> asyncio.Semaphore:
    if self._semaphore is None:
        async with self._semaphore_lock:
            if self._semaphore is None:
                self._semaphore = asyncio.Semaphore(self.max_concurrent)
    return self._semaphore
```

## Testing

1. Spawn 100 concurrent browser requests
2. Verify max 5 concurrent
3. Monitor semaphore count
