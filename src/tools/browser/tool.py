"""
Modular Browser Tool - High-Level Interface

Composes BrowserManager, Navigator, and ContentExtractor
to provide a clean interface for web content fetching.
"""

import asyncio
import os
from typing import Optional, List

import time

from .manager import BrowserManager, BrowserConfig
from .navigator import Navigator, NavigationResult
from .extractor import ContentExtractor, ExtractedContent, ExtractionConfig

from ...core.logger import setup_logger
from ...core.types import ResearchSource
from ...services.html_cache import get_html_cache
from ...core.url_cache import get_url_cache
from ...core.domain_filter import is_domain_allowed
from ...core.domain_timeout import get_timeout_for_url, get_timeout_manager, is_domain_circuit_open

logger = setup_logger("modular_browser_tool")

# Overall timeout for fetch operations (default: 60 seconds)
FETCH_OVERALL_TIMEOUT = int(os.getenv("BROWSER_FETCH_TIMEOUT_SECONDS", "60"))

# Enable/disable HTML caching (default: True)
ENABLE_HTML_CACHE = os.getenv("ENABLE_HTML_CACHE", "true").lower() == "true"


class ModularBrowserTool:
    """
    High-level browser tool composing modular components.

    Provides the same interface as the legacy BrowserTool
    but with better separation of concerns.

    Components:
    - BrowserManager: Handles Playwright lifecycle
    - Navigator: Handles navigation and waiting
    - ContentExtractor: Handles content extraction

    Usage:
        async with ModularBrowserTool() as browser:
            source = await browser.fetch_page("https://example.com")
            print(source.content)
    """

    def __init__(
        self,
        browser_config: Optional[BrowserConfig] = None,
        extraction_config: Optional[ExtractionConfig] = None,
    ):
        self.browser_manager = BrowserManager(browser_config)
        self.navigator = Navigator()
        self.extractor = ContentExtractor(extraction_config)

    async def __aenter__(self) -> "ModularBrowserTool":
        """Async context manager entry."""
        await self.browser_manager.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.browser_manager.stop()

    async def start(self) -> None:
        """Start the browser."""
        await self.browser_manager.start()

    async def stop(self) -> None:
        """Stop the browser."""
        await self.browser_manager.stop()

    @property
    def is_started(self) -> bool:
        """Check if browser is running."""
        return self.browser_manager.is_started

    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF file."""
        url_lower = url.lower()
        return (
            url_lower.endswith(".pdf")
            or "/pdf/" in url_lower
            or "download=pdf" in url_lower
            or "format=pdf" in url_lower
            or "type=pdf" in url_lower
        )

    async def fetch_page(
        self,
        url: str,
        wait_for_selector: str = "body",
        timeout_seconds: Optional[int] = None,
    ) -> ResearchSource:
        """
        Fetch a single page and extract its content.

        Performance optimizations (PERF-011, PERF-012, PERF-014):
        - Checks URL cache to avoid duplicate fetches
        - Filters blocked domains before fetching
        - Uses domain-based timeouts
        - Respects circuit breaker for failing domains

        Args:
            url: URL to fetch
            wait_for_selector: Selector to wait for before extraction
            timeout_seconds: Overall timeout for the operation

        Returns:
            ResearchSource with extracted content
        """
        # PERF-011: Check URL cache first (in-memory)
        url_cache = get_url_cache()
        cached = url_cache.get(url)
        if cached is not None:
            logger.debug(f"URL cache hit (memory): {url}")
            return cached

        # Check HTML disk cache if enabled (for resuming previous runs)
        if ENABLE_HTML_CACHE:
            try:
                html_cache = get_html_cache()
                cached_html = html_cache.get_cached_html(url)
                if cached_html is not None:
                    logger.info(f"HTML cache hit (disk): {url}")
                    # Re-extract content from cached HTML using extractor (sync method)
                    extracted = self.extractor.extract_from_html(
                        cached_html["html"],
                        url,
                        cached_html["title"],
                    )
                    result = ResearchSource(
                        url=url,
                        title=extracted.title,
                        content=extracted.text,
                        source_type=extracted.source_type,
                        category="cached",
                    )
                    # Also cache in memory for faster subsequent lookups
                    url_cache.put(url, result)
                    return result
            except Exception as cache_error:
                logger.debug(f"HTML cache read error (non-fatal): {cache_error}")

        # PERF-012: Check domain blocklist
        if not is_domain_allowed(url):
            logger.info(f"Blocked domain, skipping: {url}")
            result = ResearchSource(
                url=url,
                title="Blocked Domain",
                content="Domain is in blocklist (irrelevant or inaccessible)",
                source_type="blocked",
                category="filtered",
            )
            url_cache.put(url, result)
            return result

        # PERF-014: Check circuit breaker
        if is_domain_circuit_open(url):
            logger.info(f"Circuit breaker open, skipping: {url}")
            return ResearchSource(
                url=url,
                title="Circuit Breaker Open",
                content="Domain has too many consecutive failures, temporarily skipped",
                source_type="error",
                category="error",
            )

        # PERF-014: Get domain-specific timeout
        timeout = timeout_seconds or get_timeout_for_url(url)
        timeout_manager = get_timeout_manager()

        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                self._fetch_page_internal(url, wait_for_selector),
                timeout=timeout,
            )

            # Record success and cache result
            elapsed = time.time() - start_time
            timeout_manager.record_success(url, elapsed)
            url_cache.put(url, result)

            return result

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"Overall fetch timeout ({timeout}s) for {url}")
            timeout_manager.record_failure(url, is_timeout=True)
            url_cache.mark_failed(url)
            return ResearchSource(
                url=url,
                title="Fetch Timeout",
                content=f"Error: Overall fetch timed out after {timeout} seconds",
                source_type="error",
                category="error",
            )

    async def _fetch_page_internal(
        self,
        url: str,
        wait_for_selector: str = "body",
    ) -> ResearchSource:
        """Internal fetch implementation."""

        # Skip PDF URLs
        if self._is_pdf_url(url):
            logger.info(f"Skipping PDF URL: {url}")
            return ResearchSource(
                url=url,
                title="PDF Document (Not Extracted)",
                content="PDF documents require a separate PDF extraction tool.",
                source_type="pdf",
                category="document",
            )

        page = None
        try:
            # Get a page from the manager
            page = await self.browser_manager.get_page()

            # Navigate to the URL
            nav_result = await self.navigator.goto(page, url)

            if not nav_result.success:
                return ResearchSource(
                    url=url,
                    title="Navigation Failed",
                    content=f"Error: {nav_result.error}",
                    source_type="error",
                    category="error",
                )

            # Wait for content selector
            await self.navigator.wait_for_selector(page, wait_for_selector)

            # Extract content
            extracted = await self.extractor.extract_from_page(page, url)

            # Cache HTML if enabled
            if ENABLE_HTML_CACHE:
                try:
                    html_cache = get_html_cache()
                    html_cache.save_html(
                        url=url,
                        html_content=extracted.html,
                        title=extracted.title,
                        fetch_status="success",
                    )
                except Exception as cache_error:
                    logger.debug(f"HTML cache error (non-fatal): {cache_error}")

            return ResearchSource(
                url=nav_result.final_url,
                title=extracted.title,
                content=extracted.text,
                source_type=extracted.source_type,
                category="general",
            )

        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return ResearchSource(
                url=url,
                title="Error Fetching Page",
                content=f"Error: {str(e)}",
                source_type="error",
                category="error",
            )

        finally:
            if page:
                await self.browser_manager.release_page(page)

    async def fetch_multiple(
        self,
        urls: List[str],
        timeout_seconds: Optional[int] = None,
    ) -> List[ResearchSource]:
        """
        Fetch multiple URLs concurrently.

        Uses semaphore-based rate limiting from BrowserManager.

        Args:
            urls: List of URLs to fetch
            timeout_seconds: Timeout per URL

        Returns:
            List of ResearchSource objects
        """
        tasks = [self.fetch_page(url, timeout_seconds=timeout_seconds) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {result}")
                sources.append(
                    ResearchSource(
                        url=url,
                        title="Error",
                        content=f"Error: {str(result)}",
                        source_type="error",
                        category="error",
                    )
                )
            elif result.source_type != "error":
                sources.append(result)

        return sources

    async def fetch_with_scroll(
        self,
        url: str,
        scroll_count: int = 3,
        scroll_delay_ms: int = 500,
    ) -> ResearchSource:
        """
        Fetch a page with scrolling to trigger lazy-loaded content.

        Args:
            url: URL to fetch
            scroll_count: Number of scroll iterations
            scroll_delay_ms: Delay between scrolls

        Returns:
            ResearchSource with extracted content
        """
        page = None
        try:
            page = await self.browser_manager.get_page()

            nav_result = await self.navigator.goto(page, url)
            if not nav_result.success:
                return ResearchSource(
                    url=url,
                    title="Navigation Failed",
                    content=f"Error: {nav_result.error}",
                    source_type="error",
                    category="error",
                )

            # Scroll to trigger lazy loading
            for _ in range(scroll_count):
                await self.navigator.scroll_to_bottom(page, max_scrolls=1)
                await asyncio.sleep(scroll_delay_ms / 1000)

            # Wait for network to settle
            await self.navigator.wait_for_load_state(page, "networkidle", timeout_ms=5000)

            # Extract content
            extracted = await self.extractor.extract_from_page(page, url)

            return ResearchSource(
                url=nav_result.final_url,
                title=extracted.title,
                content=extracted.text,
                source_type=extracted.source_type,
                category="general",
            )

        except Exception as e:
            logger.error(f"Failed to fetch {url} with scroll: {e}")
            return ResearchSource(
                url=url,
                title="Error Fetching Page",
                content=f"Error: {str(e)}",
                source_type="error",
                category="error",
            )

        finally:
            if page:
                await self.browser_manager.release_page(page)
