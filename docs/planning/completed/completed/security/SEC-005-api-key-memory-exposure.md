# SEC-005: API Key Memory Exposure Risk

## Priority: Medium
## Category: Security
## Status: Backlog

## Summary

API keys are stored using `SecretStr` but may be exposed in memory longer than necessary when `.get_secret_value()` is called.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/core/config.py` | Multiple | `get_secret_value()` returns plain string |
| `src/core/ai_client.py` | Multiple | API keys passed to client constructors |
| `src/api/app.py` | 154 | API key comparison in plain text |

## Current Pattern

```python
# Every time we need the key, we extract to plain string
expected_key = settings.API_KEY.get_secret_value()  # Plain string in memory
if api_key != expected_key:  # String comparison
    ...
```

## Risk

- Memory dumps could expose API keys
- Debugging/logging might accidentally capture keys
- Long-lived string objects in memory

## Proposed Improvements

### 1. Secure Comparison

```python
import hmac

def secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())

def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    settings = get_settings()
    if not settings.API_KEY:
        return "no-auth"

    # Use secure comparison
    if not secure_compare(api_key, settings.API_KEY.get_secret_value()):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key
```

### 2. Minimize Key Exposure Time

```python
class SecureAPIKeyValidator:
    """Validate API keys with minimal memory exposure."""

    def __init__(self, settings):
        # Store hash instead of key
        import hashlib
        key = settings.API_KEY.get_secret_value() if settings.API_KEY else ""
        self._key_hash = hashlib.sha256(key.encode()).digest()
        # Key string is now out of scope

    def validate(self, provided_key: str) -> bool:
        import hashlib
        provided_hash = hashlib.sha256(provided_key.encode()).digest()
        return hmac.compare_digest(self._key_hash, provided_hash)
```

### 3. Audit Logging Without Keys

```python
def log_api_access(api_key: str, endpoint: str):
    """Log API access without exposing full key."""
    # Only log key prefix for identification
    key_prefix = api_key[:8] + "..." if len(api_key) > 8 else "***"
    logger.info(f"API access: {endpoint} by key {key_prefix}")
```

## Implementation Tasks

- [ ] Implement secure string comparison
- [ ] Add key hashing for storage where possible
- [ ] Audit all `get_secret_value()` calls
- [ ] Ensure keys are not logged
- [ ] Add memory cleanup after key use
- [ ] Document secure key handling practices

## Success Criteria

- No plain-text keys in logs
- Timing-safe comparison used
- Keys not stored longer than necessary
- Security audit passes
