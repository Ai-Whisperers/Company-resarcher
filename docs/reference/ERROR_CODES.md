# Error Codes Reference

Documentation of all error codes and exception types in Company Researcher.

## HTTP Status Codes

### Success Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful |

### Client Error Codes

| Code | Name | When | Example Response |
|------|------|------|------------------|
| 400 | Bad Request | Invalid input data | `{"detail": "Company name cannot be empty"}` |
| 404 | Not Found | Resource doesn't exist | `{"detail": "Task not found"}` |
| 413 | Payload Too Large | Request body > 1MB | `{"detail": "Request body too large. Maximum size is 1000000 bytes."}` |
| 422 | Unprocessable Entity | Validation failed | `{"detail": [{"loc": ["body", "company_name"], "msg": "..."}]}` |
| 429 | Too Many Requests | Rate limit exceeded | `{"detail": "Too many requests. Please try again later."}` |

### Server Error Codes

| Code | Name | When | Example Response |
|------|------|------|------------------|
| 500 | Internal Server Error | Unexpected error | `{"detail": "An internal error occurred"}` |
| 503 | Service Unavailable | Dependency down | `{"detail": "Service temporarily unavailable"}` |
| 504 | Gateway Timeout | Request timeout | `{"detail": "Request timed out"}` |

---

## Error Response Format

### Standard Format

```json
{
    "detail": "Human-readable error message"
}
```

### Validation Error Format (422)

```json
{
    "detail": [
        {
            "loc": ["body", "company_name"],
            "msg": "String should have at least 1 character",
            "type": "string_too_short"
        }
    ]
}
```

---

## API Errors

### Rate Limiting (429)

**Cause**: More than 10 requests per minute from same IP.

**Response**:
```json
{
    "detail": "Too many requests. Please try again later."
}
```

**Solution**:
- Wait 60 seconds before retrying
- Implement exponential backoff in client

**Client Example**:
```python
import time

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=data)
        if response.status_code == 429:
            wait_time = 2 ** attempt * 10  # 10s, 20s, 40s
            time.sleep(wait_time)
            continue
        return response
    raise Exception("Max retries exceeded")
```

---

### Request Too Large (413)

**Cause**: Request body exceeds 1MB limit.

**Response**:
```json
{
    "detail": "Request body too large. Maximum size is 1000000 bytes."
}
```

**Solution**:
- Reduce request size
- Split into multiple requests if needed

---

### Task Not Found (404)

**Cause**: Invalid or expired task ID.

**Response**:
```json
{
    "detail": "Task not found"
}
```

**Solution**:
- Verify task ID is correct
- Task may have been deleted or never existed

---

### Validation Errors (422)

**Cause**: Request body fails Pydantic validation.

**Common Validation Errors**:

| Field | Error | Message |
|-------|-------|---------|
| `company_name` | Empty | "String should have at least 1 character" |
| `company_name` | Too long | "String should have at most 200 characters" |
| `url` | Invalid format | "Input should be a valid URL" |
| `industry` | Too long | "String should have at most 100 characters" |

**Response Example**:
```json
{
    "detail": [
        {
            "loc": ["body", "company_name"],
            "msg": "Company name cannot be empty or whitespace only",
            "type": "value_error"
        }
    ]
}
```

---

## LLM Provider Errors

### Rate Limit Errors

**OpenAI**:
```python
openai.RateLimitError: Rate limit exceeded
```

**Anthropic**:
```python
anthropic.RateLimitError: Rate limit exceeded
```

**Handling**: System automatically uses fallback provider if configured.

---

### Authentication Errors

**Cause**: Invalid or missing API key.

**OpenAI**:
```python
openai.AuthenticationError: Invalid API key
```

**Solution**:
1. Verify API key is correct
2. Check key hasn't expired
3. Ensure proper format (e.g., `sk-...` for OpenAI)

---

### Model Errors

**Cause**: Requested model unavailable.

```python
openai.NotFoundError: Model 'gpt-5' not found
```

**Solution**: Use supported model from configuration.

---

### Token Limit Errors

