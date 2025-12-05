# BUG-001: Broad Exception Handling Throughout Codebase

## Priority: High
## Category: Bug Fix / Code Quality
## Status: Backlog

## Summary

Multiple files across the codebase use overly broad exception handling (`except Exception`) which can mask errors, make debugging difficult, and potentially hide security issues.

## Affected Files

### High Priority (Core Components)

| File | Line(s) | Issue |
|------|---------|-------|
| `src/agents/base_agent.py` | Multiple | Catches `Exception` in async operations |
| `src/agents/deep_research.py` | Multiple | Broad exception in research methods |
| `src/agents/orchestrator.py` | Multiple | Generic exception handling |
| `src/core/ai_client.py` | 91, 135, 183, 222 | Catches all exceptions in API calls |
| `src/core/cached_ai_client.py` | Multiple | Exception handling in cache operations |

### Medium Priority (Tools/Services)

| File | Line(s) | Issue |
|------|---------|-------|
| `src/tools/browser.py` | Multiple | Broad exception in web scraping |
| `src/tools/search.py` | Multiple | Generic exception in search ops |
| `src/services/security.py` | Multiple | Exception handling in security code |

## Current Behavior

```python
# Current pattern (problematic)
try:
    result = await some_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    return None
```

This pattern:
1. Catches unrelated exceptions (KeyboardInterrupt, SystemExit)
2. Hides the root cause of failures
3. Makes debugging extremely difficult
4. Can mask security vulnerabilities

## Proposed Fix

```python
# Improved pattern
try:
    result = await some_operation()
except (HTTPError, ConnectionError, TimeoutError) as e:
    logger.warning(f"Network error: {e}")
    return None
except ValidationError as e:
    logger.error(f"Invalid data: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error in operation: {e}", exc_info=True)
    raise  # Re-raise unexpected exceptions
```

## Implementation Tasks

- [ ] Audit all `except Exception` usages (grep for pattern)
- [ ] Categorize by component (agents, tools, services, core)
- [ ] Replace with specific exception types where appropriate
- [ ] Add proper logging with `exc_info=True` for unexpected exceptions
- [ ] Consider creating custom exception hierarchy
- [ ] Add unit tests to verify exception handling

## Custom Exception Hierarchy (Proposed)

```python
# src/core/exceptions.py

class CompanyResearcherError(Exception):
    """Base exception for all application errors."""
    pass

class AIProviderError(CompanyResearcherError):
    """Error from AI provider (OpenAI, Anthropic, etc.)."""
    pass

class NetworkError(CompanyResearcherError):
    """Network-related errors (timeouts, connection issues)."""
    pass

class ValidationError(CompanyResearcherError):
    """Input validation errors."""
    pass

class ConfigurationError(CompanyResearcherError):
    """Configuration/settings errors."""
    pass

class RateLimitError(AIProviderError):
    """Rate limit exceeded from AI provider."""
    pass
```

## Success Criteria

- No bare `except Exception` without re-raising
- All expected exceptions caught with specific types
- Unexpected exceptions logged with full traceback
- Custom exception hierarchy implemented
- Unit tests cover exception paths
