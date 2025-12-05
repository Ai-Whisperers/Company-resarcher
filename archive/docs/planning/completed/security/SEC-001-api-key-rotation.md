# SEC-001: API Key Rotation Mechanism

## Status: RESOLVED

## Resolved Date: 2024-12-01

## Summary

Implemented a comprehensive API key rotation mechanism that supports multiple keys per provider with automatic failover and round-robin rotation strategies.

## Implementation

### Files Created

| File | Description |
|------|-------------|
| `src/core/key_manager.py` | Core KeyManager class with rotation support |

### KeyManager Features

- **Multiple Keys per Provider**: Support for up to 10 keys per provider via environment variables
  - Primary key: `PROVIDER_API_KEY`
  - Additional keys: `PROVIDER_API_KEY_2`, `PROVIDER_API_KEY_3`, etc.

- **Rotation Strategies**:
  - `ROUND_ROBIN`: Cycle through keys evenly (default)
  - `FAILOVER`: Use primary until exhausted, then switch
  - `RANDOM`: Random selection

- **Key Health Tracking**:
  - Track exhaustion status
  - Error counting with auto-exhaust after 5 errors
  - Cooldown period (default 1 hour) for exhausted keys
  - Request count tracking

- **Thread-Safe**: Lock-based concurrency protection

### Supported Providers

- OpenAI
- Anthropic
- Gemini
- Groq
- Tavily
- Serper
- SerpAPI
- NewsAPI
- Jina
- LangSearch

### Environment Configuration

```bash
# Rotation strategy
KEY_ROTATION_STRATEGY=round_robin  # round_robin, failover, random

# Cooldown for exhausted keys (seconds)
KEY_EXHAUSTION_COOLDOWN_SECONDS=3600

# Multiple keys per provider
OPENAI_API_KEY=sk-primary-key
OPENAI_API_KEY_2=sk-backup-key
OPENAI_API_KEY_3=sk-third-key
```

### Usage Example

```python
from src.core.key_manager import get_key_manager

manager = get_key_manager()

# Get next available key
key = manager.get_key("openai")

# Mark key as exhausted (rate limited)
manager.mark_exhausted("openai", key)

# Check availability
if manager.has_available_key("openai"):
    key = manager.get_key("openai")

# Get status of all providers
status = manager.get_status()
```

## Verification

```bash
# Verify module loads
python -c "from src.core.key_manager import KeyManager, get_key_manager; print('KeyManager loaded')"
```

## Original Backlog Item

See `docs/planning/backlog/10-security.md` - SEC-001
