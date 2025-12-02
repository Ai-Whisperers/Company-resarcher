# BUG-009: Pipeline Context Swallowed Errors

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/pipeline/context.py:205` has a bare except without variable binding, silently swallowing errors.

## Current Code

```python
try:
    # operation
except Exception:
    pass  # Error completely lost!
```

## Implementation Tasks

- [ ] Bind exception to variable
- [ ] Add logging with context
- [ ] Determine if error should propagate
- [ ] Add error tracking
