# HIGH: Swallowed Exception in Browser Tool

## Issue #008
## Severity: 🟠 High
## Category: Error Handling
## File: `src/tools/browser.py:75`

## Problem

Exception handler swallows errors with only a warning logged:

```python
except Exception:
    logger.warning("Browser fetch failed")
    pass  # Exception details lost!
```

## Impact

- Root cause of failures unknown
- Debugging impossible
- Silent failures mask real issues

## Solution

Log the actual exception with traceback:

```python
except Exception as e:
    logger.error(f"Browser fetch failed: {e}", exc_info=True)
    raise  # Or return error result
```

## Testing

1. Force browser failure (invalid URL, network error)
2. Check logs contain full traceback
3. Verify error propagates to caller
