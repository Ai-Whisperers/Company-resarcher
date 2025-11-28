# CO-003: Environment File Can Be Read by Sandbox

## Status: N/A - Not Applicable

> **Analysis**: This issue does not exist in the current implementation.
>
> The `DockerSandbox` class in `src/core/sandbox.py`:
>
> - Does NOT mount any host volumes to the container
> - Uses `copy_to_container()` to explicitly copy only specific content
> - Container is completely isolated from host filesystem
> - No `.env` files or secrets are ever exposed to the sandbox
>
> **Conclusion**: The sandbox is properly isolated. No fix needed.

---

## Priority: Critical (if it existed)

## Description

The sandbox workspace mount may expose `.env` files or other credential files to sandboxed code, allowing malicious or compromised agent code to exfiltrate secrets.

## Location

- **File**: `src/core/sandbox.py`
- **Volume mounts in Docker configuration**

## Recommended Fix

```python
# Explicitly exclude sensitive files from mounts
EXCLUDED_PATTERNS = ['.env*', '*.key', '*.pem', 'credentials*', 'secrets*']

def create_container(self, workspace: str):
    # Create filtered workspace copy
    safe_workspace = self._create_safe_workspace(workspace)
    # Mount only the safe copy
```

## Impact

- **Severity**: Critical
- **Risk**: Credential theft by malicious code
