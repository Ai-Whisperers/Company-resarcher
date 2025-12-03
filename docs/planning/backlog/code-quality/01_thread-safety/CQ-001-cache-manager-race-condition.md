# CQ-001: Cache Manager Double-Checked Locking Race Condition

## Metadata
- **Severity**: HIGH
- **Category**: Thread Safety
- **File**: [src/core/cache/manager.py](src/core/cache/manager.py#L37-L54)
- **Lines**: 37-54
- **Effort**: M
- **Status**: Open

## Problem

The CacheManager singleton implementation has a race condition in its double-checked locking pattern. The `_initialized` flag is checked outside the lock, allowing multiple threads to potentially bypass the initialization lock.

## Current Code

```python
class CacheManager:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:  # Check outside lock - RACE CONDITION
            return
        with self._lock:
            if self._initialized:
                return
            # ... initialization code ...
            self._initialized = True
```

## Why This Is a Problem

1. Thread A checks `_initialized` (False), enters lock
2. Thread B checks `_initialized` (False), waits on lock
3. Thread A completes init, sets `_initialized = True`, releases lock
4. Thread B acquires lock, checks `_initialized` (True), returns
5. BUT: If Thread B checked `_initialized` just as Thread A was writing to it, memory visibility issues could cause Thread B to see stale value

In Python, this is less critical due to the GIL, but:
- Code may be ported to a GIL-free implementation
- Bad pattern that should be fixed for correctness
- Other parts of initialization may have issues

## Solution

Use proper double-checked locking with the check INSIDE the lock, or use a simpler pattern:

```python
class CacheManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._do_init()  # Initialize in __new__
                    cls._instance = instance
        return cls._instance

    def _do_init(self):
        """Perform initialization. Called exactly once."""
        self._memory_cache = {}
        self._file_cache = None
        self._redis_cache = None
        # ... rest of initialization ...

    def __init__(self):
        pass  # No-op, all init done in __new__
```

Or use a module-level singleton:

```python
# cache/manager.py
import threading
from functools import lru_cache

class CacheManager:
    def __init__(self):
        self._memory_cache = {}
        # ... initialization ...

@lru_cache(maxsize=1)
def get_cache_manager() -> CacheManager:
    """Get the singleton CacheManager instance."""
    return CacheManager()
```

## Testing

1. Write concurrent test with multiple threads calling `CacheManager()`
2. Verify only one initialization occurs
3. Verify all threads get same instance

```python
import threading
import time

def test_cache_manager_thread_safety():
    instances = []
    init_count = [0]
    original_init = CacheManager._do_init

    def counting_init(self):
        init_count[0] += 1
        time.sleep(0.01)  # Simulate slow init
        original_init(self)

    CacheManager._do_init = counting_init

    def get_instance():
        instances.append(CacheManager())

    threads = [threading.Thread(target=get_instance) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert init_count[0] == 1, f"Init called {init_count[0]} times"
    assert len(set(id(i) for i in instances)) == 1, "Multiple instances created"
```

## Related Issues

- CQ-002: Similar pattern in rate_limiting.py
- CQ-060: Duplicate singleton patterns should be unified
