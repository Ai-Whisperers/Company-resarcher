# Thread Safety Issues

> **Total Issues**: 16 (8 HIGH, 6 MEDIUM, 2 LOW)
> **Fixed**: 1 (CQ-001)
> **Priority**: Phase 1 - Critical

## Overview

Thread safety issues can cause data corruption, race conditions, and unpredictable behavior in concurrent environments. These are critical to fix for production stability.

## Issues Summary

### HIGH Severity (8)

| ID | File | Description |
|----|------|-------------|
| ~~CQ-001~~ | ~~cache/manager.py~~ | ~~Double-checked locking race condition~~ ✅ |
| CQ-002 | resilience/rate_limiting.py | Unprotected class variables |
| CQ-003 | tools/__init__.py | Non-atomic reset across locks |
| CQ-004 | api/app.py | _running_tasks dict without locks |
| CQ-005 | graph/graph_builder.py | CircuitBreaker state unsynchronized |
| CQ-006 | search/manager.py | ProviderHealth non-atomic mutation |
| CQ-007 | pipeline/pipeline.py | _checkpoints accessed without sync |
| CQ-008 | graph/state.py | asyncio.Lock in sync context |

### MEDIUM Severity (6)

| ID | File | Description |
|----|------|-------------|
| CQ-009 | cache/file_cache.py | Lock released before write |
| CQ-010 | config/api_limits.py | LRU cache clear unsynchronized |
| CQ-011 | search/manager.py | Unbounded queues |
| CQ-012 | browser/manager.py | Playwright cleanup not guaranteed |
| CQ-013 | pipeline/orchestrator.py | Tools without context manager |
| CQ-014 | data/content/crawler.py | asyncio.to_thread no timeout |

### LOW Severity (2)

| ID | File | Description |
|----|------|-------------|
| CQ-015 | browser/extractor.py | Selector cache read not locked |
| CQ-016 | pipeline/smart_parallel_executor.py | CancelledError caught silently |

## Common Patterns to Fix

### 1. Singleton Pattern Fix
```python
# BAD: Race condition
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:  # Check outside lock
            cls._instance = super().__new__(cls)
        return cls._instance

# GOOD: Thread-safe singleton
import threading

class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check inside lock
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. Mutable Class Variables Fix
```python
# BAD: Shared mutable state
class RateLimiter:
    _limiters = {}  # Shared across instances!

# GOOD: Instance-level or protected
class RateLimiter:
    def __init__(self):
        self._limiters = {}
        self._lock = threading.Lock()

    def get_limiter(self, name):
        with self._lock:
            return self._limiters.get(name)
```

## Verification Checklist

- [ ] All singletons use proper double-checked locking
- [ ] Mutable class variables are protected with locks
- [ ] async operations have proper synchronization
- [ ] Resource cleanup is guaranteed with context managers
