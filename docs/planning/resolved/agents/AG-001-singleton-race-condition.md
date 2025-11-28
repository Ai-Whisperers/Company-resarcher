# AG-001: Race Condition in AgentFactory Singleton

## Status: COMPLETED

> **Resolution**: The race condition has been fixed using double-checked locking pattern with `threading.Lock()` in `src/agents/orchestrator.py`. The actual singleton was in `get_orchestrator()`, not in `AgentFactory` (which doesn't use singleton pattern).
>
> **Fixed in**: `src/agents/orchestrator.py`
> **Date**: 2024-11-28

---

## Original Description (for reference)

## Priority: Critical

## Description

The `AgentFactory` class implements a singleton pattern that is not thread-safe. When multiple threads attempt to create agents simultaneously, race conditions can occur leading to:
- Multiple factory instances being created
- Inconsistent agent configurations
- Memory leaks from orphaned instances

## Location

- **File**: `src/agents/orchestrator.py` (corrected location)
- **Lines**: `get_orchestrator()` function

## Current Code Pattern

```python
class AgentFactory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## Problem

The check `if cls._instance is None` and the subsequent assignment are not atomic. In a multi-threaded environment:

1. Thread A checks `_instance is None` → True
2. Thread B checks `_instance is None` → True (before A assigns)
3. Both threads create new instances
4. One instance is lost, potentially with initialized resources

## Recommended Fix

```python
import threading

class AgentFactory:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

## Impact

- **Severity**: High
- **Frequency**: Intermittent (depends on concurrent usage)
- **Affected Components**: All agent creation, research workflows

## Testing Requirements

- Unit test with concurrent agent creation
- Stress test with multiple threads
- Verify single instance under load

## Related Issues

- [AG-010](AG-010-global-state-mutation.md) - Global state mutation
- [CO-006](../core/CO-006-singleton-not-threadsafe.md) - Similar issue in core module
