# GR-001: No State Validation Between Transitions

## Priority: Critical

## Description

The LangGraph state machine does not validate state objects between transitions, allowing:
- Invalid state to propagate through the workflow
- Corrupted data to reach output nodes
- Silent failures that produce incorrect results
- Type mismatches causing runtime errors

## Location

- **File**: `src/graph/state.py`
- **File**: `src/graph/graph_builder.py`
- **Functions**: State transition handlers

## Current Code Pattern

```python
class ResearchState(TypedDict):
    company_name: str
    research_data: dict
    analysis_results: list
    # No validation

def research_node(state: ResearchState) -> ResearchState:
    # State could be corrupted, no validation
    state["research_data"] = fetch_data(state["company_name"])
    return state
```

## Problems

1. **No type validation**: State fields can be wrong types
2. **No required field checks**: Missing required data passes silently
3. **No invariant checks**: Business rules not enforced
4. **No schema versioning**: State schema changes break workflows

## Recommended Fix

```python
from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ResearchPhase(str, Enum):
    INIT = "init"
    GATHERING = "gathering"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    ERROR = "error"

class ResearchState(BaseModel):
    """Validated research workflow state."""

    company_name: str = Field(..., min_length=1, max_length=200)
    phase: ResearchPhase = ResearchPhase.INIT
    research_data: Dict[str, Any] = Field(default_factory=dict)
    analysis_results: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    iteration: int = Field(default=0, ge=0, le=10)

    @validator('company_name')
    def validate_company_name(cls, v):
        if not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()

    @validator('research_data')
    def validate_research_data(cls, v, values):
        if values.get('phase') == ResearchPhase.ANALYZING and not v:
            raise ValueError('Research data required for analysis phase')
        return v

    def transition_to(self, new_phase: ResearchPhase) -> 'ResearchState':
        """Validate phase transition."""
        valid_transitions = {
            ResearchPhase.INIT: {ResearchPhase.GATHERING, ResearchPhase.ERROR},
            ResearchPhase.GATHERING: {ResearchPhase.ANALYZING, ResearchPhase.ERROR},
            ResearchPhase.ANALYZING: {ResearchPhase.COMPLETE, ResearchPhase.ERROR},
        }

        if new_phase not in valid_transitions.get(self.phase, set()):
            raise ValueError(f"Invalid transition: {self.phase} -> {new_phase}")

        return self.copy(update={'phase': new_phase})

    class Config:
        validate_assignment = True  # Validate on every update
        extra = 'forbid'  # No extra fields allowed

# State validation decorator for nodes
def validate_state(func):
    @wraps(func)
    def wrapper(state: dict) -> dict:
        # Validate input
        validated_input = ResearchState(**state)
        # Execute node
        result = func(validated_input.dict())
        # Validate output
        validated_output = ResearchState(**result)
        return validated_output.dict()
    return wrapper

@validate_state
def research_node(state: dict) -> dict:
    # State is guaranteed to be valid
    state["research_data"] = fetch_data(state["company_name"])
    return state
```

## Impact

- **Severity**: High
- **Frequency**: Every state transition
- **Affected Components**: All workflow executions

## Testing Requirements

- Test valid state transitions
- Test invalid state rejection
- Test edge cases (empty, null, wrong types)
- Test phase transition rules

## Related Issues

- [GR-002](GR-002-race-conditions.md) - State race conditions
- [GR-004](GR-004-no-rollback.md) - State rollback
