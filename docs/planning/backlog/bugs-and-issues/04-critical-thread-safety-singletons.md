# CRITICAL: Thread Safety Issues in Singletons

## Severity: Critical
## File: `src/tools/__init__.py` (lines 11-37)

## Problem

The singleton pattern used is not thread-safe:

```python
_search_tool_instance = None

def get_shared_search_tool() -> SearchTool:
    global _search_tool_instance
    if _search_tool_instance is None:
        _search_tool_instance = SearchTool()
    return _search_tool_instance
```

## Impact

Race condition when multiple threads/async tasks call simultaneously:
1. Thread A checks `_search_tool_instance is None` -> True
2. Thread B checks `_search_tool_instance is None` -> True
3. Thread A creates instance
4. Thread B creates another instance
5. Multiple tool instances exist, defeating singleton purpose

This can cause:
- Resource duplication
- State inconsistencies
- Memory leaks

## Solution

Use thread-safe singleton with locking:

```python
import threading

_search_tool_instance = None
_search_tool_lock = threading.Lock()

def get_shared_search_tool() -> SearchTool:
    global _search_tool_instance
    if _search_tool_instance is None:
        with _search_tool_lock:
            if _search_tool_instance is None:  # Double-check
                _search_tool_instance = SearchTool()
    return _search_tool_instance
```

Or use `functools.lru_cache`:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_shared_search_tool() -> SearchTool:
    return SearchTool()
```

## Testing

After fix:
1. Run concurrent calls to `get_shared_search_tool()`
2. Verify only one instance created
3. Verify same instance returned to all callers
