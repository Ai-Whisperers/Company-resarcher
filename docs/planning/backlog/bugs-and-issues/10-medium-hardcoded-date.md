# MEDIUM: Hardcoded Date in main.py

## Severity: Medium
## File: `main.py` (line 58)

## Problem

The vault storage uses a hardcoded date:

```python
await vault.store_report(
    company_name=company_name,
    report_content=full_report_content,
    metadata={"source": "Company Researcher", "date": "2024-05-22"},  # Hardcoded!
)
```

## Impact

- All reports have the same incorrect date
- Impossible to track when reports were generated
- Confusing metadata

## Solution

Use dynamic date:

```python
from datetime import datetime

await vault.store_report(
    company_name=company_name,
    report_content=full_report_content,
    metadata={
        "source": "Company Researcher",
        "date": datetime.now().isoformat(),
    },
)
```

## Testing

After fix:
1. Generate a research report
2. Check vault metadata
3. Verify date matches current date/time
