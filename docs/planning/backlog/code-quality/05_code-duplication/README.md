# Code Duplication Issues

> **Total Issues**: 18 (6 HIGH, 8 MEDIUM, 4 LOW)
> **Priority**: Phase 2 - Code Quality

## Overview

Code duplication increases maintenance burden, makes changes error-prone, and leads to inconsistent behavior. These issues represent opportunities for significant code reduction.

## Issues Summary

### HIGH Severity (6)

| ID | File | Description | Lines Affected |
|----|------|-------------|----------------|
| CQ-058 | agents/factory.py | 12 identical try/except blocks | 154-240 |
| CQ-059 | agents/specialists.py | All _fetch_* methods identical | 361-411 |
| CQ-060 | cache/manager.py | Duplicate singleton pattern | 34-54 vs rate_limiting |
| CQ-061 | graph/state.py | Legacy constants duplicate StateConfig | 102-108 |
| CQ-062 | graph/graph_builder.py | Duplicate import of ReportWriter | 40-41 |
| CQ-063 | agents/deep_research.py | Utilities should be shared | 23-44 |

### MEDIUM Severity (8)

| ID | File | Description |
|----|------|-------------|
| CQ-064 | agents/specialists.py | Query list construction repeated |
| CQ-065 | agents/specialists.py | Error tracking with .extend(errors) |
| CQ-066 | agents/base_agent.py | Research cycle execution repeated |
| CQ-067 | api/app.py | SQLAlchemyError import in functions |
| CQ-068 | pipeline/stages/research.py | return_exceptions=True pattern |
| CQ-069 | pipeline/research_pipeline.py | Same return_exceptions pattern |
| CQ-070 | pipeline/stage.py | Same return_exceptions pattern |
| CQ-071 | agents/specialists.py | Hardcoded agent names |

### LOW Severity (4)

Minor duplication in helper functions and logging patterns.

## Refactoring Patterns

### CQ-058: Factory Tool Initialization

**Before**: 12 identical try/except blocks
```python
# Repeated 12 times!
try:
    self.search_tool = SearchTool(...)
except Exception as e:
    logger.warning(f"Failed to init search tool: {e}")
    self.search_tool = None
```

**After**: Factory method pattern
```python
def _init_tool(
    self,
    name: str,
    factory: Callable[[], T],
    required: bool = False
) -> Optional[T]:
    """Initialize a tool with standard error handling."""
    try:
        tool = factory()
        logger.debug(f"Initialized {name}")
        return tool
    except Exception as e:
        if required:
            raise
        logger.warning(f"Failed to init {name}: {e}")
        return None

# Usage
self.search_tool = self._init_tool("search", lambda: SearchTool(...))
self.browser_tool = self._init_tool("browser", lambda: BrowserTool(...))
```

### CQ-059: Fetch Method Pattern

**Before**: Identical _fetch_* methods
```python
async def _fetch_financials(self, query: str) -> DataSourceResult:
    if not self.financial_tool:
        return DataSourceResult(source="financial", data=None, error="Not available")
    try:
        data = await self.financial_tool.search(query)
        return DataSourceResult(source="financial", data=data)
    except Exception as e:
        return DataSourceResult(source="financial", data=None, error=str(e))

async def _fetch_news(self, query: str) -> DataSourceResult:
    # Exact same pattern...
```

**After**: Generic fetch method
```python
async def _fetch_from_tool(
    self,
    tool: Optional[BaseTool],
    source_name: str,
    query: str,
    method: str = "search"
) -> DataSourceResult:
    """Generic fetch from any tool."""
    if not tool:
        return DataSourceResult(source=source_name, data=None, error="Not available")
    try:
        method_fn = getattr(tool, method)
        data = await method_fn(query)
        return DataSourceResult(source=source_name, data=data)
    except Exception as e:
        return DataSourceResult(source=source_name, data=None, error=str(e))

# Usage
await self._fetch_from_tool(self.financial_tool, "financial", query)
await self._fetch_from_tool(self.news_tool, "news", query)
```

### CQ-060: Unified Singleton Pattern

**Create base class**:
```python
# src/core/patterns/singleton.py
import threading
from typing import TypeVar, Type

T = TypeVar('T')

class ThreadSafeSingleton:
    _instance: Optional['ThreadSafeSingleton'] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls: Type[T]) -> T:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                self._do_init()
                self._initialized = True

    def _do_init(self):
        """Override in subclass for initialization logic."""
        pass
```

### CQ-068-070: asyncio.gather Pattern

**Create utility function**:
```python
# src/core/utils/async_utils.py
from typing import List, TypeVar, Callable, Any
import asyncio

T = TypeVar('T')

async def gather_with_errors(
    tasks: List[Callable[[], T]],
    on_error: Callable[[Exception], T] = None
) -> List[T]:
    """
    Gather async tasks with consistent error handling.

    Unlike asyncio.gather(return_exceptions=True), this:
    - Logs errors consistently
    - Optionally transforms errors to result type
    - Maintains type safety
    """
    results = await asyncio.gather(
        *[task() for task in tasks],
        return_exceptions=True
    )

    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Task {i} failed: {result}")
            if on_error:
                processed.append(on_error(result))
        else:
            processed.append(result)

    return processed
```

## Verification Checklist

- [ ] All 12 factory try/except blocks use _init_tool()
- [ ] All _fetch_* methods use _fetch_from_tool()
- [ ] All singletons inherit from ThreadSafeSingleton
- [ ] asyncio.gather patterns use gather_with_errors()
- [ ] No duplicate imports
- [ ] Agent names use constants from config
