# DO-010: No Usage Examples

**Priority**: Medium
**Category**: Documentation
**Status**: Partially Resolved
**Effort**: Medium (2-4 hours)

## Problem

Limited usage examples for common tasks.

## Current State

Some examples exist:
- `docs/guides/QUICK_START_TOOLS.md` - Tool implementation examples
- README.md - Basic CLI usage

## Missing Examples

### API Usage
```python
# Example: Using the REST API
import requests

# Start research
response = requests.post(
    "http://localhost:8000/api/v1/research",
    json={"company_name": "Adidas", "url": "https://adidas.com"}
)
task_id = response.json()["task_id"]

# Poll for results
while True:
    status = requests.get(f"http://localhost:8000/api/v1/research/{task_id}")
    if status.json()["status"] == "completed":
        break
    time.sleep(10)
```

### Programmatic Usage
```python
# Example: Using the orchestrator directly
from src.agents.orchestrator import ResearchOrchestrator

orchestrator = ResearchOrchestrator()
result = await orchestrator.conduct_research(
    company_name="Tesla",
    url="https://tesla.com"
)
```

### Custom Agent Creation
```python
# Example: Creating a custom specialist agent
from src.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def research(self, state):
        # Custom implementation
        pass
```

## Solution

Create `docs/examples/` directory with:
- `api_usage.py` - REST API examples
- `programmatic_usage.py` - Direct library usage
- `custom_agent.py` - Agent extension examples
- `tool_integration.py` - Adding new tools

## Acceptance Criteria

- [ ] API usage examples created
- [ ] Programmatic usage examples created
- [ ] Agent extension examples created
- [ ] Examples are runnable and tested
