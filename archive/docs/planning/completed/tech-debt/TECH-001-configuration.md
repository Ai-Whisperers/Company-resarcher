# TECH-001: Hardcoded Configuration Values

## Priority: Medium
## Category: Technical Debt
## Status: RESOLVED

## Summary

Configuration values externalized to Settings class with environment variable support.

## Implementation

All tasks completed in `src/core/config.py`:

### Features Implemented

1. **AIConfig Class**
   - Configurable AI providers (openai, anthropic, gemini, groq, ollama)
   - Per-provider model configuration
   - Temperature and max_tokens settings
   - Primary/fallback provider routing

   ```python
   class AIConfig(BaseModel):
       primary: Literal["openai", "anthropic", "gemini", "groq", "ollama"] = "openai"
       fallback: Optional[...] = None
       openai: AIProviderConfig = AIProviderConfig(model="gpt-4o")
       anthropic: AIProviderConfig = AIProviderConfig(model="claude-sonnet-4-20250514")
       # ... etc
   ```

2. **Profile-Based Defaults**
   - Development, Testing, Production profiles
   - Profile-specific settings (log levels, concurrency)
   - Environment-based profile selection

3. **Externalized Settings**
   - All API keys via SecretStr (secure handling)
   - Search configuration (MAX_SEARCH_RESULTS, CONCURRENT_SEARCHES)
   - Cache configuration (CacheConfig)
   - Runtime configuration (RuntimeConfig)

4. **Configuration Priority**
   - Environment variables (highest)
   - .env file
   - Profile-specific defaults
   - Class defaults (lowest)

## Files

- `src/core/config.py` - Comprehensive Settings class with nested configs

## Usage

```python
from src.core.config import get_settings

settings = get_settings()
model = settings.ai.openai.model  # Configurable
```

## Resolved Date: 2025-12-01
