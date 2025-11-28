# HIGH: Hardcoded Values in Constants

## Issue #010
## Severity: 🟠 High
## Category: Configuration
## File: `src/core/constants.py:6-10`

## Problem

Critical values hardcoded instead of using configuration:

```python
DEFAULT_MODEL = "gpt-4o"  # Hardcoded
DEFAULT_TEMPERATURE = 0.7  # Hardcoded
MAX_TOKENS = 4096  # Hardcoded
```

## Impact

- Cannot change without code modification
- Different environments need different values
- No override mechanism

## Solution

Load from environment or config:

```python
import os

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
```

Or use Settings class:

```python
from src.core.config import get_settings

def get_default_model() -> str:
    return get_settings().ai.openai.model
```

## Testing

1. Set environment variable
2. Verify constant reflects new value
3. Test default when env var not set
