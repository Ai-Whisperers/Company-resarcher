# CO-007: No Configuration Validation

## Priority: High

## Description

Configuration values are loaded without validation, allowing invalid configurations to cause runtime errors.

## Location

- **File**: `src/core/config.py`

## Recommended Fix

```python
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    API_KEY: str
    TIMEOUT: int = 30

    @validator('TIMEOUT')
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v
```

## Impact

- **Severity**: High
- **Risk**: Runtime failures from invalid config
