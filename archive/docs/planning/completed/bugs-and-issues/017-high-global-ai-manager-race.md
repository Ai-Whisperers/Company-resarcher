# HIGH: Race Condition in Global AI Manager

## Issue #017
## Severity: 🟠 High
## Category: Concurrency
## File: `src/core/ai_client.py:437`

## Problem

Global `_ai_manager` accessed without locks:

```python
_ai_manager: Optional[AIClientManager] = None

def get_ai_manager() -> AIClientManager:
    global _ai_manager
    if _ai_manager is None:  # Race condition!
        _ai_manager = AIClientManager()
    return _ai_manager
```

## Impact

- Multiple managers created in concurrent access
- Inconsistent state
- Resource waste

## Solution

Use thread-safe singleton:

```python
import threading

_ai_manager: Optional[AIClientManager] = None
_ai_manager_lock = threading.Lock()

def get_ai_manager() -> AIClientManager:
    global _ai_manager
    if _ai_manager is None:
        with _ai_manager_lock:
            if _ai_manager is None:
                _ai_manager = AIClientManager()
    return _ai_manager
```

## Testing

1. Spawn 100 concurrent get_ai_manager() calls
2. Verify single instance created
3. Verify same instance returned to all
