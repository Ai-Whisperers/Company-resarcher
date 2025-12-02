# TECH-031: Windows Unicode Console Encoding Errors

## Priority: MEDIUM
## Category: Technical Debt/Platform Compatibility
## Status: Backlog
## Discovered: 2025-11-28

## Summary

On Windows systems, console output fails with `UnicodeEncodeError` when trying to print characters outside the Windows console's default encoding (cp1252). This affects logging of international content, URLs with special characters, and non-ASCII company names.

## Problem Statement

### Error Messages:
```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 24-25: character maps to <undefined>
```

### Affected Scenarios:
1. **Chinese characters in source titles**: Dictionary sites like iciba.com return Chinese titles
2. **Spanish/Portuguese characters**: Paraguay company names with ñ, á, é, etc.
3. **Special URL characters**: Encoded URLs with international characters
4. **Emoji in content**: Social media content with emojis

### Example Failures:
```python
# This fails on Windows cp1252 console
logger.info(f"Found source: personal是什么意思_personal的翻译")
logger.info(f"Processing: Señor García's Company")
```

## Root Cause Analysis

### 1. Windows Console Default Encoding

Windows command prompt uses `cp1252` (Western European) encoding by default, which cannot represent:
- CJK characters (Chinese, Japanese, Korean)
- Many Unicode symbols
- Emojis

### 2. Python Print/Logger Encoding

When Python tries to write to stdout/stderr, it uses the console's encoding:
```python
import sys
print(sys.stdout.encoding)  # 'cp1252' on Windows
```

### 3. Rich Console Library

The rich library used for console output may not properly handle encoding:
```python
# src/ui/console.py
console = Console()
console.print(text_with_unicode)  # Fails on Windows
```

## Proposed Solutions

### Solution 1: Force UTF-8 Console Output (Recommended)

```python
# src/main.py or src/__init__.py

import sys
import io

# Force UTF-8 encoding for stdout/stderr
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

### Solution 2: Configure Windows Console for UTF-8

```python
# src/utils/platform.py

import subprocess
import sys

def configure_windows_console():
    """Configure Windows console for UTF-8 support."""
    if sys.platform == 'win32':
        # Change code page to UTF-8
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)

        # Set environment variable
        import os
        os.environ['PYTHONIOENCODING'] = 'utf-8'
```

### Solution 3: Sanitize Log Output

```python
# src/utils/encoding.py

def safe_str(text: str, encoding: str = 'ascii') -> str:
    """Convert text to safe encoding for console output."""
    return text.encode(encoding, errors='replace').decode(encoding)

def safe_log(message: str) -> str:
    """Sanitize message for safe logging on any platform."""
    import sys
    if sys.platform == 'win32':
        # Replace problematic characters
        return message.encode('cp1252', errors='replace').decode('cp1252')
    return message

# Usage in logging
logger.info(safe_log(f"Found source: {source.title}"))
```

### Solution 4: Custom Logger Handler

```python
# src/utils/logging.py

import logging
import sys

class SafeStreamHandler(logging.StreamHandler):
    """Stream handler that handles encoding errors gracefully."""

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Replace unencodable characters
            if hasattr(stream, 'encoding') and stream.encoding:
                msg = msg.encode(stream.encoding, errors='replace').decode(stream.encoding)
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Configure logging
def setup_logging():
    handler = SafeStreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.root.addHandler(handler)
```

### Solution 5: Rich Console Configuration

```python
# src/ui/console.py

from rich.console import Console
import sys

def create_console() -> Console:
    """Create a console with proper encoding support."""
    if sys.platform == 'win32':
        # Use legacy Windows console mode with safe encoding
        return Console(
            force_terminal=True,
            legacy_windows=True,
            safe_box=True,
        )
    return Console()
```

## Files to Modify

1. `src/main.py` - Add UTF-8 encoding configuration at startup
2. `src/utils/encoding.py` - New file for encoding utilities
3. `src/utils/logging.py` - Custom safe stream handler
4. `src/ui/console.py` - Configure Rich console for Windows

## Acceptance Criteria

- [ ] No `UnicodeEncodeError` on Windows console
- [ ] Chinese/Japanese/Korean characters display or show replacement char
- [ ] Spanish/Portuguese characters display correctly
- [ ] Emojis don't crash the application
- [ ] Log files still contain full Unicode content
- [ ] Works in Windows Terminal, cmd.exe, and PowerShell

## Testing Plan

1. **Windows Command Prompt (cmd.exe)**
   - Run research on company with Chinese name
   - Verify no crashes, output shows replacement characters

2. **Windows PowerShell**
   - Run same test
   - Verify UTF-8 output if terminal supports it

3. **Windows Terminal (modern)**
   - Full Unicode should display correctly

4. **Cross-platform**
   - Verify Linux/macOS still work correctly

## Test Cases

```python
def test_unicode_logging():
    """Test that logging handles Unicode gracefully."""
    test_cases = [
        "Personal Paraguay",  # ASCII
        "Señor García",       # Spanish
        "日本語テスト",         # Japanese
        "emoji test 🚀",      # Emoji
        "Mixed: 中文 español", # Mixed
    ]

    for text in test_cases:
        logger.info(f"Testing: {text}")  # Should not raise
```

## Related Issues

- BUG-039: Dictionary sites in results (source of Chinese titles)
- TECH-029: Console output formatting

## Notes

This is a platform-specific issue that only affects Windows users. The application should degrade gracefully by replacing unencodable characters rather than crashing.

Consider adding a `--debug-encoding` flag that shows the actual encoding being used and any characters that were replaced.
