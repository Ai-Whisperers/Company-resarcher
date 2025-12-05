# Browserbase Integration Guide

## 1. Use Cases

Browserbase provides a serverless infrastructure for running headless browsers.

- **Stealth Scraping**: Avoid bot detection (Cloudflare, etc.) which often blocks local Playwright.
- **Scalability**: Run multiple browser sessions in parallel without consuming local RAM/CPU.
- **Debugging**: View live sessions and recordings of the browser actions.

## 2. Implementation Strategy

We should refactor `src/tools/browser` to support a "cloud" mode.

### Current vs. Proposed

- **Current**: Local `playwright` launch.
- **Proposed**: Connect to Browserbase WebSocket URL.

### Code Example

```python
from playwright.async_api import async_playwright

async def get_browser():
    # If BROWSERBASE_API_KEY is present
    if settings.BROWSERBASE_API_KEY:
        return await p.chromium.connect_over_cdp(
            f"wss://connect.browserbase.com?apiKey={settings.BROWSERBASE_API_KEY}"
        )
    # Fallback to local
    return await p.chromium.launch()
```

## 3. Integration with Stack

- **LangChain**: Can be used as a Tool.
- **Stagehand**: Browserbase's "Stagehand" library (downloaded in research) offers AI-driven controlling of the browser, which fits perfectly with our agentic approach.
