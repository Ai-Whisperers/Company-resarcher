# HIGH: Settings Not Cached

## Severity: High
## File: `src/core/config.py` (lines 64-65)

## Problem

The `get_settings()` function creates a new `Settings` instance on every call:

```python
def get_settings() -> Settings:
    return Settings()  # Creates new instance every call!
```

## Impact

- Environment variables re-parsed on every call
- `.env` file re-read on every call
- Pydantic validation runs on every call
- Wasted CPU and I/O resources
- Inconsistent behavior if env changes mid-execution

## Solution

Use `@lru_cache` decorator:

```python
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

Or use a module-level singleton:

```python
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reset_settings():
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None
```

## Testing

After fix:
1. Call `get_settings()` multiple times
2. Verify same instance returned (check `id()`)
3. Measure performance improvement
