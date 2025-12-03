# Exception Handling Issues

> **Total Issues**: 55 (12 HIGH, 35 MEDIUM, 8 LOW)
> **Priority**: Phase 2 - Code Quality

## Overview

Poor exception handling masks bugs, makes debugging difficult, and can lead to silent failures. These issues affect system reliability and observability.

## Issues Summary

### HIGH Severity (12)

| ID | File | Line | Description |
|----|------|------|-------------|
| CQ-017 | cache/manager.py | 77-83 | Bare except swallows import failures |
| CQ-018 | api/app.py | 164 | Generic catch masks critical errors |
| CQ-019 | api/app.py | 506 | Broad catch loses stack context |
| CQ-020 | search/manager.py | 315-319 | Generic Exception without differentiation |
| CQ-021 | pipeline/comprehensive_research.py | 266+ | 25+ bare except catches |
| CQ-022 | pipeline/stages/research.py | 314 | Exception info lost in QueryResult |
| CQ-023 | pipeline/stages/research.py | 541 | Bare exception |
| CQ-024 | pipeline/stages/research.py | 593 | No traceback preservation |
| CQ-025 | pipeline/orchestrator.py | 236 | Generic exception handling |
| CQ-026 | pipeline/orchestrator.py | 397 | Bare exception catch |
| CQ-027 | smart_parallel_executor.py | 369 | CancelledError caught silently |
| CQ-028 | stages/evaluation.py | 120 | Generic exception catch |

### MEDIUM Severity (35)

Files affected:
- `output/report_generator.py` (3 locations)
- `ai/wrappers/cached.py` (1 location)
- `config/api_limits.py` (1 location)
- `agents/deep_research.py` (2 locations)
- `agents/generic_agent.py` (1 location)
- `agents/specialist.py` (1 location)
- `agents/writer.py` (1 location)
- `search/providers/*.py` (4 locations)
- `pipeline/stages/fetch.py` (1 location)
- `pipeline/orchestrator.py` (2 locations)
- `pipeline/context.py` (1 location)
- `pipeline/stage.py` (1 location)
- `data/content/crawler.py` (2 locations)
- `api/app.py` (14 locations)

### LOW Severity (8)

Minor logging and error context improvements needed.

## Common Anti-Patterns

### 1. Bare Exception Catch
```python
# BAD
try:
    result = await fetch_data()
except Exception as e:
    logger.warning(f"Failed: {e}")
    return None

# GOOD
try:
    result = await fetch_data()
except asyncio.TimeoutError:
    logger.warning("Request timed out")
    raise
except ConnectionError as e:
    logger.warning(f"Connection failed: {e}")
    return None
except Exception:
    logger.exception("Unexpected error fetching data")
    raise
```

### 2. Lost Exception Context
```python
# BAD
except Exception as e:
    return QueryResult(error=str(e))  # Lost traceback!

# GOOD
import traceback

except Exception as e:
    return QueryResult(
        error=str(e),
        traceback=traceback.format_exc()
    )
```

### 3. Silent CancelledError Catch
```python
# BAD - CancelledError is a BaseException in Python 3.8+
except asyncio.CancelledError:
    last_error = "Cancelled"
    break  # Swallows cancellation!

# GOOD
except asyncio.CancelledError:
    logger.info("Task cancelled")
    raise  # Always re-raise CancelledError
```

## Verification Checklist

- [ ] All `except Exception` replaced with specific types
- [ ] `asyncio.CancelledError` is always re-raised
- [ ] Tracebacks preserved in error objects
- [ ] Critical errors logged with `logger.exception()`
- [ ] Error context includes relevant identifiers
