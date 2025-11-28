# AG-009: Hardcoded Configuration Values

**Priority**: High
**Effort**: Small (< 1 day)
**Type**: Configuration

## Problem

Several configuration values are hardcoded instead of being environment-configurable:

```python
# deep_research.py:18
MAX_CONTEXT_WORDS = 25000  # Should be env var

# factory.py:85-87
requests_per_minute=10, requests_per_hour=500  # Hardcoded

# deep_research.py:79
concurrency_limit: int = 2  # Hardcoded in constructor
```

## Locations

- `src/agents/deep_research.py:18` - MAX_CONTEXT_WORDS
- `src/agents/factory.py:85-87` - Rate limiting values
- `src/agents/deep_research.py:79` - concurrency_limit

## Impact

1. **Inflexibility**: Can't tune without code changes
2. **Environment differences**: Can't have different configs per environment
3. **Operational overhead**: Requires redeployment to change

## Recommended Fix

```python
# At module level
MAX_CONTEXT_WORDS = int(os.getenv("DEEP_RESEARCH_MAX_CONTEXT_WORDS", "25000"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))
CONCURRENCY_LIMIT = int(os.getenv("DEEP_RESEARCH_CONCURRENCY", "2"))
```

## Acceptance Criteria

- [ ] All hardcoded values moved to environment variables
- [ ] Sensible defaults provided
- [ ] Configuration documented
- [ ] Validation for config values added
