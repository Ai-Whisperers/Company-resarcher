# BUG-003: Base Agent Broad Exception Handling

## Priority: High
## Category: Bug / Code Quality
## Status: Backlog

## Summary

`src/agents/base_agent.py` uses overly broad `except Exception` handlers that mask errors and make debugging difficult.

## Affected Lines

| Line | Context |
|------|---------|
| 170 | In `execute_research_cycle()` |
| 196 | In async operations |
| 287 | In prompt rendering |
| 296 | In JSON parsing |

## Current Code

```python
# src/agents/base_agent.py:170
try:
    result = await self._call_llm(prompt)
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    return None  # Masks all errors!
```

## Problems

1. **AI-specific errors hidden**: Rate limits, token limits, model errors all treated same
2. **No retry differentiation**: Can't distinguish retriable from fatal errors
3. **Silent failures**: Returns None instead of propagating error
4. **Lost context**: Original exception traceback lost

## Proposed Fix

```python
from src.core.exceptions import (
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AITokenLimitError,
    AIModelError,
)

async def execute_research_cycle(self, ...):
    try:
        result = await self._call_llm(prompt)
    except AIRateLimitError as e:
        logger.warning(f"Rate limited, will retry: {e}")
        raise  # Let retry logic handle
    except AITimeoutError as e:
        logger.warning(f"LLM timeout: {e}")
        raise  # Retriable
    except AITokenLimitError as e:
        logger.error(f"Token limit exceeded: {e}")
        # Truncate prompt and retry once
        return await self._retry_with_truncated_prompt(prompt)
    except AIModelError as e:
        logger.error(f"Model error: {e}")
        raise  # Fatal, don't retry
    except AIProviderError as e:
        logger.error(f"Provider error: {e}", exc_info=True)
        raise
    except Exception as e:
        # Only catch truly unexpected errors
        logger.exception(f"Unexpected error in LLM call: {e}")
        raise AIProviderError(f"Unexpected error: {e}") from e
```

## Implementation Tasks

- [ ] Create exception hierarchy in `src/core/exceptions.py`
- [ ] Update base_agent.py exception handling
- [ ] Map provider errors to custom exceptions
- [ ] Add proper logging with exc_info
- [ ] Update retry logic to use exception types
- [ ] Add unit tests for each exception path

## Success Criteria

- Specific exceptions caught and handled appropriately
- Retriable errors distinguished from fatal
- Full tracebacks in logs
- Unit tests cover all exception paths
