import asyncio
import os
import threading
from typing import Optional, List, Dict
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from ..core.logger import setup_logger
from ..core.types import ResearchSource
from ..core.url_validator import URLValidator, URLValidationError
from ..services.html_cache import get_html_cache

logger = setup_logger("browser_tool")

# Overall timeout for the entire fetch operation (default: 60 seconds)
FETCH_OVERALL_TIMEOUT = int(os.getenv("BROWSER_FETCH_TIMEOUT_SECONDS", "60"))

# Enable/disable HTML caching (default: True)
ENABLE_HTML_CACHE = os.getenv("ENABLE_HTML_CACHE", "true").lower() == "true"

# Combined CSS selector for main content (single query instead of sequential)
# This is O(1) instead of O(n) sequential queries
MAIN_CONTENT_SELECTOR = ", ".join([
    "article",
    "main",
    "[role='main']",
    ".content",
    "#content",
    ".post-content",
    ".entry-content",
    ".article-content",
    ".post-body",
    "#main-content",
])

# Cache for successful selectors by domain (PERF-003)
# Stores which selector worked best for each domain
_selector_cache: Dict[str, str] = {}
_selector_cache_lock = threading.Lock()


class BrowserTool:
    """
    Tool for fetching and parsing web content using Playwright.
    Handles dynamic content and basic anti-bot measures.
    Supports context manager for proper resource cleanup.
    """

    def __init__(self, max_concurrent: int = 5):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.max_concurrent = max_concurrent
        # Initialize semaphore immediately to avoid race condition
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)
        # Lock for thread-safe browser initialization (BUG-046)
        self._init_lock: asyncio.Lock = asyncio.Lock()
        self._cleanup_registered = False

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """Returns the semaphore for rate limiting."""
        return self._semaphore

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.stop()

    async def start(self):
        """Initialize the browser instance"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info("Browser initialized")

    async def stop(self):
        """Close the browser instance"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.info("Browser stopped")

    async def fetch_page(
        self, url: str, wait_for_selector: str = "body"
    ) -> ResearchSource:
        """
        Fetch a single page and extract its content with metadata.
        Includes overall timeout to prevent hanging on slow pages.
        """
        try:
            return await asyncio.wait_for(
                self._fetch_page_internal(url, wait_for_selector),
                timeout=FETCH_OVERALL_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Overall fetch timeout ({FETCH_OVERALL_TIMEOUT}s) for {url}")
            return ResearchSource(
                url=url,
                title="Fetch Timeout",
                content=f"Error: Overall fetch timed out after {FETCH_OVERALL_TIMEOUT} seconds",
                source_type="error",
                category="error",
            )

    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF file (BUG-051)."""
        url_lower = url.lower()
        return (
            url_lower.endswith('.pdf') or
            '/pdf/' in url_lower or
            'download=pdf' in url_lower or
            'format=pdf' in url_lower or
            'type=pdf' in url_lower
        )

    async def _fetch_page_internal(
        self, url: str, wait_for_selector: str = "body"
    ) -> ResearchSource:
        """
        Internal fetch implementation wrapped by fetch_page for timeout.
        """
        # Validate URL to prevent SSRF attacks
        try:
            URLValidator.validate_url(url)
        except URLValidationError as e:
            logger.warning(f"URL validation failed for {url}: {e}")
            return ResearchSource(
                url=url,
                title="URL Validation Failed",
                content=f"Error: URL blocked for security reasons - {e}",
                source_type="error",
                category="error",
            )

        # Skip PDF URLs - browser can't render them properly (BUG-051)
        if self._is_pdf_url(url):
            logger.info(f"Skipping PDF URL (not supported): {url}")
            return ResearchSource(
                url=url,
                title="PDF Document (Not Extracted)",
                content="PDF documents are not currently supported for content extraction. "
                        "Consider adding a PDF extraction library like PyMuPDF.",
                source_type="pdf",
                category="document",
            )

        # Use lock for thread-safe initialization (BUG-046)
        if not self.browser:
            async with self._init_lock:
                if not self.browser:  # Double-check after acquiring lock
                    await self.start()

        page = None
        try:
            page = await self.browser.new_page()
            logger.info(f"Navigating to: {url}")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")

            # Wait for content to load
            try:
                await page.wait_for_selector(wait_for_selector, timeout=5000)
            except asyncio.TimeoutError:
                logger.warning(
                    f"Timeout waiting for selector '{wait_for_selector}' on {url}"
                )
            except Exception as e:
                logger.warning(
                    f"Error waiting for selector '{wait_for_selector}' on {url}: {e}"
                )

            # Get content
            content = await page.content()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Extract Metadata
            metadata = self._extract_metadata(soup)
            title = metadata.get("title") or await page.title()

            # Cache raw HTML if enabled
            if ENABLE_HTML_CACHE:
                try:
                    html_cache = get_html_cache()
                    html_cache.save_html(
                        url=url,
                        html_content=content,
                        title=title,
                        fetch_status="success",
                    )
                except Exception as cache_error:
                    logger.debug(f"HTML cache error (non-fatal): {cache_error}")

            # Remove unwanted elements
            for element in soup.find_all(
                [
                    "script",
                    "style",
                    "nav",
                    "footer",
                    "header",
                    "aside",
                    "form",
                    "iframe",
                    "noscript",
                    "ads",
                    "advertising",
                ]
            ):
                element.decompose()

            # Smart Content Extraction (PERF-003 optimized)
            # Use combined selector for O(1) lookup instead of sequential O(n)
            domain = urlparse(url).netloc

            # Check if we have a cached selector for this domain
            cached_selector = None
            with _selector_cache_lock:
                cached_selector = _selector_cache.get(domain)

            main_content = None

            if cached_selector:
                # Try cached selector first (fast path for known domains)
                main_content = soup.select_one(cached_selector)

            if not main_content:
                # Use combined selector (single CSS query)
                main_content = soup.select_one(MAIN_CONTENT_SELECTOR)

                # If found, cache the specific selector that matched for this domain
                if main_content and main_content.name:
                    matched_selector = main_content.name
                    if main_content.get('id'):
                        matched_selector = f"#{main_content['id']}"
                    elif main_content.get('class'):
                        matched_selector = f".{main_content['class'][0]}"
                    elif main_content.get('role'):
                        matched_selector = f"[role='{main_content['role']}']"

                    with _selector_cache_lock:
                        _selector_cache[domain] = matched_selector
                    logger.debug(f"Cached selector '{matched_selector}' for domain {domain}")

            if not main_content:
                main_content = soup.body or soup

            text_content = main_content.get_text(separator="\n", strip=True)

            # Classify source type
            source_type = self.classify_source_type(url, text_content)

            return ResearchSource(
                url=url,
                title=title,
                content=text_content[:20000],  # Limit content size
                source_type=source_type,
                category="general",  # Will be updated by agent
            )

        except Exception as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return ResearchSource(
                url=url,
                title="Error Fetching Page",
                content=f"Error: {str(e)}",
                source_type="error",
                category="error",
            )
        finally:
            # Ensure page is always closed to prevent resource leaks
            if page is not None:
                try:
                    await page.close()
                except Exception as close_error:
                    logger.warning(f"Error closing page for {url}: {close_error}")

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML."""
        metadata = {}

        # Title
        if soup.title:
            metadata["title"] = soup.title.string

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            metadata["description"] = meta_desc.get("content", "")

        # Meta keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            metadata["keywords"] = meta_keywords.get("content", "")

        # Author
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author:
            metadata["author"] = meta_author.get("content", "")

        # Published date
        for attr in ["article:published_time", "datePublished", "pubdate"]:
            date_meta = soup.find("meta", attrs={"property": attr}) or soup.find(
                "meta", attrs={"name": attr}
            )
            if date_meta:
                metadata["published"] = date_meta.get("content", "")
                break

        return metadata

    def classify_source_type(self, url: str, content: str) -> str:
        """
        Classify the type of source based on URL and content.
        Ported from web_fetcher.py
        """
        url_lower = url.lower()
        content_lower = content.lower()

        # Check for specific source types
        if any(
            x in url_lower for x in ["statista", "euromonitor", "nielsen", "ibisworld"]
        ):
            return "industry_report"

        if any(x in url_lower for x in ["news", "press", "article", "blog"]):
            return "news_article"

        if any(x in url_lower for x in ["study", "research", "journal", "academic"]):
            return "academic"

        if any(
            x in url_lower
            for x in ["facebook", "twitter", "instagram", "linkedin", "tiktok"]
        ):
            return "social_media"

        if any(x in url_lower for x in ["gov", "gob", "gobierno"]):
            return "government"

        if "%" in content_lower or any(
            x in content_lower for x in ["growth", "market size", "revenue"]
        ):
            return "market_data"

        return "web"

    async def _fetch_with_semaphore(self, url: str) -> ResearchSource:
        """Fetch a page with rate limiting via semaphore."""
        async with self.semaphore:
            return await self.fetch_page(url)

    async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
        """
        Fetch multiple URLs concurrently with rate limiting.
        Uses semaphore to limit concurrent requests (default: 5).
        """
        tasks = [self._fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {result}")
                continue

            # result is already a ResearchSource from fetch_page
            if result and result.source_type != "error":
                sources.append(result)

        return sources
