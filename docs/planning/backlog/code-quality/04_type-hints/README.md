# Type Hints Issues

> **Total Issues**: 26 (6 HIGH, 12 MEDIUM, 8 LOW)
> **Priority**: Phase 3 - Maintainability

## Overview

Missing or incorrect type hints reduce IDE support, make refactoring error-prone, and prevent static analysis tools from catching bugs.

## Issues Summary

### HIGH Severity (6)

| ID | File | Line | Description |
|----|------|------|-------------|
| CQ-040 | agents/reasoning_agent.py | 17-18 | tools parameter no type, mismatches parent |
| CQ-041 | search/manager.py | 721 | provider_worker missing types |
| CQ-042 | search/manager.py | 550-568 | search_provider return not typed |
| CQ-043 | agents/sector_analyst.py | 9 | Entire class missing annotations |
| CQ-044 | agents/deep_research.py | 64-75 | Constructor param name mismatch |
| CQ-045 | agents/generic_agent.py | 20-35 | Phase config validation incomplete |

### MEDIUM Severity (12)

| ID | File | Description |
|----|------|-------------|
| CQ-046 | output/report_generator.py | Methods missing return type hints |
| CQ-047 | agents/deep_research.py | process_query lambda no return type |
| CQ-048 | agents/insight_generator.py | Python 3.10+ syntax incompatible |
| CQ-049 | agents/specialist.py | DataSourceResult no docstring |
| CQ-050 | data/content/crawler.py | Python 3.10+ union syntax |
| CQ-051 | pipeline/stages/fetch.py | dict instead of Dict[str, Any] |
| CQ-052 | api/app.py | asyncio.Task missing generic |
| CQ-053 | api/app.py | list_tasks() no return type |
| CQ-054 | agents/reasoning_agent.py | _format_context() return missing |
| CQ-055 | agents/sector_analyst.py | Entire class missing hints |
| CQ-056 | agents/specialists.py | Result assumes attributes exist |
| CQ-057 | agents/specialists.py | No null check on company.website |

### LOW Severity (8)

Minor type hint gaps in helper functions and internal methods.

## Common Fixes

### 1. Add Return Types
```python
# BAD
def process_data(items):
    return [x for x in items if x]

# GOOD
from typing import List, Optional, Any

def process_data(items: List[Optional[Any]]) -> List[Any]:
    return [x for x in items if x]
```

### 2. Fix Python Version Compatibility
```python
# BAD - Python 3.10+ only
def get_result() -> tuple[str, int]:
    return ("ok", 200)

# GOOD - Python 3.9 compatible
from typing import Tuple

def get_result() -> Tuple[str, int]:
    return ("ok", 200)
```

### 3. Fix Dict Type Hints
```python
# BAD
source_metadata: dict = field(default_factory=dict)

# GOOD
from typing import Dict, Any
source_metadata: Dict[str, Any] = field(default_factory=dict)
```

### 4. Generic Type Parameters
```python
# BAD
_running_tasks: dict[str, asyncio.Task] = {}

# GOOD
from typing import Dict, Any
_running_tasks: Dict[str, asyncio.Task[Dict[str, Any]]] = {}
```

### 5. Constructor Parameter Consistency
```python
# BAD - Mismatched parameter names
class DeepResearchAgent(BaseAgent):
    def __init__(self, ai_client):  # Parent uses 'client'
        super().__init__(client=ai_client)

# GOOD - Consistent naming
class DeepResearchAgent(BaseAgent):
    def __init__(self, client: AIClient):
        super().__init__(client=client)
```

## Verification Checklist

- [ ] Run `mypy src/` with no errors
- [ ] All public functions have return type hints
- [ ] All class attributes have type annotations
- [ ] Use `typing` module for Python 3.9 compatibility
- [ ] Generic types include type parameters
- [ ] Constructor parameters match parent class
