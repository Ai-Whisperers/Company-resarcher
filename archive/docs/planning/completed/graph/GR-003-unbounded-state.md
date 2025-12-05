# GR-003: Unbounded State Accumulation

## Priority: Critical

## Description

State objects grow without limit during workflow execution, eventually causing memory exhaustion.

## Location

- **File**: `src/graph/state.py`

## Recommended Fix

```python
class BoundedState:
    MAX_HISTORY_SIZE = 100

    def add_result(self, result):
        self.results.append(result)
        if len(self.results) > self.MAX_HISTORY_SIZE:
            self.results = self.results[-self.MAX_HISTORY_SIZE:]
```

## Impact

- **Severity**: High
- **Risk**: Memory exhaustion, OOM crashes
