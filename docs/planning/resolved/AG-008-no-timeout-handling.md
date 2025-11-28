# AG-008: No Timeout Handling for LLM Calls

## Status: COMPLETED

> **Resolution**: Timeout handling has been added via the new `_safe_generate()` method in `BaseAgent`. Uses `asyncio.wait_for()` with:
>
> - Configurable timeout via `LLM_TIMEOUT_SECONDS` env var (default: 120s)
> - Proper `AITimeoutError` exception raised on timeout
> - Timeout errors are retried (up to `LLM_MAX_RETRIES` attempts)
>
> **Fixed in**: `src/agents/base_agent.py`
> **Date**: 2024-11-28
> **Related**: AG-004, AG-006 (fixed together)

---

## Original Description (for reference)

## Priority: High

## Description

LLM calls can hang indefinitely without timeout, blocking workflows and consuming resources.

## Location

- **File**: `src/agents/base_agent.py`
- **Method**: `_safe_generate()`

## Implemented Fix

```python
import asyncio

LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

async def _safe_generate(self, prompt: str, timeout: float = None) -> str:
    timeout = timeout or LLM_TIMEOUT_SECONDS
    return await asyncio.wait_for(
        self.ai.generate(prompt, response_format=response_format),
        timeout=timeout,
    )
```

## Impact

- **Severity**: High
- **Risk**: Resource exhaustion, hung workflows
