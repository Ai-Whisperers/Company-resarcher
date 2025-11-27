# Feature: Browser Agent

## Source

- **Repository:** `OpenHands/OpenHands`
- **File:** `openhands/runtime/browser/browser_env.py`

## Description

Go beyond simple scraping. Give the agent full control over a browser (Playwright/Selenium) to interact with complex SPAs, fill forms, and navigate.

## Implementation Details

1.  **Playwright:** Use `playwright` for browser automation.
2.  **Action Space:** Define actions: `click(selector)`, `type(text)`, `scroll(x, y)`, `goto(url)`.
3.  **Observation:** Return the DOM tree (simplified) and a screenshot after each action.
4.  **Accessibility Tree:** Use the accessibility tree for a more token-efficient representation of the page.

## Code Reference

```python
async def execute_browser_action(action):
    if action.type == "click":
        await page.click(action.selector)
    elif action.type == "type":
        await page.fill(action.selector, action.text)
```