**Cause**: Request exceeds model's context window.

```python
openai.BadRequestError: This model's maximum context length is 128000 tokens
```

**Solution**: System uses smart router to handle appropriately.

---

## Research Errors

### Task Timeout

**Cause**: Research exceeds timeout (default: 30 minutes).

**Task Status**:
```json
{
    "task_id": "...",
    "status": "failed",
    "error": "Task timed out after 1800 seconds"
}
```

**Solution**:
- Increase `RESEARCH_TIMEOUT_SECONDS`
- Use simpler research parameters
- Check for slow external dependencies

---

### No AI Provider

**Cause**: No AI provider API key configured.

**Error**: Returned during health check or research start.

**Solution**: Configure at least one provider in `.env`:
```env
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
# OR use Ollama (no key needed)
```

---

### Search Failures

**Cause**: Search API unavailable or rate limited.

**Handling**: System falls back to DuckDuckGo if Tavily fails.

**Log Message**:
```
WARNING: Tavily search failed, using DuckDuckGo fallback
```

---

### Browser/Scraping Errors

**Cause**: Website blocking, timeout, or browser issues.

**Common Errors**:

| Error | Cause | Handling |
|-------|-------|----------|
| Page timeout | Slow website | Retry with longer timeout |
| Navigation failed | Invalid URL | Skip and continue |
| Access denied | Anti-bot protection | Use search results instead |
| Browser crashed | Resource exhaustion | Restart browser |

**Handling**: System continues with available data; doesn't fail entire research.

---

## Error Handling Best Practices

### Client-Side

```python
import requests

def start_research(company_name: str) -> dict:
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/research",
            json={"company_name": company_name},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 400:
            error = response.json()
            raise ValueError(f"Invalid input: {error['detail']}")

        elif response.status_code == 422:
            errors = response.json()["detail"]
            messages = [f"{e['loc'][-1]}: {e['msg']}" for e in errors]
            raise ValueError(f"Validation failed: {', '.join(messages)}")

        elif response.status_code == 429:
            raise Exception("Rate limited. Retry after 60 seconds.")

        elif response.status_code >= 500:
            raise Exception("Server error. Please try again later.")

        else:
            raise Exception(f"Unexpected error: {response.status_code}")

    except requests.Timeout:
        raise Exception("Request timed out")
    except requests.ConnectionError:
        raise Exception("Could not connect to API")
```

### Retry Logic

```python
import time
from functools import wraps

def retry_on_rate_limit(max_retries=3, base_delay=10):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        delay = base_delay * (2 ** attempt)
                        print(f"Rate limited, waiting {delay}s...")
                        time.sleep(delay)
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

@retry_on_rate_limit(max_retries=3)
def make_api_call():
    # ... API call
    pass
```

---

## Logging Errors

### Log Levels

| Level | When Used |
|-------|-----------|
| ERROR | Operation failed, needs attention |
| WARNING | Recoverable issue, fallback used |
| INFO | Normal operation events |
| DEBUG | Detailed debugging info |

### Log Format

```
2024-01-15 10:30:45 ERROR [api] Research task abc-123 failed: Rate limit exceeded
2024-01-15 10:30:46 WARNING [ai_client] OpenAI rate limited, using Anthropic fallback
2024-01-15 10:30:47 INFO [browser] Page loaded: https://example.com
```

---

## Health Check Errors

### Degraded Status

```json
{
    "status": "degraded",
    "checks": {
        "database": {"status": "ok"},
        "config": {"status": "warning", "warnings": ["TAVILY_API_KEY not set"]},
        "ai_provider": {"status": "ok"}
    }
}
```

### Unhealthy Status

```json
{
    "status": "unhealthy",
    "checks": {
        "database": {"status": "ok"},
        "config": {"status": "ok"},
        "ai_provider": {"status": "error", "message": "No AI provider configured"}
    }
}
```

---

## Related Documentation

- [API Reference](../api/API_REFERENCE.md)
- [Troubleshooting Guide](../guides/TROUBLESHOOTING.md)
- [Configuration Reference](../guides/CONFIGURATION.md)
