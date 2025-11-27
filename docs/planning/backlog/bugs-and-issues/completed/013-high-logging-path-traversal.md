# HIGH: Path Traversal Risk in Logger

## Issue #013
## Severity: 🟠 High
## Category: Security
## File: `src/core/logger.py:73`

## Problem

Hardcoded log file path with no validation:

```python
file_handler = logging.FileHandler("research.log")  # Could be hijacked
```

## Impact

- Log file could be symlink to sensitive file
- Attacker could redirect logs
- Information disclosure

## Solution

Use config for log path and validate:

```python
import os
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    log_dir = Path(os.getenv("LOG_DIR", "./logs")).resolve()
    log_file = log_dir / "research.log"

    # Security: ensure log file is within log directory
    if not str(log_file).startswith(str(log_dir)):
        raise ValueError("Invalid log path")

    # Create directory if needed
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
```

## Testing

1. Create symlink `research.log -> /etc/passwd`
2. Start application
3. Verify symlink not followed or error raised
