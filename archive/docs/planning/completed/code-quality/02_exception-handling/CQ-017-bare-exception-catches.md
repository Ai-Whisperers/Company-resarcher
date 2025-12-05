# CQ-017: Bare Exception Catches Throughout Codebase

## Metadata
- **Severity**: HIGH
- **Category**: Exception Handling
- **Files**: Multiple (see list below)
- **Total Occurrences**: 55+
- **Effort**: L
- **Status**: Open

## Problem

The codebase has 55+ instances of bare `except Exception` catches that:
1. Mask programming errors
2. Catch `SystemExit`, `KeyboardInterrupt` unintentionally
3. Make debugging extremely difficult
4. Hide the true cause of failures

## Affected Files

### HIGH Priority (Critical Paths)

| File | Line | Context |
|------|------|---------|
| cache/manager.py | 77-83 | Import failures silently swallowed |
| api/app.py | 164 | Metrics flushing |
| api/app.py | 506 | Research execution |
| search/manager.py | 315-319 | Search provider errors |
| pipeline/comprehensive_research.py | 266+ | 25+ occurrences |
| pipeline/stages/research.py | 314, 541, 593 | Query execution |
| pipeline/orchestrator.py | 236, 397 | Pipeline coordination |
| smart_parallel_executor.py | 369 | CancelledError caught |

### MEDIUM Priority

| File | Line | Context |
|------|------|---------|
| output/report_generator.py | 81-82, 121-124 | Report generation |
| ai/wrappers/cached.py | 66-75 | Cache initialization |
| config/api_limits.py | 90-103 | Environment parsing |
| agents/deep_research.py | 224-225 | Research cycles |
| agents/generic_agent.py | 78-83 | Template loading |

## Solution Pattern

### Step 1: Identify Specific Exceptions

```python
# BEFORE: Catches everything
try:
    result = await search_provider.search(query)
except Exception as e:
    logger.warning(f"Search failed: {e}")
    return []
```

```python
# AFTER: Specific exceptions
from httpx import HTTPError, TimeoutException
from asyncio import CancelledError

try:
    result = await search_provider.search(query)
except CancelledError:
    # Always re-raise cancellation
    raise
except TimeoutException:
    logger.warning(f"Search timed out for: {query}")
    return []
except HTTPError as e:
    logger.warning(f"HTTP error in search: {e.response.status_code}")
    return []
except Exception:
    # Log unexpected errors with full traceback
    logger.exception(f"Unexpected error searching: {query}")
    raise  # Re-raise unexpected errors
```

### Step 2: Create Exception Hierarchy

```python
# src/core/exceptions/base.py

class ResearchError(Exception):
    """Base exception for research operations."""
    pass

class SearchError(ResearchError):
    """Error during search operations."""
    pass

class ProviderError(SearchError):
    """Error from a specific provider."""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"{provider}: {message}")

class RateLimitError(ProviderError):
    """Rate limit exceeded."""
    def __init__(self, provider: str, retry_after: Optional[float] = None):
        self.retry_after = retry_after
        super().__init__(provider, "Rate limit exceeded")

class ContentError(ResearchError):
    """Error processing content."""
    pass

class AnalysisError(ResearchError):
    """Error during analysis phase."""
    pass
```

### Step 3: Implement Consistent Handling

```python
# src/core/utils/error_handling.py

from typing import TypeVar, Callable, Any
from functools import wraps
import asyncio

T = TypeVar('T')

def handle_errors(
    *expected_exceptions: type[Exception],
    default: T = None,
    log_level: str = "warning"
) -> Callable:
    """
    Decorator for consistent error handling.

    Args:
        expected_exceptions: Exception types to catch and handle
        default: Value to return on expected exception
        log_level: Logging level for expected exceptions

    Raises:
        Unexpected exceptions are always re-raised
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except asyncio.CancelledError:
                raise  # Never catch cancellation
            except expected_exceptions as e:
                log_fn = getattr(logger, log_level)
                log_fn(f"{func.__name__} failed: {e}")
                return default
            except Exception:
                logger.exception(f"Unexpected error in {func.__name__}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except expected_exceptions as e:
                log_fn = getattr(logger, log_level)
                log_fn(f"{func.__name__} failed: {e}")
                return default
            except Exception:
                logger.exception(f"Unexpected error in {func.__name__}")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Usage
@handle_errors(TimeoutError, HTTPError, default=[])
async def search(query: str) -> List[Result]:
    return await provider.search(query)
```

## Migration Script

```python
#!/usr/bin/env python3
"""Find bare exception catches in codebase."""

import ast
import sys
from pathlib import Path

class BareExceptFinder(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []

    def visit_ExceptHandler(self, node):
        if node.type is None:
            # Bare except:
            self.issues.append((node.lineno, "bare except"))
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            # except Exception:
            self.issues.append((node.lineno, "except Exception"))
        self.generic_visit(node)

def find_bare_excepts(directory: Path):
    for py_file in directory.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text())
            finder = BareExceptFinder(str(py_file))
            finder.visit(tree)
            for line, issue in finder.issues:
                print(f"{py_file}:{line}: {issue}")
        except SyntaxError:
            pass

if __name__ == "__main__":
    find_bare_excepts(Path(sys.argv[1]))
```

## Testing

```python
def test_search_specific_exception_handling():
    """Test that specific exceptions are handled correctly."""
    provider = MockProvider()

    # Timeout should return empty, not raise
    provider.search.side_effect = TimeoutError()
    result = await search_with_fallback(provider, "query")
    assert result == []

    # HTTP 500 should return empty
    provider.search.side_effect = HTTPError(response=Mock(status_code=500))
    result = await search_with_fallback(provider, "query")
    assert result == []

    # CancelledError should propagate
    provider.search.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await search_with_fallback(provider, "query")

    # Unexpected errors should propagate
    provider.search.side_effect = ValueError("unexpected")
    with pytest.raises(ValueError):
        await search_with_fallback(provider, "query")
```

## Verification Checklist

- [ ] No bare `except:` statements
- [ ] No `except Exception:` without re-raise
- [ ] `asyncio.CancelledError` always re-raised
- [ ] All expected exceptions documented
- [ ] Unexpected errors logged with traceback
- [ ] Run: `python find_bare_excepts.py src/`
