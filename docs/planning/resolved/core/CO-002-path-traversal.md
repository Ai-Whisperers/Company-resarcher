# CO-002: Path Traversal Vulnerability

## Status: COMPLETED

> **Resolution**: Fixed in `src/core/sandbox.py`
>
> - Added `_validate_path()` method that:
>   - Checks for dangerous shell characters (`;`, `|`, `&`, `$`, etc.)
>   - Validates path contains only safe characters
>   - Normalizes path and detects `..` traversal attempts
>   - Enforces paths stay within `/workspace/` directory
> - `copy_to_container()` now uses validated paths

---

## Priority: Critical

## Description

File path handling in the core module does not validate paths against traversal attacks. Attackers can use sequences like `../` to access files outside intended directories.

## Location

- **File**: `src/core/sandbox.py`
- **File**: `src/core/report_generator.py`
- **Functions**: File read/write operations

## Current Code Pattern

```python
def read_file(self, filename: str) -> str:
    # VULNERABLE: No path validation
    path = os.path.join(self.workspace, filename)
    with open(path, 'r') as f:
        return f.read()
```

## Attack Vectors

```python
# Malicious paths:
filename = "../../../etc/passwd"
filename = "....//....//etc/passwd"
filename = "/etc/passwd"
filename = "workspace/../../../secrets.env"
```

## Recommended Fix

```python
import os
from pathlib import Path

class SecureFileHandler:
    def __init__(self, base_directory: str):
        self.base_dir = Path(base_directory).resolve()

    def validate_path(self, user_path: str) -> Path:
        """Ensure path stays within base directory."""
        # Resolve the full path
        requested_path = (self.base_dir / user_path).resolve()

        # Check it's still within base directory
        try:
            requested_path.relative_to(self.base_dir)
        except ValueError:
            raise PermissionError(
                f"Access denied: {user_path} is outside workspace"
            )

        return requested_path

    def read_file(self, filename: str) -> str:
        safe_path = self.validate_path(filename)
        return safe_path.read_text()

    def write_file(self, filename: str, content: str) -> None:
        safe_path = self.validate_path(filename)
        # Also check parent directory exists
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content)
```

## Additional Protections

```python
# Blocklist sensitive paths
BLOCKED_PATHS = [
    '.env', 'secrets', 'credentials', 'config/prod',
    'id_rsa', 'private', '.git/config'
]

def is_sensitive_path(path: str) -> bool:
    return any(blocked in path.lower() for blocked in BLOCKED_PATHS)
```

## Impact

- **Severity**: Critical (Arbitrary File Read/Write)
- **CVSS Score**: 8.6 (High)
- **Affected Components**: File operations, report generation

## Testing

```python
@pytest.mark.parametrize("malicious_path", [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "/absolute/path",
    "valid/../../invalid",
])
def test_path_traversal_blocked(file_handler, malicious_path):
    with pytest.raises(PermissionError):
        file_handler.read_file(malicious_path)
```

## Related Issues

- [CO-001](CO-001-command-injection.md) - Command injection
- [CO-003](CO-003-env-file-exposure.md) - Environment file exposure
