# AG-007: Hardcoded Model Names

## Status: ALREADY FIXED

> **Resolution**: This issue was already addressed in the existing codebase. Model names are configurable via environment variables in `src/core/constants.py`:
>
> - `DEFAULT_MODEL` - defaults to "gpt-4o", configurable via `DEFAULT_MODEL` env var
> - `DEFAULT_TEMPERATURE` - configurable via `DEFAULT_TEMPERATURE` env var
> - `DEFAULT_MAX_TOKENS` - configurable via `DEFAULT_MAX_TOKENS` env var
>
> Additionally, `SmartAIRouter` in `src/core/smart_router.py` allows configuring cheap vs expensive models via:
>
> - `ROUTER_CHEAP_MODEL` env var
> - `ROUTER_EXPENSIVE_MODEL` env var
>
> **Already implemented in**: `src/core/constants.py`, `src/core/smart_router.py`
> **Reviewed**: 2024-11-28

---

## Original Description (for reference)

## Priority: High

## Description

LLM model names are hardcoded throughout the codebase, making it difficult to switch models or use different models for different tasks.

## Location

- **File**: `src/core/constants.py` (configurable via env vars)
- **File**: `src/core/smart_router.py` (router model selection)

## Current Implementation

```python
# src/core/constants.py
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.0"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "4000"))
```

## Impact

- **Severity**: Medium
- **Maintenance**: Difficult to upgrade models
