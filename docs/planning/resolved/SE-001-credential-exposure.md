# SE-001: Credential Exposure in Service Configs

## Status: COMPLETED

## Priority: Critical

## Description

Service configurations contain credentials that may be exposed through:
- Logging of configuration objects
- Error messages with full config
- Serialization to disk or network
- Memory dumps during debugging

## Location

- **File**: `src/services/*.py`
- **All service configurations**

## Current Code Pattern

```python
class ServiceConfig:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.database_url = os.getenv("DATABASE_URL")  # Contains password

    def __repr__(self):
        return f"ServiceConfig(api_key={self.api_key}, db={self.database_url})"
```

## Problems

1. **Repr exposes secrets**: Default `__repr__` shows credentials
2. **Logging includes config**: `logger.info(f"Config: {config}")`
3. **No secret masking**: Credentials shown in full
4. **Serialization risk**: JSON/pickle includes secrets

## Recommended Fix

```python
from dataclasses import dataclass, field
from typing import Optional

class Secret(str):
    """String subclass that hides value in repr/str."""

    def __repr__(self) -> str:
        return "Secret(***)"

    def __str__(self) -> str:
        return "***"

    def get_secret_value(self) -> str:
        return super().__str__()

@dataclass
class ServiceConfig:
    service_name: str
    api_key: Secret = field(repr=False)
    database_url: Secret = field(repr=False)
    timeout: int = 30

    @classmethod
    def from_env(cls, service_name: str) -> 'ServiceConfig':
        return cls(
            service_name=service_name,
            api_key=Secret(os.getenv(f"{service_name.upper()}_API_KEY", "")),
            database_url=Secret(os.getenv("DATABASE_URL", "")),
        )

    def __repr__(self) -> str:
        return f"ServiceConfig(service={self.service_name}, timeout={self.timeout})"

    def to_safe_dict(self) -> dict:
        """Return dict without secrets for logging."""
        return {
            'service_name': self.service_name,
            'timeout': self.timeout,
            'has_api_key': bool(self.api_key.get_secret_value()),
            'has_database': bool(self.database_url.get_secret_value()),
        }

# Usage
config = ServiceConfig.from_env("research")
logger.info(f"Loaded config: {config}")  # Safe - no secrets shown
logger.debug(f"Config details: {config.to_safe_dict()}")  # Also safe
```

## Alternative with Pydantic

```python
from pydantic import BaseModel, SecretStr

class ServiceConfig(BaseModel):
    service_name: str
    api_key: SecretStr
    database_url: SecretStr
    timeout: int = 30

    class Config:
        json_encoders = {
            SecretStr: lambda v: "***" if v else None
        }
```

## Impact

- **Severity**: Critical (credential leakage)
- **Compliance**: Fails security audits
- **Affected Components**: All services

## Related Issues

- [AG-005](../agents/AG-005-secrets-in-logs.md) - Secrets in logs
- [SE-002](SE-002-no-encryption.md) - Data encryption

## Resolution

**Implemented**: 2024-11-28

Updated `src/core/config.py` to use Pydantic's `SecretStr` for all API keys:

- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`
- `TAVILY_API_KEY`, `NEWSAPI_KEY`, `SERPAPI_API_KEY`
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`

SecretStr prevents accidental exposure in:

- `repr()` output (shows `SecretStr('**********')`)
- Logging
- JSON serialization

Additionally, `src/core/logger.py` already had regex-based API key sanitization for extra protection.

Updated files to use `.get_secret_value()`:

- `src/core/ai_client.py`
- `src/tools/search.py`
