# GR-002: Race Conditions in State Updates

## Priority: Critical

## Description

Concurrent state updates in the graph can cause race conditions, leading to lost updates or corrupted state.

## Location

- **File**: `src/graph/state.py`
- **File**: `src/graph/graph_builder.py`

## Recommended Fix

```python
import asyncio

class StateManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._state = {}

    async def update(self, key: str, value: Any):
        async with self._lock:
            self._state[key] = value
```

## Impact

- **Severity**: High
- **Risk**: Data corruption, inconsistent results
