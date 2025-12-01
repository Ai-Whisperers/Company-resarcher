# BUG-017: Cache Double-Checked Locking Issue

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/cache.py:22-40` uses double-checked locking pattern without proper volatile semantics, potentially causing visibility issues.

## Current Code

```python
class AICache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:  # First check without lock
            with cls._lock:
                if cls._instance is None:  # Second check with lock
                    cls._instance = super().__new__(cls)
        return cls._instance
```

## Issue

In Python, this is generally safe due to GIL, but the pattern is fragile and may break with future Python changes.

## Implementation Tasks

- [ ] Document thread-safety assumptions
- [ ] Consider using `threading.local()` for thread-local cache
- [ ] Or use dependency injection instead of singleton
- [ ] Add thread safety tests
