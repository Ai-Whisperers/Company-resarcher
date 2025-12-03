# CQ-029: API Key Partially Exposed in Logs

## Metadata
- **Severity**: HIGH
- **Category**: Security
- **File**: [src/core/managers/key_manager.py](src/core/managers/key_manager.py#L85)
- **Lines**: 85, 148, 168-169
- **Effort**: S
- **Status**: Open

## Problem

The KeyManager uses the last 8 characters of API keys as identifiers in logs and error messages. This exposes a significant portion of the actual key, making it easier to guess or brute-force the complete key.

## Current Code

```python
class KeyManager:
    def _get_key_id(self, value: str) -> str:
        """Get a safe identifier for logging."""
        return value[-8:]  # SECURITY ISSUE: Exposes last 8 chars!

    def log_key_usage(self, key: str):
        key_id = self._get_key_id(key)
        logger.info(f"Using key: ...{key_id}")  # Leaks "abc12345" from "sk-xxx...abc12345"
```

## Why This Is a Problem

1. **Information Disclosure**: Last 8 characters reveal significant entropy
2. **API Key Format**: Many API keys have predictable prefixes (e.g., `sk-`, `api-`)
3. **Brute Force**: Reduces keyspace significantly for attackers
4. **Compliance**: May violate security policies requiring full key redaction
5. **Log Aggregation**: Keys may be searchable in centralized logging systems

## Solution

Use a cryptographic hash of the key for identification:

```python
import hashlib
from typing import Optional

class KeyManager:
    def _get_key_id(self, value: str) -> str:
        """
        Get a safe identifier for logging.

        Uses SHA-256 hash prefix instead of actual key characters.
        This allows tracking key usage without exposing any key content.
        """
        if not value:
            return "empty"

        # Hash the entire key
        key_hash = hashlib.sha256(value.encode()).hexdigest()

        # Return first 8 chars of hash (safe, no key info)
        return key_hash[:8]

    def log_key_usage(self, key: str):
        key_id = self._get_key_id(key)
        logger.info(f"Using key: {key_id}")  # Safe: logs "a1b2c3d4"
```

### Alternative: Masked Format

If you need to show some structure:

```python
def _get_key_id(self, value: str) -> str:
    """Get a masked key identifier."""
    if not value:
        return "empty"
    if len(value) < 8:
        return "****"

    # Show prefix (usually non-secret) + hash
    prefix = value[:3] if len(value) > 10 else ""
    key_hash = hashlib.sha256(value.encode()).hexdigest()[:6]
    return f"{prefix}...{key_hash}"  # "sk-...a1b2c3"
```

## Files to Update

1. `src/core/managers/key_manager.py` - Main fix
2. Any other files that log API keys (search for patterns like `[-8:]`)

## Testing

```python
def test_key_id_no_exposure():
    """Verify key ID doesn't expose key content."""
    km = KeyManager()

    key = "sk-abc123xyz789secretkey"
    key_id = km._get_key_id(key)

    # Should NOT contain any part of the actual key
    assert "secret" not in key_id.lower()
    assert "xyz789" not in key_id
    assert key[-8:] not in key_id

    # Same key should produce same ID (for tracking)
    assert km._get_key_id(key) == km._get_key_id(key)

    # Different keys should produce different IDs
    other_key = "sk-different-key-here"
    assert km._get_key_id(key) != km._get_key_id(other_key)
```

## Verification Steps

1. Search codebase for `[-8:]` pattern on key/secret variables
2. Search logs for patterns matching API key formats
3. Verify no key fragments appear in any log output
4. Run security scan for credential exposure

## Related Issues

- CQ-032: API key in headers could leak in error messages
