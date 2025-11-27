# MEDIUM: No Input Validation on Research Request

## Severity: Medium
## File: `src/api/models.py`

## Problem

The `ResearchRequest` model has minimal validation:

```python
class ResearchRequest(BaseModel):
    company_name: str  # No min length - empty string accepted
    url: Optional[str] = None  # No URL validation
    industry: Optional[str] = None
    country: Optional[str] = "USA"
```

## Impact

- Empty company names accepted
- Malformed URLs accepted
- Whitespace-only strings accepted
- Leads to confusing errors downstream
- Potential security issues

## Solution

Add Pydantic validators:

```python
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional

class ResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    url: Optional[HttpUrl] = None
    industry: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field("USA", max_length=100)

    @field_validator('company_name')
    @classmethod
    def company_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Company name cannot be empty or whitespace')
        return v

    @field_validator('industry', 'country')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v
```

## Testing

After fix:
1. Send request with empty company_name
2. Verify 422 validation error returned
3. Send request with invalid URL
4. Verify 422 validation error returned
