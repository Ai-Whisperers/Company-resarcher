# HIGH: Circular Import Risk in Orchestrator

## Issue #009
## Severity: 🟠 High
## Category: Architecture
## File: `src/agents/orchestrator.py:33`

## Problem

Imports `AgentFactory` inside `__init__()` to avoid circular imports, indicating poor module structure:

```python
def __init__(self, ...):
    from src.agents.factory import AgentFactory  # Deferred import
    self.factory = AgentFactory(...)
```

## Impact

- Slower instantiation (import at runtime)
- Fragile dependency chain
- Hard to test and mock
- IDE autocomplete broken

## Solution

Restructure dependencies:
1. Move factory to separate module
2. Use dependency injection
3. Create interfaces package

```python
# In __init__.py or interfaces.py
from typing import Protocol

class AgentFactoryProtocol(Protocol):
    def create_specialists(self) -> Dict[str, BaseAgent]: ...

# In orchestrator.py
def __init__(self, factory: AgentFactoryProtocol):
    self.factory = factory
```

## Testing

1. Run `python -c "from src.agents.orchestrator import *"`
2. Verify no ImportError
3. Check import time doesn't increase
