# GR-004: No State Rollback on Failure

## Priority: Critical

## Description

When a node fails, there's no mechanism to rollback state to a consistent checkpoint.

## Location

- **File**: `src/graph/graph_builder.py`

## Recommended Fix

```python
class StatefulGraph:
    def __init__(self):
        self.checkpoints = []

    def checkpoint(self, state: dict):
        self.checkpoints.append(copy.deepcopy(state))

    def rollback(self) -> dict:
        if self.checkpoints:
            return self.checkpoints.pop()
        raise NoCheckpointError("No checkpoint to rollback to")
```

## Impact

- **Severity**: High
- **Risk**: Corrupted state, inconsistent results
