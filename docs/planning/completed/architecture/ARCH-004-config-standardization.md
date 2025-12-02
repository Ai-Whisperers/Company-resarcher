# ARCH-004: Configuration Standardization

## Status: RESOLVED

## Resolved Date: 2024-12-01

## Summary

Standardized configuration management by adding comprehensive config models to `src/core/config.py` and updating key modules to use centralized settings instead of direct `os.getenv()` calls.

## Implementation

### New Config Models Added

| Config Class | Purpose | Key Settings |
|--------------|---------|--------------|
| `DatabaseConfig` | Database connection | url, pool_size, max_overflow |
| `RedisConfig` | Redis caching | host, port, db, password, ssl, ttl |
| `ServerConfig` | API server | cors_origins, timeouts, max_request_size |
| `AgentConfig` | Agent execution | concurrent_queries, domain_limits, llm_timeout |
| `BrowserConfig` | Web scraping | fetch_timeout, page_timeout, max_concurrent |
| `GraphConfig` | Research graph | node_timeout, retry_attempts, circuit_breaker |
| `DeepResearchConfig` | Deep research | max_context_words, breadth, depth |
| `SearchConfig` | Search providers | timeout, rate_limits, retries |
| `TelemetryConfig` | Observability | sentry, otel, prometheus settings |
| `IntegrationKeysConfig` | Third-party APIs | glassdoor, linkedin, crunchbase keys |

### Files Updated

| File | Changes |
|------|---------|
| `src/core/config.py` | Added 10 new config model classes |
| `src/api/database.py` | Uses `settings.database.*` |
| `src/tools/glassdoor_tool.py` | Uses `settings.integrations.*` |
| `src/tools/linkedin_tool.py` | Uses `settings.integrations.*` |
| `src/tools/crunchbase_tool.py` | Uses `settings.integrations.*` |
| `src/core/redis_cache.py` | Uses `settings.redis.*` |

### Usage Pattern

```python
# Before (direct os.getenv)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/research.db")
pool_size = int(os.getenv("DB_POOL_SIZE", "5"))

# After (centralized settings)
from src.core.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database.url
pool_size = settings.database.pool_size
```

### Environment Variable Mapping

Settings support nested environment variables using `__` delimiter:

```bash
# Database settings
DATABASE__URL=postgresql://user:pass@localhost:5432/db
DATABASE__POOL_SIZE=10
DATABASE__MAX_OVERFLOW=20

# Redis settings
REDIS__HOST=redis.example.com
REDIS__PORT=6379
REDIS__PASSWORD=secret
REDIS__SSL=true

# Server settings
SERVER__CORS_ORIGINS=https://app.example.com
SERVER__RESEARCH_TIMEOUT_SECONDS=3600

# Agent settings
AGENT__MAX_CONCURRENT_QUERIES=10
AGENT__LLM_TIMEOUT_SECONDS=180

# Integration keys
INTEGRATIONS__GLASSDOOR_API_KEY=your-key
INTEGRATIONS__PROXYCURL_API_KEY=your-key
INTEGRATIONS__CRUNCHBASE_API_KEY=your-key
```

### Benefits

1. **Type Safety**: Pydantic models provide validation and type hints
2. **Centralized Management**: All settings in one place
3. **IDE Support**: Autocomplete and documentation
4. **Profile-Aware**: Different defaults per environment
5. **Testability**: Easy to mock/override for tests
6. **Documentation**: Self-documenting config structure

## Remaining Work

Some files still use direct `os.getenv()` calls for backwards compatibility. These can be migrated incrementally:

- `src/core/telemetry.py` - Uses multiple OTEL_* env vars
- `src/core/error_tracking.py` - Uses SENTRY_* env vars
- `src/graph/graph_builder.py` - Uses GRAPH_* env vars
- Various tool files - Use specific timeout/config values

The pattern is established and new code should use `get_settings()`.

## Verification

```bash
# Verify settings load correctly
python -c "from src.core.config import get_settings; s = get_settings(); print(f'DB: {s.database.url}, Redis: {s.redis.host}')"

# Verify modules work
python -c "from src.api.database import DATABASE_URL; print(f'OK: {DATABASE_URL}')"
python -c "from src.tools.glassdoor_tool import GlassdoorTool; print('Glassdoor OK')"
python -c "from src.tools.linkedin_tool import LinkedInTool; print('LinkedIn OK')"
python -c "from src.tools.crunchbase_tool import CrunchbaseTool; print('Crunchbase OK')"
```
