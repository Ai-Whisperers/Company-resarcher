# TECH-001: Hardcoded Configuration Values

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

Multiple files contain hardcoded configuration values that should be externalized to environment variables or configuration files for better flexibility and security.

## Affected Areas

### AI Model Names

| File | Line | Hardcoded Value |
|------|------|-----------------|
| `src/core/ai_client.py` | 91 | `"gpt-4-turbo"` |
| `src/core/ai_client.py` | 135 | `"claude-3-opus-20240229"` |
| `src/core/ai_client.py` | 183 | `"command-r-plus"` |
| `src/core/ai_client.py` | 222 | `"llama-3.1-70b"` |
| `src/core/smart_router.py` | Multiple | Model capability mappings |

### Other Hardcoded Values

| File | Value | Issue |
|------|-------|-------|
| `src/api/app.py` | CORS origins | Limited to localhost |
| `src/tools/browser.py` | User agent string | Static, easily blocked |
| `src/tools/search.py` | Search result limits | Not configurable |
| `src/core/rate_limiter.py` | Rate limits | Hardcoded per endpoint |

## Current Behavior

```python
# src/core/ai_client.py
async def _call_openai(self, prompt: str) -> str:
    response = await self.client.chat.completions.create(
        model="gpt-4-turbo",  # Hardcoded!
        messages=[...]
    )
```

## Proposed Fix

### 1. Centralized Model Configuration

```python
# src/core/config.py

class Settings(BaseSettings):
    # AI Model Configuration
    OPENAI_MODEL: str = "gpt-4-turbo"
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    COHERE_MODEL: str = "command-r-plus"
    OLLAMA_MODEL: str = "llama-3.1-70b"

    # Model for specific tasks
    SUMMARIZATION_MODEL: str = "gpt-4-turbo"
    ANALYSIS_MODEL: str = "claude-3-opus-20240229"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Browser
    USER_AGENT: str = "Mozilla/5.0 (compatible; CompanyResearcher/1.0)"

    # Rate Limits
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 10
    RATE_LIMIT_SEARCH_PER_MINUTE: int = 5
```

### 2. Usage Update

```python
# src/core/ai_client.py
from .config import get_settings

async def _call_openai(self, prompt: str) -> str:
    settings = get_settings()
    response = await self.client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[...]
    )
```

## Implementation Tasks

- [ ] Audit all hardcoded values (grep for string literals)
- [ ] Categorize values by type (models, URLs, limits, etc.)
- [ ] Add settings to `src/core/config.py`
- [ ] Add to `.env.example` with documentation
- [ ] Update code to use settings
- [ ] Add configuration validation
- [ ] Update documentation

## Configuration Priority

1. **Critical** - AI model names (affects functionality)
2. **High** - CORS origins, rate limits (affects security)
3. **Medium** - User agents, timeouts (affects reliability)
4. **Low** - Display strings, defaults (cosmetic)

## Success Criteria

- All model names configurable via environment
- CORS origins configurable for production
- Rate limits adjustable without code changes
- `.env.example` documents all settings
- No hardcoded values in core business logic
