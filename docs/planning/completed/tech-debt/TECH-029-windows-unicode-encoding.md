# TECH-004: Windows Console Unicode Encoding Errors

## Priority: LOW
## Category: Technical Debt/Platform
## Status: Backlog
## Discovered: 2025-11-28

## Summary

On Windows, logging statements with non-ASCII characters (Chinese, special symbols) cause `UnicodeEncodeError` exceptions that clutter the console output.

## Problem Statement

When the browser navigates to URLs containing non-ASCII characters (e.g., Chinese dictionary sites), the logging system fails to encode the message for the Windows console (cp1252 encoding).

## Error Example

```
--- Logging error ---
UnicodeEncodeError: 'charmap' codec can't encode characters in position 85-86: character maps to <undefined>
Message: 'Navigating to: https://dictionary.cambridge.org/zhs/词典/英语-汉语-简体/personal'
```

## Impact

- Console output is cluttered with stack traces
- Actual log message is lost
- Makes debugging harder on Windows
- Does NOT affect functionality (just logging)

## Root Cause

1. Windows cmd/PowerShell uses cp1252 encoding by default
2. Python's logging module tries to write UTF-8 to cp1252 stream
3. Characters outside cp1252 cause encoding errors

## Proposed Solutions

### Option A: Configure Logger Encoding (Recommended)

In `src/core/logger.py`:
```python
import sys
import os

def setup_logger(name: str) -> logging.Logger:
    # Force UTF-8 for Windows console
    if sys.platform == "win32":
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    # ... rest of logger setup
```

### Option B: Use Safe String Formatting

```python
def safe_log(message: str) -> str:
    """Encode message safely for console output."""
    try:
        return message.encode('cp1252', errors='replace').decode('cp1252')
    except:
        return message.encode('ascii', errors='replace').decode('ascii')

logger.info(safe_log(f"Navigating to: {url}"))
```

### Option C: Custom Log Formatter

```python
class SafeFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        if sys.platform == "win32":
            return message.encode('cp1252', errors='replace').decode('cp1252')
        return message
```

### Option D: Set Environment Variable

Users can set `PYTHONIOENCODING=utf-8` before running:
```powershell
$env:PYTHONIOENCODING = "utf-8"
python main.py ...
```

Or in the startup script:
```python
# At the very top of main.py
import os
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
```

## Implementation Recommendation

1. Add Option A to `src/core/logger.py` - handles most cases
2. Document Option D in README for edge cases

## Acceptance Criteria

- [ ] No UnicodeEncodeError in console on Windows
- [ ] Non-ASCII characters display correctly or are replaced with `?`
- [ ] Logging functionality preserved on all platforms
- [ ] Works in cmd, PowerShell, and Windows Terminal

## Files to Modify

- `src/core/logger.py` - Add encoding configuration
- `main.py` - Optional: set environment variable early

## Testing

```python
def test_unicode_logging_windows():
    """Test that Unicode logging works on Windows."""
    logger = setup_logger("test")
    # Should not raise UnicodeEncodeError
    logger.info("URL with Chinese: https://example.com/中文")
    logger.info("URL with emoji: https://example.com/🎉")
```

## Notes

- This is cosmetic - doesn't affect research quality
- Only affects Windows console, not file logging
- Windows Terminal has better Unicode support than cmd.exe
