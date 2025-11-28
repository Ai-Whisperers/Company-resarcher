# HIGH: Type Error in Writer - Wrong Attribute Name

## Issue #006
## Severity: 🟠 High
## Category: Bug
## File: `src/agents/writer.py:40`

## Problem

Accessing `company.url` but `CompanyProfile` has `website` attribute, not `url`.

```python
context = {
    "company_name": company.name,
    "company_url": company.url,  # AttributeError! Should be company.website
}
```

## Impact

- AttributeError at runtime
- Report generation fails
- Research workflow crashes

## Solution

```python
context = {
    "company_name": company.name,
    "company_url": company.website,  # Correct attribute
}
```

## Testing

1. Run report generation
2. Verify no AttributeError
3. Check URL appears in report
