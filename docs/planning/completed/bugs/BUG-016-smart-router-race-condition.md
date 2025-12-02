# BUG-016: Smart Router Race Condition

## Priority: High
## Category: Bug
## Status: Backlog

## Summary

`src/core/smart_router.py:60-71` has counter reset logic that's not thread-safe, causing potential race conditions.

## Current Code

```python
def route_request(self):
    now = time.time()
    if now - self.reset_time > 60:
        self.counters = {}  # Race condition here!
        self.reset_time = now
    self.counters[key] = self.counters.get(key, 0) + 1
```

## Implementation Tasks

- [ ] Add threading.Lock around counter operations
- [ ] Use atomic counter operations
- [ ] Consider using collections.Counter with lock
- [ ] Add thread safety tests
