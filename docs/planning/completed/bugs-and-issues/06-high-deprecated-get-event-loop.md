# FIXED: Deprecated `asyncio.get_event_loop()`

## Status: COMPLETED
## Severity: High
## File: `src/tools/search.py`

## Problem

Using deprecated `asyncio.get_event_loop()` which emits warnings in Python 3.10+ and may fail in Python 3.12+.

## Solution Applied

Replaced:
```python
loop = asyncio.get_event_loop()
response = await loop.run_in_executor(...)
```

With:
```python
response = await asyncio.to_thread(self.client.search, ...)
```

## Date Fixed: 2025-11-27
