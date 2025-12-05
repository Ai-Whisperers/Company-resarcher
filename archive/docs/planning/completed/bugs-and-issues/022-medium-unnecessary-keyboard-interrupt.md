# MEDIUM: Unnecessary KeyboardInterrupt Handling

## Issue #022
## Severity: 🟡 Medium
## Category: Code Quality
## File: `src/agents/critic.py:74`

## Problem

```python
except KeyboardInterrupt:
    raise
```

Unnecessary - let KeyboardInterrupt propagate naturally.

## Solution

Remove the explicit catch and re-raise.
