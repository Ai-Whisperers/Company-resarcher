# AG-001: Late-Stage Imports in Methods

**Priority**: Critical
**Effort**: Small (< 1 day)
**Type**: Code Quality / Performance

## Problem

In `base_agent.py`, imports are done inside methods rather than at module top level:

```python
# Lines 189-207 in execute_research_cycle()
from pathlib import Path
import jinja2
import json
```

## Location

- `src/agents/base_agent.py:189-207` - `execute_research_cycle()` method

## Impact

1. **Runtime overhead**: Imports are checked on every method call
2. **Harder to track dependencies**: Import statements scattered throughout code
3. **IDE/linter issues**: Static analysis tools may miss dependencies
4. **Circular import masking**: Hides potential circular import issues

## Recommended Fix

Move all imports to the top of the module:

```python
# At top of base_agent.py
from pathlib import Path
import json
import jinja2
```

## Acceptance Criteria

- [ ] All imports moved to module top level
- [ ] No runtime import statements inside methods
- [ ] All tests pass
- [ ] No circular import errors introduced
