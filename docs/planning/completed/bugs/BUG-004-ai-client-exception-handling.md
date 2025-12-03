# BUG-004: AI Client Broad Exception Handling

## Priority: High
## Category: Bug / Code Quality
## Status: Backlog

## Summary

`src/core/ai_client.py` has multiple overly broad exception handlers that prevent proper error propagation and differentiation.

## Affected Lines

| Line | Method | Issue |
|------|--------|-------|
| 77 | `_call_openai()` | Generic exception catch |
| 122 | `_call_anthropic()` | Generic exception catch |
| 209 | `_call_cohere()` | Generic exception catch |
| 249 | `_call_ollama()` | Generic exception catch |
| 317 | `_call_groq()` | Generic exception catch |
| 483 | `generate()` | Multiple generic catches |
| 493 | Retry logic | Exception type not checked |

## Current Pattern

```python
async def _call_openai(self, prompt: str) -> str:
    try:
        response = await self.client.chat.completions.create(...)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        raise  # Re-raises but loses context
```

## Problems

1. Can't differentiate rate limits from auth errors
2. Retry logic retries non-retriable errors
3. Error messages not actionable
4. No telemetry on error types

## Proposed Fix

```python
import openai
import anthropic

class AIClientException(Exception):
    """Base exception for AI client errors."""
    retriable: bool = False

class AIRateLimitError(AIClientException):
    """Rate limit exceeded."""
    retriable = True

class AIAuthenticationError(AIClientException):
    """Authentication failed."""
    retriable = False

class AIModelNotFoundError(AIClientException):
    """Model not available."""
    retriable = False

async def _call_openai(self, prompt: str) -> str:
    try:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        raise AIRateLimitError(f"OpenAI rate limit: {e}") from e
    except openai.AuthenticationError as e:
        raise AIAuthenticationError(f"OpenAI auth failed: {e}") from e
    except openai.NotFoundError as e:
        raise AIModelNotFoundError(f"Model not found: {e}") from e
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}", exc_info=True)
        raise AIClientException(f"OpenAI API error: {e}") from e
```

## Implementation Tasks

- [ ] Map each provider's exceptions to common hierarchy
- [ ] Update all `_call_*` methods
- [ ] Add retriable flag to exception classes
- [ ] Update retry logic to check retriable flag
- [ ] Add metrics for error types
- [ ] Document error handling behavior

## Success Criteria

- Provider-specific errors mapped to common types
- Retry logic only retries retriable errors
- Metrics available for error type analysis
- Documentation covers error scenarios
