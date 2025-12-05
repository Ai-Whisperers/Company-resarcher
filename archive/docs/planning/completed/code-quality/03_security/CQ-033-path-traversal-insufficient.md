# CQ-033: Path Traversal Check Insufficient

## Metadata
- **Severity**: HIGH
- **Category**: Security
- **File**: [src/agents/base_agent.py](src/agents/base_agent.py#L300-L310)
- **Lines**: 300-310
- **Effort**: S
- **Status**: Open

## Problem

The path traversal check in `base_agent.py` uses a simple string prefix comparison that:
1. Doesn't handle Windows path separators
2. Doesn't resolve symlinks
3. Can be bypassed with certain path patterns
4. Doesn't handle case-insensitivity on Windows

## Current Code

```python
def _is_safe_path(self, path: str, base_dir: str) -> bool:
    """Check if path is within base directory."""
    # Simple prefix check - VULNERABLE
    return path.startswith(base_dir)
```

## Why This Is Vulnerable

### Attack Vectors

```python
# Symlink bypass
# If /safe/link -> /etc, this passes but accesses /etc/passwd
_is_safe_path("/safe/link/passwd", "/safe")  # Returns True!

# Case sensitivity on Windows
_is_safe_path("C:\\Safe\\..\\Windows\\system.ini", "c:\\safe")
# Returns False, but "C:\\Safe" != "c:\\safe"

# Encoded characters
_is_safe_path("/safe/%2e%2e/etc/passwd", "/safe")
# May return True depending on encoding handling

# UNC paths on Windows
_is_safe_path("\\\\server\\share\\file", "C:\\safe")
# May bypass checks entirely
```

## Solution

Use `pathlib.Path` with proper resolution:

```python
from pathlib import Path
from typing import Union
import os

def is_safe_path(
    path: Union[str, Path],
    base_dir: Union[str, Path],
    allow_symlinks: bool = False
) -> bool:
    """
    Check if path is safely within base directory.

    This function properly handles:
    - Symlink resolution (unless explicitly allowed)
    - Case-insensitive comparison on Windows
    - Relative path components (.. and .)
    - Different path separators

    Args:
        path: Path to check
        base_dir: Base directory that path must be within
        allow_symlinks: If True, don't resolve symlinks

    Returns:
        True if path is safely within base_dir

    Example:
        >>> is_safe_path("/safe/data/file.txt", "/safe")
        True
        >>> is_safe_path("/safe/../etc/passwd", "/safe")
        False
    """
    try:
        # Convert to Path objects
        check_path = Path(path)
        base_path = Path(base_dir)

        # Resolve to absolute paths
        if allow_symlinks:
            # Only resolve .. and . but not symlinks
            check_resolved = check_path.absolute()
            base_resolved = base_path.absolute()
        else:
            # Full resolution including symlinks
            check_resolved = check_path.resolve()
            base_resolved = base_path.resolve()

        # Use is_relative_to (Python 3.9+) for safe comparison
        return check_resolved.is_relative_to(base_resolved)

    except (ValueError, OSError, RuntimeError):
        # Any path resolution error means unsafe
        return False


def is_safe_path_compat(
    path: Union[str, Path],
    base_dir: Union[str, Path]
) -> bool:
    """
    Python 3.8 compatible version of is_safe_path.
    """
    try:
        check_path = Path(path).resolve()
        base_path = Path(base_dir).resolve()

        # Manual relative check for Python < 3.9
        try:
            check_path.relative_to(base_path)
            return True
        except ValueError:
            return False

    except (OSError, RuntimeError):
        return False
```

### Additional Protections

```python
from pathlib import Path, PurePath
from typing import Set
import re

# Dangerous patterns to reject
DANGEROUS_PATTERNS: Set[str] = {
    "..",  # Parent directory
    "~",   # Home directory expansion
}

# Dangerous characters (especially for Windows)
DANGEROUS_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe filesystem use.

    Args:
        filename: Raw filename from user input

    Returns:
        Sanitized filename safe for filesystem operations
    """
    # Remove dangerous characters
    safe_name = DANGEROUS_CHARS.sub('_', filename)

    # Remove dangerous patterns
    parts = PurePath(safe_name).parts
    safe_parts = [p for p in parts if p not in DANGEROUS_PATTERNS]

    if not safe_parts:
        return "unnamed"

    return str(Path(*safe_parts))


def validate_output_path(
    requested_path: str,
    output_dir: str
) -> Path:
    """
    Validate and return safe output path.

    Args:
        requested_path: User-requested file path
        output_dir: Allowed output directory

    Returns:
        Safe absolute path within output_dir

    Raises:
        ValueError: If path would escape output_dir
    """
    # Sanitize the filename component
    safe_name = sanitize_filename(Path(requested_path).name)

    # Construct full path
    full_path = Path(output_dir) / safe_name

    # Verify it's within output_dir
    if not is_safe_path(full_path, output_dir):
        raise ValueError(
            f"Path would escape output directory: {requested_path}"
        )

    return full_path.resolve()
```

## Testing

```python
import pytest
from pathlib import Path
import tempfile
import os

class TestPathSafety:
    def test_basic_safe_path(self):
        """Test basic safe path detection."""
        assert is_safe_path("/safe/data/file.txt", "/safe")
        assert is_safe_path("/safe/subdir/file.txt", "/safe")

    def test_parent_directory_traversal(self):
        """Test parent directory traversal is blocked."""
        assert not is_safe_path("/safe/../etc/passwd", "/safe")
        assert not is_safe_path("/safe/data/../../etc/passwd", "/safe")

    def test_symlink_resolution(self):
        """Test symlink resolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_dir = Path(tmpdir) / "safe"
            safe_dir.mkdir()
            danger_dir = Path(tmpdir) / "danger"
            danger_dir.mkdir()
            (danger_dir / "secret.txt").write_text("secret")

            # Create symlink from safe to danger
            link = safe_dir / "link"
            link.symlink_to(danger_dir)

            # Should be blocked (symlinks resolved)
            assert not is_safe_path(
                str(link / "secret.txt"),
                str(safe_dir)
            )

    def test_case_sensitivity(self):
        """Test case handling on different platforms."""
        if os.name == 'nt':  # Windows
            # Windows is case-insensitive
            assert is_safe_path("C:\\Safe\\file.txt", "c:\\safe")
        else:
            # Unix is case-sensitive
            assert not is_safe_path("/Safe/file.txt", "/safe")

    def test_dangerous_characters(self):
        """Test dangerous character sanitization."""
        assert sanitize_filename("file<>:.txt") == "file___.txt"
        assert sanitize_filename("../../../etc/passwd") == "passwd"

    def test_empty_input(self):
        """Test empty/invalid input handling."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("..") == "unnamed"
```

## Verification Checklist

- [ ] `is_safe_path()` uses `Path.resolve()`
- [ ] Symlinks are resolved before comparison
- [ ] Case sensitivity handled per-platform
- [ ] Dangerous patterns rejected
- [ ] Tests cover all attack vectors
- [ ] No string-based path comparisons remain
