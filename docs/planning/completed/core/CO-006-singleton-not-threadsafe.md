# CO-006: Singleton Pattern Not Thread-Safe

## Priority: High

## Description

Singleton implementations in core modules are not thread-safe, similar to the agent factory issue.

## Location

- **File**: `src/core/config.py`
- **File**: `src/core/ai_client.py`

## Recommended Fix

```python
import threading

class Config:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

## Impact

- **Severity**: High
- **Risk**: Multiple instances, inconsistent state
