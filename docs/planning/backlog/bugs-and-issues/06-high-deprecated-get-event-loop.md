# HIGH: Deprecated `asyncio.get_event_loop()`

## Severity: High
## File: `src/tools/search.py` (line 34)

## Problem

Using deprecated `asyncio.get_event_loop()`:

```python
loop = asyncio.get_event_loop()
response = await loop.run_in_executor(...)
```

## Impact

- Deprecated in Python 3.10+
- Emits `DeprecationWarning`
- May fail in Python 3.12+ when no running event loop exists
- Creates inconsistent behavior across Python versions

## Solution

Use `asyncio.get_running_loop()` instead:

```python
async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    # ...
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=False,
            ),
        )
```

Or use `asyncio.to_thread()` (Python 3.9+):

```python
response = await asyncio.to_thread(
    self.client.search,
    query=query,
    search_depth="advanced",
    max_results=max_results,
    include_raw_content=False,
)
```

## Testing

After fix:
1. Run with Python 3.10+
2. Verify no deprecation warnings
3. Test search functionality works correctly
