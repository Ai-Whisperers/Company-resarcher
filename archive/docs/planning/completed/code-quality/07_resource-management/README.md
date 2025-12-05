# Resource Management Issues

> **Total Issues**: 15 (5 HIGH, 6 MEDIUM, 4 LOW)
> **Priority**: Phase 1 - Critical

## Overview

Resource management issues can cause memory leaks, connection pool exhaustion, and system instability. These are critical for production reliability.

## Issues Summary

### HIGH Severity (5)

| ID | File | Line | Description |
|----|------|------|-------------|
| CQ-100 | browser/tool.py | 281-317 | fetch_multiple() tasks not cancelled |
| CQ-101 | api/app.py | 353 | SessionLocal() not closed in error paths |
| CQ-102 | api/database.py | 52 | check_db_health() session never closed |
| CQ-103 | agents/base_agent.py | 178-247 | seen_urls set never cleared |
| CQ-104 | data/content/crawler.py | 413-430 | Partial initialization on exception |

### MEDIUM Severity (6)

| ID | File | Line | Description |
|----|------|------|-------------|
| CQ-105 | cache/file_cache.py | 117-120 | Lock released before write |
| CQ-106 | config/api_limits.py | 621 | LRU cache clear unsynchronized |
| CQ-107 | search/manager.py | 707-710 | Unbounded queues |
| CQ-108 | browser/manager.py | 83-124 | Playwright cleanup not guaranteed |
| CQ-109 | pipeline/orchestrator.py | 322-409 | Tools without context manager |
| CQ-110 | data/content/crawler.py | 351 | asyncio.to_thread no timeout |

### LOW Severity (4)

| ID | File | Description |
|----|------|-------------|
| CQ-111 | browser/extractor.py | Selector cache read not locked |
| CQ-112 | agents/specialists.py | Sequential async instead of gather |
| CQ-113 | Various | Missing cleanup in exception paths |
| CQ-114 | Various | No maximum size for in-memory caches |

## Resource Management Fixes

### CQ-100: Task Cancellation in fetch_multiple()

**Problem**: Tasks not cancelled on failure
```python
# BAD
async def fetch_multiple(self, urls: List[str]) -> List[Result]:
    tasks = [self.fetch(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # If one fails, others may still be running and holding resources
    return results
```

**Solution**: Proper task cleanup
```python
# GOOD
async def fetch_multiple(self, urls: List[str]) -> List[Result]:
    tasks = [asyncio.create_task(self.fetch(url)) for url in urls]
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    except Exception:
        # Cancel any still-running tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for cancellations to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
```

### CQ-101/102: Database Session Cleanup

**Problem**: Sessions not closed in all paths
```python
# BAD
def run_research_task(...):
    db = SessionLocal()
    try:
        # ... work ...
    except Exception:
        # Session not closed on exception!
        raise
    finally:
        db.close()  # May not run if exception before finally
```

**Solution**: Use context manager
```python
# GOOD
from contextlib import contextmanager

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def run_research_task(...):
    with get_session() as db:
        # ... work ...
        # Session always closed
```

### CQ-103: Unbounded Set Growth

**Problem**: Set grows without bound
```python
# BAD
class BaseAgent:
    def __init__(self):
        self.seen_urls = set()  # Never cleared!

    async def _gather_data(self, query):
        # Adds to seen_urls but never removes
        self.seen_urls.add(url)
```

**Solution**: Use bounded cache
```python
# GOOD
from collections import OrderedDict

class LRUSet:
    def __init__(self, maxsize=1000):
        self._data = OrderedDict()
        self._maxsize = maxsize

    def add(self, item):
        if item in self._data:
            self._data.move_to_end(item)
        else:
            self._data[item] = None
            if len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def __contains__(self, item):
        return item in self._data

class BaseAgent:
    def __init__(self):
        self.seen_urls = LRUSet(maxsize=1000)
```

### CQ-108: Playwright Cleanup

**Problem**: Cleanup not guaranteed
```python
# BAD
async def start(self):
    self._playwright = await async_playwright().start()
    try:
        self._browser = await self._playwright.chromium.launch()
    except Exception:
        # Playwright not cleaned up!
        raise
```

**Solution**: Use async context manager
```python
# GOOD
class BrowserManager:
    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.launch()
            return self
        except Exception:
            await self._playwright.stop()
            raise

    async def __aexit__(self, *args):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
```

### CQ-107: Bounded Queues

**Problem**: Unbounded queue growth
```python
# BAD
query_queue = asyncio.Queue()  # Unbounded!
```

**Solution**: Set maximum size
```python
# GOOD
MAX_QUEUE_SIZE = 1000
query_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

# Handle queue full
try:
    await asyncio.wait_for(
        query_queue.put(item),
        timeout=5.0
    )
except asyncio.TimeoutError:
    logger.warning("Queue full, dropping item")
```

## Verification Checklist

- [ ] All async tasks are cancelled on failure
- [ ] Database sessions use context managers
- [ ] In-memory caches have maximum sizes
- [ ] Playwright uses async context manager
- [ ] Queues have maximum sizes
- [ ] All resources have explicit cleanup paths
- [ ] Timeout on all resource acquisition
