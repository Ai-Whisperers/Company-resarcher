# LOW: Inconsistent Error Types

## Severity: Low
## File: `src/core/ai_client.py`

## Problem

Different AI clients handle errors inconsistently:

```python
# OpenAI - specific rate limit handling
except OpenAIRateLimitError:
    raise AIRateLimitError("openai")
except OpenAIAPIError as e:
    raise AIProviderError(str(e), "openai")

# Gemini - catches everything as generic
except Exception as e:
    raise AIProviderError(str(e), "gemini")  # Loses error type

# Groq - same issue
except Exception as e:
    raise AIProviderError(str(e), "groq")
```

## Impact

- Inconsistent error handling across providers
- Lost error context (original exception type)
- Hard to implement provider-specific retry logic
- Rate limit errors not detected for some providers

## Solution

Implement consistent error handling for all providers:

```python
class GeminiClient(BaseAIClient):
    async def generate(self, ...):
        try:
            # ...
        except google_exceptions.ResourceExhausted as e:
            raise AIRateLimitError("gemini") from e
        except google_exceptions.GoogleAPIError as e:
            raise AIProviderError(str(e), "gemini") from e
        except Exception as e:
            raise AIProviderError(str(e), "gemini") from e

class GroqClient(BaseAIClient):
    async def generate(self, ...):
        try:
            # ...
        except groq.RateLimitError as e:
            raise AIRateLimitError("groq") from e
        except groq.APIError as e:
            raise AIProviderError(str(e), "groq") from e
        except Exception as e:
            raise AIProviderError(str(e), "groq") from e
```

Also use `from e` to preserve exception chain:
```python
raise AIProviderError(str(e), "openai") from e
```

## Testing

After fix:
1. Trigger rate limit on each provider
2. Verify AIRateLimitError raised consistently
3. Verify original exception in `__cause__`
