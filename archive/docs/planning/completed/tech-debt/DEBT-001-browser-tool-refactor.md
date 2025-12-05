# DEBT-001: Browser Tool Modularization

## Problem Statement

The current browser tool is a monolithic class that handles initialization, navigation, extraction, and closing. This violates the Single Responsibility Principle and makes testing hard.

## Proposed Solution

Refactor the browser tool into smaller, focused components as seen in `crawl4ai`:

- `BrowserManager`: Handles Playwright lifecycle.
- `NavigationHandler`: Handles goto, wait, and scrolling.
- `ExtractionHandler`: Handles content retrieval.

## Implementation Steps

1.  Create `browser/` directory.
2.  Extract `BrowserManager` class.
3.  Extract `Navigator` class.
4.  Update the main tool to compose these classes.

## Code Example

```python
class BrowserManager:
    async def get_context(self): ...

class Navigator:
    async def goto(self, page, url): ...
```

## Acceptance Criteria

- [ ] Code is split into multiple files/classes.
- [ ] Each class has a single responsibility.
- [ ] Unit tests can mock individual components.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/browser_manager.py`
