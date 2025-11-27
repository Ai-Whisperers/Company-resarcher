# Exception Handling & Recovery Pattern

## 📖 Overview

Robust error handling with classification, exponential backoff, and graceful fallbacks to ensure system reliability.

## 🎯 Core Concept

```
Execute → Error? → Classify → Strategy:
                              ├── Retry (transient)
                              ├── Fallback (degraded)
                              └── Fail gracefully (fatal)
```

## 💡 Implementation Strategy

### 1. Error Classification

```python
class ErrorType(Enum):
    TRANSIENT = "transient"  # Retry
    DEGRADED = "degraded"    # Fallback
    FATAL = "fatal"          # Fail gracefully

def classify_error(error: Exception) -> ErrorType:
    if isinstance(error, (TimeoutError, ConnectionError)):
        return ErrorType.TRANSIENT
    elif isinstance(error, (RateLimitError, QuotaError)):
        return ErrorType.DEGRADED
    else:
        return ErrorType.FATAL
```

### 2. Retry with Backoff

```python
async def retry_with_backoff(
    func,
    max_retries=3,
    base_delay=1.0
):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if classify_error(e) != ErrorType.TRANSIENT:
                raise

            delay = base_delay * (2 ** attempt)  # Exponential
            await asyncio.sleep(delay)

    raise MaxRetriesExceeded()
```

### 3. Fallback Strategy

```python
async def execute_with_fallback(primary, fallback):
    try:
        return await primary()
    except Exception as e:
        logger.warning(f"Primary failed: {e}, using fallback")
        return await fallback()
```

## 📊 Current Implementation

### AI Provider Fallback

```python
# Location: code/api/services/ai_client.py
async def generate_json(self, prompt: str):
    try:
        # Try Groq (primary)
        return await self.groq_client.generate(prompt)
    except Exception as e:
        logger.warning(f"Groq failed: {e}")
        # Fallback to OpenAI
        return await self.openai_client.generate(prompt)
```

## 🎓 Best Practices

### Do's ✅

- **Classify errors**: Know what to retry
- **Exponential backoff**: Avoid overwhelming
- **Log failures**: Track patterns
- **Graceful degradation**: Partial functionality
- **Circuit breaker**: Stop cascading failures

### Don'ts ❌

- **Don't retry forever**: Set limits
- **Don't ignore errors**: Handle explicitly
- **Don't lose context**: Preserve state
- **Don't spam**: Use backoff

## 🔧 Enhancement Opportunities

### Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5):
        self.failures = 0
        self.threshold = failure_threshold
        self.state = "closed"  # closed, open, half-open

    async def call(self, func):
        if self.state == "open":
            raise CircuitOpenError()

        try:
            result = await func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "open"

    def on_success(self):
        self.failures = 0
        self.state = "closed"
```

## ⚠️ Edge Cases & Pitfalls

### Common Pitfalls

1.  **Cascading Failures**: One service failing causes all others to fail (e.g., Database down -> API down -> Frontend down).
    - _Fix_: Implement Circuit Breakers to stop the bleeding.
2.  **Error Swallowing**: Catching `Exception` and doing nothing, hiding bugs.
    - _Fix_: Always log the error, even if you handle it gracefully.
3.  **Retry Storms**: Thousands of clients retrying at the exact same time.
    - _Fix_: Add "Jitter" (randomness) to the backoff delay.

### Edge Cases

- **Partial Failure**: The batch job processed 50/100 items. (Need to track individual item status).
- **Zombie Processes**: A task hangs forever without failing. (Need timeouts).

## 🧪 Testing Strategy

### 1. Fault Injection

Intentionally break dependencies (e.g., disconnect DB) to verify recovery.

```python
def test_db_failure():
    with mock.patch("db.connect", side_effect=ConnectionError):
        response = service.get_user(1)
        assert response.status == "degraded"
```

### 2. Chaos Engineering

Randomly kill services in staging to test resilience.

### 3. Eval Metrics

- **MTTR (Mean Time To Recovery)**: How fast does it bounce back?
- **Availability**: % of successful requests.

## 💻 Runnable Example

View a working example of Exception Handling:
[12_exception_handling.py](../examples/12_exception_handling.py)

---

**Status**: 🟡 Partial (basic fallback)  
**Priority**: High  
**Impact**: High  
**Next Steps**: Add circuit breaker, better classification
