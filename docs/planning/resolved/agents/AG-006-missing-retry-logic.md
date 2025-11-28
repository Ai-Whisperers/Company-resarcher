# AG-006: Missing Retry Logic for Transient Failures

## Status: COMPLETED

> **Resolution**: Retry logic has been added via the new `_safe_generate()` method in `BaseAgent`. Uses `tenacity` library with:
>
> - Max 3 retry attempts (`LLM_MAX_RETRIES` env var)
> - Exponential backoff (2s min, 30s max)
> - Retries on `AIRateLimitError` and `asyncio.TimeoutError`
> - Logging of retry attempts via `before_sleep_log`
>
> **Fixed in**: `src/agents/base_agent.py`
> **Date**: 2024-11-28
> **Related**: AG-004, AG-008 (fixed together)

---

## Original Description (for reference)

## Priority: High

## Description

Agent operations do not implement retry logic for transient failures (network timeouts, rate limits, temporary service unavailability).

## Location

- **File**: `src/agents/base_agent.py`
- **Method**: `_safe_generate()`

## Implemented Fix

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(LLM_MAX_RETRIES), wait=wait_exponential(min=2, max=30))
async def _invoke_with_retry():
    return await asyncio.wait_for(self.ai.generate(prompt), timeout=timeout)
```

## Impact

- **Severity**: High
- **Risk**: Failed research due to transient errors
