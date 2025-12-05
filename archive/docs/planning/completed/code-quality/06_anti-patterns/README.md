# Anti-patterns Issues

> **Total Issues**: 28 (8 HIGH, 14 MEDIUM, 6 LOW)
> **Priority**: Phase 2 - Code Quality

## Overview

Anti-patterns are common solutions that appear correct but cause problems. These issues represent architectural and design problems that make the codebase harder to maintain and extend.

## Issues Summary

### HIGH Severity (8)

| ID | File | Line | Description |
|----|------|------|-------------|
| CQ-072 | agents/base_agent.py | 74 | Fallback to singleton violates DI |
| CQ-073 | agents/base_agent.py | 71-72 | Shared tool singletons bypass DI |
| CQ-074 | agents/reasoning_agent.py | 76 | self.client assigned but unused |
| CQ-075 | agents/deep_research.py | 75 | super().__init__() wrong param |
| CQ-076 | agents/sector_analyst.py | 14-16 | Direct instantiation no error handling |
| CQ-077 | agents/orchestrator.py | 8 | Deprecated module still used |
| CQ-078 | graph/__init__.py | 50-55 | Entire deprecated module in use |
| CQ-079 | pipeline/orchestrator.py | 536-537 | Global singleton after anti-singleton design |

### MEDIUM Severity (14)

| ID | File | Description |
|----|------|-------------|
| CQ-080 | agents/specialist.py | hasattr() instead of interface |
| CQ-081 | pipeline/stages/fetch.py | isinstance() for type checking |
| CQ-082 | pipeline/comprehensive_research.py | Runtime isinstance() checks |
| CQ-083 | agents/base_agent.py | Import inside method |
| CQ-084 | agents/deep_research.py | Regex import inside method |
| CQ-085 | agents/deep_research.py | Inconsistent import style |
| CQ-086 | agents/writer.py | GroundingService direct instantiation |
| CQ-087 | search/manager.py | Private naming unclear |
| CQ-088 | api/app.py | Different error response structures |
| CQ-089 | agents/factory.py | Ollama assumes model exists |
| CQ-090 | agents/generic_agent.py | Redundant initialization |
| CQ-091 | agents/generic_agent.py | Phase-specific hints hardcoded |
| CQ-092 | search/providers/duckduckgo.py | run_in_executor without timeout |
| CQ-093 | graph/state.py | get_state_manager_sync() async lock in sync |

### LOW Severity (6)

| ID | File | Description |
|----|------|-------------|
| CQ-094 | agents/__init__.py | __getattr__() for deprecated import |
| CQ-095 | agents/base_agent.py | Implicit class name assumption |
| CQ-096 | agents/orchestrator.py | graph.compile() return not checked |
| CQ-097 | agents/factory.py | Client wrapping order-dependent |
| CQ-098 | ai/ai_client.py | Langfuse incomplete fallback |
| CQ-099 | managers/key_manager.py | Import inside method |

## Anti-Pattern Fixes

### CQ-072/073: Singleton Fallback Violates DI

**Problem**: Base class falls back to global singletons
```python
# BAD - Hidden dependency
class BaseAgent:
    def __init__(self, client=None):
        self.ai = client or get_ai_manager()  # Global fallback!
        self.search = get_shared_search_tool()  # Another global!
```

**Solution**: Require explicit injection
```python
# GOOD - Explicit dependencies
class BaseAgent:
    def __init__(
        self,
        client: AIClient,
        search_tool: Optional[SearchTool] = None
    ):
        if client is None:
            raise ValueError("AIClient is required")
        self.ai = client
        self.search = search_tool  # Explicit optional
```

### CQ-077/078: Deprecated Module Still Used

**Problem**: Module marked deprecated but actively used
```python
# graph/__init__.py
import warnings
warnings.warn("This module is deprecated", DeprecationWarning)
# ... but code still imports from here
```

**Solution**: Complete migration plan
1. Identify all imports of deprecated module
2. Create migration path to replacement
3. Update all call sites
4. Remove deprecated module

### CQ-080: hasattr() Instead of Interface

**Problem**: Duck typing with hasattr()
```python
# BAD
if hasattr(result, 'errors'):
    self.errors.extend(result.errors)
```

**Solution**: Use Protocol for structural typing
```python
# GOOD
from typing import Protocol, List

class HasErrors(Protocol):
    errors: List[str]

def process_result(result: HasErrors):
    self.errors.extend(result.errors)
```

### CQ-081/082: isinstance() Type Checking

**Problem**: Runtime type checking indicates poor design
```python
# BAD
if isinstance(news_results, dict) and news_results.get("enabled"):
    ...
elif isinstance(result, dict):
    return FetchedContent(...)
```

**Solution**: Use proper types and type narrowing
```python
# GOOD - Union types with TypeGuard
from typing import TypeGuard, Union

def is_enabled_result(result: Union[dict, list]) -> TypeGuard[dict]:
    return isinstance(result, dict) and result.get("enabled", False)

if is_enabled_result(news_results):
    # Type narrowed to dict with enabled key
    ...
```

### CQ-092: Executor Without Timeout

**Problem**: run_in_executor can hang forever
```python
# BAD
result = await loop.run_in_executor(None, blocking_call)
```

**Solution**: Add timeout
```python
# GOOD
import asyncio

async def run_with_timeout(func, timeout=30.0):
    try:
        return await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, func),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning("Executor call timed out")
        raise
```

## Verification Checklist

- [ ] No global singleton fallbacks in constructors
- [ ] All deprecated modules have migration plans
- [ ] hasattr() replaced with Protocol types
- [ ] isinstance() minimized, TypeGuard used where needed
- [ ] All executor calls have timeouts
- [ ] Imports at module level, not inside methods
- [ ] Error response structures consistent
