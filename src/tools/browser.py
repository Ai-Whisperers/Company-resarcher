"""
Browser Tool with Pool Support (INT-005).

Provides web scraping capabilities using Playwright with optional browser pooling
for improved performance and resource management.
"""

import asyncio
import os
import threading
import time
from typing import Optional, List, Dict
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup
from ..core.logger import setup_logger
from ..core.types import ResearchSource
from ..core.url_validator import URLValidator, URLValidationError
from ..core.source_classifier import classify_source
from ..services.html_cache import get_html_cache

logger = setup_logger("browser_tool")

# Overall timeout for the entire fetch operation (default: 60 seconds)
FETCH_OVERALL_TIMEOUT = int(os.getenv("BROWSER_FETCH_TIMEOUT_SECONDS", "60"))

# Page navigation timeout in milliseconds (TECH-012: default: 30 seconds)
PAGE_NAVIGATION_TIMEOUT_MS = int(os.getenv("BROWSER_PAGE_TIMEOUT_MS", "30000"))

# Maximum concurrent browser pages (TECH-013: default: 5)
DEFAULT_MAX_CONCURRENT = int(os.getenv("BROWSER_MAX_CONCURRENT", "5"))

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

# Browser pool settings (INT-005)
BROWSER_POOL_SIZE = int(os.getenv("BROWSER_POOL_SIZE", "3"))
BROWSER_POOL_MAX_AGE_SECONDS = int(os.getenv("BROWSER_POOL_MAX_AGE", "300"))  # 5 min


class BrowserPool:
    """
    Browser context pool for reusing browser contexts (INT-005).

    Maintains a pool of browser contexts to avoid the overhead of
    creating new browsers for each request. Contexts are recycled
    periodically to prevent memory leaks.

    Usage:
        async with BrowserPool() as pool:
            page = await pool.acquire()
            try:
                await page.goto(url)
                content = await page.content()
            finally:
                await pool.release(page)
    """

    def __init__(
        self,
        pool_size: int = BROWSER_POOL_SIZE,
        max_age_seconds: int = BROWSER_POOL_MAX_AGE_SECONDS,
    ):
        self.pool_size = pool_size
        self.max_age_seconds = max_age_seconds
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._available_contexts: asyncio.Queue = asyncio.Queue()
        self._context_ages: Dict[int, float] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        self._total_created = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Initialize the browser and create initial pool of contexts."""
        async with self._lock:
            if self._initialized:
                return

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

            # Pre-create contexts
            for _ in range(self.pool_size):
                context = await self._create_context()
                await self._available_contexts.put(context)

            self._initialized = True
            logger.info(f"Browser pool started with {self.pool_size} contexts")

    async def stop(self):
        """Stop the pool and close all resources."""
        async with self._lock:
            if not self._initialized:
                return

            # Close all available contexts
            while not self._available_contexts.empty():
                try:
                    context = self._available_contexts.get_nowait()
                    await self._close_context(context)
                except asyncio.QueueEmpty:
                    break

            if self._browser:
                await self._browser.close()
                self._browser = None

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._initialized = False
            self._context_ages.clear()
            logger.info("Browser pool stopped")

    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with standard settings."""
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            java_script_enabled=True,
            bypass_csp=True,
        )
        context_id = id(context)
        self._context_ages[context_id] = time.time()
        self._total_created += 1
        logger.debug(f"Created browser context {context_id}")
        return context

    async def _close_context(self, context: BrowserContext):
        """Close a browser context and clean up."""
        context_id = id(context)
        try:
            await context.close()
            self._context_ages.pop(context_id, None)
            logger.debug(f"Closed browser context {context_id}")
        except Exception as e:
            logger.warning(f"Error closing context {context_id}: {e}")

    def _is_context_stale(self, context: BrowserContext) -> bool:
        """Check if a context has exceeded its max age."""
        context_id = id(context)
        created_at = self._context_ages.get(context_id, 0)
        return (time.time() - created_at) > self.max_age_seconds

    async def acquire(self) -> Page:
        """
        Acquire a page from the pool.

        Returns a new page from an available context. If the context
        is stale, it will be recycled with a fresh one.

        Returns:
            Playwright Page instance
        """
        if not self._initialized:
            await self.start()

        # Get a context from the pool
        context = await self._available_contexts.get()

        # Check if context is stale and needs recycling
        if self._is_context_stale(context):
            logger.debug(f"Recycling stale context {id(context)}")
            await self._close_context(context)
            context = await self._create_context()

        # Create a new page from the context
        page = await context.new_page()
        page.set_default_timeout(PAGE_NAVIGATION_TIMEOUT_MS)

        return page

    async def release(self, page: Page):
        """
        Release a page back to the pool.

        Closes the page and returns its context to the available pool.

        Args:
            page: Playwright Page instance to release
        """
        try:
            context = page.context
            await page.close()

            # Return context to pool
            await self._available_contexts.put(context)
        except Exception as e:
            logger.warning(f"Error releasing page to pool: {e}")
            # Create a replacement context if release failed
            try:
                new_context = await self._create_context()
                await self._available_contexts.put(new_context)
            except Exception as create_error:
                logger.error(f"Failed to create replacement context: {create_error}")

    @property
    def available_count(self) -> int:
        """Number of available contexts in the pool."""
        return self._available_contexts.qsize()

    @property
    def total_created(self) -> int:
        """Total number of contexts created (for metrics)."""
        return self._total_created


# Global browser pool instance (lazy initialized)
_browser_pool: Optional[BrowserPool] = None
_browser_pool_lock = asyncio.Lock()


async def get_browser_pool() -> BrowserPool:
    """Get or create the global browser pool instance."""
    global _browser_pool
    if _browser_pool is None:
        async with _browser_pool_lock:
            if _browser_pool is None:
                _browser_pool = BrowserPool()
                await _browser_pool.start()
    return _browser_pool


async def close_browser_pool():
    """Close the global browser pool."""
    global _browser_pool
    if _browser_pool is not None:
        await _browser_pool.stop()
        _browser_pool = None


class BrowserTool:
    """
    Tool for fetching and parsing web content using Playwright.
    Handles dynamic content and basic anti-bot measures.
    Supports context manager for proper resource cleanup.
    """

    def __init__(self, max_concurrent: int = DEFAULT_MAX_CONCURRENT):
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
            await page.goto(url, timeout=PAGE_NAVIGATION_TIMEOUT_MS, wait_until="domcontentloaded")

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

            # Fallback to domain name if title is empty or generic
            if not title or title.strip() in ("", "Untitled", "Document"):
                domain = urlparse(url).netloc
                title = domain.replace("www.", "") if domain else url[:50]

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

        Uses the configurable SourceTypeClassifier (TECH-027, TECH-028).
        Supports 15+ source types with regex patterns and scoring.
        """
        return classify_source(url, content)

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
