# IMP-008: Browser Configuration Management

## Problem Statement

Browser settings (headless mode, user agent, viewport) are scattered across the codebase. Changing them requires editing multiple files.

## Proposed Solution

Centralize browser configuration using a `BrowserConfig` object, as done in `crawl4ai`.

## Implementation Steps

1.  Create `BrowserConfig` data class.
2.  Include fields for: `headless`, `user_agent`, `viewport`, `proxy`, `extra_args`.
3.  Pass this config object to the `Crawl4AITool` and `AsyncWebCrawler`.
4.  Load defaults from `config.yaml` or `.env`.

## Code Example

```python
@dataclass
class BrowserConfig:
    browser_type: str = "chromium"
    headless: bool = True
    user_agent: str = "Mozilla/5.0..."
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
```

## Acceptance Criteria

- [ ] All browser settings are in one place.
- [ ] Easy to switch user agents or toggle headless mode globally.
- [ ] Configuration is loaded from environment variables.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/async_configs.py`
