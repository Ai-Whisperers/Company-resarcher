# [RESOLVED] CRIT-001: Windows Unicode Encoding Issues

**Status**: RESOLVED
**Original File**: backlog/01-critical.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Critical
**Description:** The system forces UTF-8 encoding for stdout/stderr in `main.py` to handle non-ASCII characters on Windows. This is a patch. We need a more robust cross-platform solution.

**Acceptance Criteria:**
- [x] Remove `sys.stdout` modification in `main.py`.
- [x] Implement a custom logger handler that handles encoding gracefully.
- [x] Verify output on Windows (PowerShell/CMD) and Linux.

## Resolution

Comprehensive Windows Unicode support implemented in `src/core/logger.py`.

### Implementation Details

**File:** `src/core/logger.py`

#### 1. `_configure_windows_encoding()` Function

Handles Windows console encoding at startup:
```python
def _configure_windows_encoding() -> None:
    """Configure UTF-8 encoding for Windows console."""
    if platform.system() != "Windows":
        return

    # Method 1: Reconfigure streams (Python 3.7+)
    sys.stdout.reconfigure(encoding='utf-8', errors=error_handler)
    sys.stderr.reconfigure(encoding='utf-8', errors=error_handler)

    # Method 2: Set environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'
```

#### 2. `SafeStreamHandler` Class

Custom logging handler that gracefully handles encoding errors:
```python
class SafeStreamHandler(logging.StreamHandler):
    """
    A StreamHandler that gracefully handles Unicode encoding errors.

    On Windows, console output may fail with UnicodeEncodeError when logging
    messages containing emojis or special characters. This handler catches
    those errors and falls back to ASCII-safe representation.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # Fallback: encode with backslashreplace and decode back
            msg = self.format(record)
            safe_msg = msg.encode('ascii', 'backslashreplace').decode('ascii')
            self.stream.write(safe_msg + self.terminator)
```

#### 3. Integration in `setup_logger()`

```python
# Console Handler - use SafeStreamHandler for Windows Unicode support
console_handler = SafeStreamHandler(sys.stdout)
```

### Error Handling Modes

- **Development**: Uses `backslashreplace` to show what character failed
- **Production**: Uses `replace` for cleaner output

### References

- TECH-029: Original tech debt item
- TECH-031: Windows Unicode console encoding

## Files

- `src/core/logger.py` - SafeStreamHandler and encoding configuration
