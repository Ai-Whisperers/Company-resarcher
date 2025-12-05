# AG-010: Inconsistent Import Styles

**Priority**: High
**Effort**: Small (< 1 day)
**Type**: Code Quality

## Problem

Mixed use of absolute and relative imports across agent files:

```python
# factory.py - Absolute imports
from src.core.ai_client import BaseAIClient, get_ai_manager

# base_agent.py - Relative imports
from ..core.ai_client import BaseAIClient
```

## Locations

- `src/agents/factory.py` - Uses absolute imports
- `src/agents/base_agent.py` - Uses relative imports
- `src/agents/orchestrator.py` - Mixed styles
- `src/agents/deep_research.py` - Absolute imports

## Impact

1. **Maintenance burden**: Inconsistent style confuses developers
2. **Refactoring risk**: Moving files breaks different import styles
3. **IDE issues**: Some IDEs handle one style better than other

## Recommended Fix

Standardize on relative imports within the package:

```python
# All agent files should use:
from ..core.ai_client import BaseAIClient
from ..core.types import CompanyProfile
from .base_agent import BaseAgent
```

## Acceptance Criteria

- [ ] All agent files use consistent import style
- [ ] Style documented in CONTRIBUTING.md
- [ ] Linter rule added to enforce style
- [ ] All tests pass after changes
