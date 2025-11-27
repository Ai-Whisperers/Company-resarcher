# HIGH: Browser Resource Leak

## Severity: High
## File: `src/tools/browser.py`

## Problem

The `BrowserTool` starts a Playwright browser but there's no automatic cleanup:

```python
async def start(self):
    self.browser = await self.playwright.chromium.launch(headless=True)

async def stop(self):
    if self.browser:
        await self.browser.close()
    # stop() exists but is never called automatically
```

## Impact

- Browser instances accumulate in memory
- Chrome processes left running
- Memory leaks over time
- System resource exhaustion
- Eventually crashes on long-running servers

## Solution

Option 1: Use context manager:

```python
class BrowserTool:
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

# Usage:
async with BrowserTool() as browser:
    await browser.fetch_page(url)
```

Option 2: Use `atexit` or signal handlers:

```python
import atexit
import signal

class BrowserTool:
    def __init__(self):
        self.browser = None
        self.playwright = None
        atexit.register(self._cleanup_sync)

    def _cleanup_sync(self):
        if self.browser:
            asyncio.run(self.stop())
```

Option 3: Add cleanup to singleton getter:

```python
def get_shared_browser_tool() -> BrowserTool:
    global _browser_tool_instance
    if _browser_tool_instance is None:
        _browser_tool_instance = BrowserTool()
        atexit.register(lambda: asyncio.run(_browser_tool_instance.stop()))
    return _browser_tool_instance
```

## Testing

After fix:
1. Run multiple research cycles
2. Monitor Chrome process count
3. Verify processes cleaned up on exit
