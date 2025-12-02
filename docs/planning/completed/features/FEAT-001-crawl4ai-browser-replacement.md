# FEAT-001: Replace Browser Tool with Crawl4AI

## Problem Statement

The current browser tool is basic and lacks advanced capabilities like anti-bot detection, smart caching, and efficient resource handling. It is not optimized for heavy data extraction tasks.

## Proposed Solution

Replace the existing browser tool with the `AsyncWebCrawler` from the `crawl4ai` library. This will provide a robust, production-grade web crawling solution with built-in support for:

- Playwright for browser automation
- Anti-bot detection mechanisms
- Smart caching and rate limiting
- Markdown generation from HTML

## Implementation Steps

1.  Add `crawl4ai` to `requirements.txt`.
2.  Create a new `Crawl4AITool` class that wraps `AsyncWebCrawler`.
3.  Implement `arun` method to handle URL crawling.
4.  Map `crawl4ai` configuration options (headless, user_agent, etc.) to tool arguments.
5.  Replace usages of the old browser tool with the new `Crawl4AITool`.

## Code Example

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def crawl_url(url: str):
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(cache_mode="ENABLED")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return result.markdown
```

## Acceptance Criteria

- [ ] `Crawl4AITool` is implemented and registered.
- [ ] Tool successfully crawls a target URL and returns markdown.
- [ ] Caching is working (second request to same URL is faster).
- [ ] Old browser tool is deprecated or removed.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/async_webcrawler.py`
