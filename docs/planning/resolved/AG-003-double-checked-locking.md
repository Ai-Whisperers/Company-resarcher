# AG-003: Double-Checked Locking Anti-Pattern

**Priority**: Critical
**Effort**: Small (< 1 day)
**Type**: Architecture / Concurrency

## Problem

The orchestrator uses double-checked locking pattern which is unnecessary in Python due to the GIL and adds complexity:

```python
# orchestrator.py:102-108
_orchestrator: Optional[ResearchOrchestrator] = None
_orchestrator_lock = threading.Lock()

def get_orchestrator(...) -> ResearchOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        with _orchestrator_lock:
            if _orchestrator is None:  # Double check
                _orchestrator = ResearchOrchestrator(...)
    return _orchestrator
```

## Location

- `src/agents/orchestrator.py:102-108`

## Impact

1. **Unnecessary complexity**: Python's GIL makes this pattern redundant
2. **Maintenance burden**: More code to understand and maintain
3. **Potential bugs**: Double-checked locking is notoriously error-prone

## Recommended Fix

Use a simpler thread-safe singleton pattern:

```python
_orchestrator: Optional[ResearchOrchestrator] = None
_orchestrator_lock = threading.Lock()

def get_orchestrator(...) -> ResearchOrchestrator:
    global _orchestrator
    with _orchestrator_lock:
        if _orchestrator is None:
            _orchestrator = ResearchOrchestrator(...)
        return _orchestrator
```

Or use a module-level initialization pattern.

## Acceptance Criteria

- [ ] Double-checked locking removed
- [ ] Simpler singleton pattern implemented
- [ ] Thread safety maintained
- [ ] All tests pass
