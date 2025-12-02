# BUG-005: Browser Tool Exception Handling

## Priority: High
## Category: Bug / Code Quality
## Status: Backlog

## Summary

`src/tools/browser.py` has generic exception handlers that can cause resource leaks and mask browser automation errors.

## Affected Lines

| Line | Issue |
|------|-------|
| 119 | Generic exception in page creation |
| 184 | Generic exception in content extraction |
| 198 | Generic exception in navigation |

## Current Code

```python
async def scrape(self, url: str) -> dict:
    try:
        page = await self.context.new_page()
        await page.goto(url)
        content = await page.content()
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        return {"error": str(e)}
    finally:
        await page.close()  # Might fail if page not created!
```

## Problems

1. `page` might not exist in `finally` block
2. Network errors treated same as browser crashes
3. Timeout errors not distinguished
4. Resource leaks on certain failure paths

## Proposed Fix

```python
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import Error as PlaywrightError

class BrowserError(Exception):
    """Base browser tool error."""
    pass

class BrowserTimeoutError(BrowserError):
    """Page load or operation timed out."""
    pass

class BrowserNavigationError(BrowserError):
    """Failed to navigate to URL."""
    pass

async def scrape(self, url: str) -> dict:
    page = None
    try:
        page = await self.context.new_page()

        try:
            await page.goto(url, timeout=30000)
        except PlaywrightTimeout:
            raise BrowserTimeoutError(f"Page load timeout: {url}")
        except PlaywrightError as e:
            if "net::" in str(e):
                raise BrowserNavigationError(f"Network error: {e}")
            raise

        content = await self._extract_content(page)
        return {"content": content, "url": url}

    except BrowserTimeoutError as e:
        logger.warning(f"Timeout scraping {url}: {e}")
        return {"error": str(e), "error_type": "timeout"}
    except BrowserNavigationError as e:
        logger.warning(f"Navigation failed for {url}: {e}")
        return {"error": str(e), "error_type": "navigation"}
    except PlaywrightError as e:
        logger.error(f"Browser error scraping {url}: {e}", exc_info=True)
        return {"error": str(e), "error_type": "browser"}
    except Exception as e:
        logger.exception(f"Unexpected error scraping {url}")
        return {"error": str(e), "error_type": "unknown"}
    finally:
        if page is not None:
            try:
                await page.close()
            except Exception as e:
                logger.warning(f"Failed to close page: {e}")
```

## Implementation Tasks

- [ ] Create browser-specific exception classes
- [ ] Initialize `page = None` before try block
- [ ] Handle Playwright-specific exceptions
- [ ] Add error_type to return dict
- [ ] Ensure page always closed
- [ ] Add retry logic for timeouts

## Success Criteria

- No resource leaks on any failure path
- Error types distinguished in responses
- Timeouts handled gracefully
- Full exception context logged
