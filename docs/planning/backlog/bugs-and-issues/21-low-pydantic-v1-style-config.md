# LOW: State Model Uses Pydantic v1 Style Config

## Severity: Low
## File: `src/graph/state.py` (lines 52-53)

## Problem

Using Pydantic v1 style configuration:

```python
class ResearchState(BaseModel):
    # ...fields...

    class Config:
        arbitrary_types_allowed = True
```

## Impact

- Pydantic v2 deprecation warning
- Inconsistent with rest of codebase using v2
- Will break in future Pydantic versions

## Solution

Use Pydantic v2 style with `model_config`:

```python
from pydantic import BaseModel, Field, ConfigDict

class ResearchState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Input
    company_name: str
    website: str
    # ... rest of fields
```

## Testing

After fix:
1. Run with Pydantic v2
2. Verify no deprecation warnings
3. Verify ResearchState works correctly
