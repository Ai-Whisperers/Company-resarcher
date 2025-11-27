# CRITICAL: Singleton Orchestrator Startup Crash

## Severity: Critical
## File: `src/agents/orchestrator.py` (line 88)

## Problem

The module creates a `ResearchOrchestrator` instance at import time:

```python
# Singleton instance (optional)
orchestrator = ResearchOrchestrator()
```

This triggers full initialization including:
- AI client creation
- Agent factory initialization
- All specialist agent creation
- LangGraph workflow compilation

## Impact

Importing `orchestrator.py` will crash if:
- API keys are missing from environment
- Required dependencies aren't installed
- Environment isn't properly configured
- Any agent initialization fails

This makes the module impossible to import in tests or other contexts.

## Solution

Use lazy initialization pattern:

```python
_orchestrator = None

def get_orchestrator(use_local_tools: bool = False) -> ResearchOrchestrator:
    """Get or create the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ResearchOrchestrator(use_local_tools=use_local_tools)
    return _orchestrator
```

Or remove the singleton entirely and create instances as needed.

## Testing

After fix:
1. Import the module without environment configured
2. Verify no crash on import
3. Verify orchestrator created only when `get_orchestrator()` called
