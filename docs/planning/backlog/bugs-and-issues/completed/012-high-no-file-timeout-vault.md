# HIGH: No Timeout on File Operations in Vault

## Issue #012
## Severity: 🟠 High
## Category: Reliability
## File: `src/core/vault.py:76-77`

## Problem

File operations have no timeout or error handling for hung file systems:

```python
def save(self, data: dict):
    with open(self.vault_path, "w") as f:  # Could hang forever on NFS
        json.dump(data, f)
```

## Impact

- Hung requests on network file systems
- No graceful degradation
- Research workflow blocks indefinitely

## Solution

Add timeout and context managers:

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    def handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds}s")

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def save(self, data: dict, timeout_seconds: int = 30):
    try:
        with timeout(timeout_seconds):
            with open(self.vault_path, "w") as f:
                json.dump(data, f)
    except TimeoutError as e:
        logger.error(f"Vault save timed out: {e}")
        raise
```

## Testing

1. Mount slow network share
2. Attempt save with timeout
3. Verify timeout exception raised
