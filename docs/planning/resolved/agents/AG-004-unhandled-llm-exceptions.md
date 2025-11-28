# AG-004: Unhandled LLM API Exceptions

## Status: COMPLETED

> **Resolution**: Added `_safe_generate()` method in `BaseAgent` that wraps all LLM calls with:
> - Retry logic using `tenacity` (exponential backoff, max 3 attempts)
> - Timeout handling via `asyncio.wait_for()` (configurable via `LLM_TIMEOUT_SECONDS` env var, default 120s)
> - Proper exception handling for `AIRateLimitError` and `asyncio.TimeoutError`
> - Logging of retry attempts and failures
>
> The `execute_research_cycle()` method now uses `_safe_generate()` instead of direct `self.ai.generate()` calls.
>
> **Fixed in**: `src/agents/base_agent.py`
> **Date**: 2024-11-28

---

## Original Description (for reference)

## Priority: Critical

## Description

LLM API calls in agent code do not properly handle exceptions, causing:
- Uncaught exceptions to propagate to users
- Research workflows to fail completely on transient errors
- No retry logic for recoverable failures
- Stack traces potentially exposing internal details

## Location

- **File**: `src/agents/base_agent.py`
- **Method**: `_safe_generate()` (new), `execute_research_cycle()`

## Current Code Pattern

```python
async def analyze(self, prompt: str) -> str:
    # No exception handling
    response = await self.llm.invoke(prompt)
    return response.content
```

## Problems

1. **No exception handling**: API errors crash the workflow
2. **No retry logic**: Transient failures are not retried
3. **No fallback**: No alternative when primary LLM fails
4. **No timeout**: Calls can hang indefinitely
5. **No rate limit handling**: 429 errors crash instead of backing off

## Recommended Fix

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APIError, APITimeoutError
import asyncio

class LLMExceptionHandler:
    """Centralized exception handling for LLM calls."""

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        reraise=True
    )
    async def safe_invoke(llm, prompt: str, timeout: float = 30.0) -> str:
        try:
            async with asyncio.timeout(timeout):
                response = await llm.invoke(prompt)
                return response.content
        except RateLimitError as e:
            logger.warning(f"Rate limited, retrying: {e}")
            raise  # Let tenacity retry
        except APITimeoutError as e:
            logger.warning(f"Timeout, retrying: {e}")
            raise
        except APIError as e:
            logger.error(f"API error (not retrying): {e}")
            raise LLMServiceError(f"LLM API error: {e}") from e
        except Exception as e:
            logger.exception("Unexpected LLM error")
            raise LLMServiceError(f"Unexpected error: {e}") from e

class BaseAgent:
    async def analyze(self, prompt: str) -> str:
        return await LLMExceptionHandler.safe_invoke(
            self.llm,
            prompt,
            timeout=self.config.llm_timeout
        )
```

## Exception Types to Handle

| Exception | Cause | Action |
|-----------|-------|--------|
| `RateLimitError` | Too many requests | Exponential backoff retry |
| `APITimeoutError` | Request timeout | Retry with longer timeout |
| `AuthenticationError` | Invalid API key | Fail fast, log error |
| `InvalidRequestError` | Malformed request | Fail fast, fix request |
| `APIConnectionError` | Network issues | Retry with backoff |
| `ServiceUnavailableError` | Server overload | Retry with backoff |

## Impact

- **Severity**: High
- **Frequency**: Common during peak usage
- **Affected Components**: All agent operations

## Testing Requirements

- Mock LLM to simulate each exception type
- Verify retry behavior
- Test timeout handling
- Confirm error messages don't leak sensitive info

## Related Issues

- [AG-006](AG-006-missing-retry-logic.md) - General retry logic
- [AG-008](AG-008-no-timeout-handling.md) - Timeout handling
- [AG-030](AG-030-no-circuit-breaker.md) - Circuit breaker pattern
