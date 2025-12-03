# BUG-046: Browser Tool Race Condition - NoneType Error

## Summary
Browser tool fails with `'NoneType' object has no attribute 'new_page'` when multiple concurrent fetch requests are made before the browser context is initialized.

## Severity
**CRITICAL** - Causes data loss, first 6+ URLs fail silently

## Symptoms
```
19:32:11 - browser_tool - ERROR - Failed to fetch https://www.linkedin.com/company/personalparaguay/: 'NoneType' object has no attribute 'new_page'
19:32:11 - browser_tool - ERROR - Failed to fetch https://tienda.personal.com.py/: 'NoneType' object has no attribute 'new_page'
19:32:12 - browser_tool - ERROR - Failed to fetch https://portal.powertec.com.au/...: 'NoneType' object has no attribute 'new_page'
```

Then later:
```
19:32:12 - browser_tool - INFO - Browser initialized
```

## Root Cause
The browser context (`self.context`) is lazily initialized, but `fetch_multiple()` spawns concurrent tasks that try to call `self.context.new_page()` before initialization completes.

Race condition sequence:
1. `fetch_multiple([url1, url2, url3, ...])` called
2. Multiple async tasks spawned via `asyncio.gather()`
3. First task calls `self.context.new_page()` - triggers lazy init
4. Other tasks also call `self.context.new_page()` before init completes
5. `self.context` is still `None` for those tasks → crash

## Impact
- **LinkedIn company pages**: Critical for competitor/brand analysis - LOST
- **Official store pages**: Key for product/pricing info - LOST
- **Wikipedia demographics**: Market sizing data - LOST
- Result: 6+ sources missing from each research phase

## Affected Files
- `src/tools/browser.py` - `fetch_multiple()` and lazy initialization

## Proposed Solution

### Option 1: Eager Initialization with Lock (Recommended)
```python
import asyncio

class BrowserTool:
    def __init__(self):
        self._context = None
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_initialized(self):
        if self._initialized:
            return
        async with self._init_lock:
            if not self._initialized:
                await self._init_browser()
                self._initialized = True

    async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
        await self._ensure_initialized()  # Wait for init before spawning tasks
        # ... rest of method
```

### Option 2: Initialize Before Gather
```python
async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
    # Force initialization before concurrent access
    if self.context is None:
        await self._init_browser()

    # Now safe to spawn concurrent tasks
    tasks = [self._fetch_single(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Test Cases
1. Call `fetch_multiple()` with 10+ URLs on fresh BrowserTool instance
2. Verify no "NoneType has no attribute" errors
3. Verify all URLs are attempted (may still fail for other reasons)
4. Check log shows "Browser initialized" before any "Navigating to" messages

## Acceptance Criteria
- [ ] No `'NoneType' object has no attribute 'new_page'` errors in logs
- [ ] Browser initialization completes before any page navigation
- [ ] All URLs in `fetch_multiple()` are attempted
- [ ] Concurrent performance maintained (don't serialize all fetches)

## Related Issues
- BUG-037: Error sources in output (some caused by this bug)
- TECH-033: Error count mismatch (affected by silent failures)

## Labels
`critical`, `bug`, `browser`, `race-condition`, `data-loss`
