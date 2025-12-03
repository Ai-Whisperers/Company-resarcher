"""
DuckDuckGo Search Provider - FREE, no API key required.

Uses the ddgs library (formerly duckduckgo-search) to search the web.
This is the primary provider due to being completely free.

Limitations:
- Rate limited (but generous for normal use)
- Results may be less comprehensive than Google
- No advanced filtering options
"""

import asyncio
from typing import List
from .base import SearchProvider, SearchResult, SearchError, RateLimitError
from ...core.logger import setup_logger
from ...utils.url_utils import get_ddg_region

logger = setup_logger("search.duckduckgo")

# Lazy import to avoid loading if not needed
_DDGS = None


def _get_ddgs():
    """Lazy load DDGS to avoid import errors if not installed."""
    global _DDGS
    if _DDGS is None:
        try:
            # Try new package name first
            from ddgs import DDGS
            _DDGS = DDGS
        except ImportError:
            try:
                # Fall back to old package name
                from duckduckgo_search import DDGS
                _DDGS = DDGS
            except ImportError:
                raise ImportError(
                    "ddgs not installed. "
                    "Install with: pip install ddgs"
                )
    return _DDGS


class DuckDuckGoProvider(SearchProvider):
    """
    DuckDuckGo search provider - FREE, no API key required.

    Priority: 1 (highest - used first in fallback chain)
    Cost: FREE
    Rate Limit: Generous but present
    Quality: Good for general searches
    """

    name = "duckduckgo"
    priority = 1  # Highest priority (free)

    def __init__(self, timeout: int = None, proxy: str = None, region: str = "wt-wt"):
        """
        Initialize DuckDuckGo provider.

        Args:
            timeout: Request timeout in seconds (default from SEARCH_TIMEOUT_SECONDS env var or 60s)
            proxy: Optional proxy URL (e.g., "http://user:pass@host:port")
            region: Search region (default "wt-wt" for worldwide neutral results,
                    "us-en" for US English). Using "wt-wt" to avoid locale-based
                    routing that can return non-English results (BUG-048).
        """
        # Use environment variable if no timeout specified (default 60s for slow DuckDuckGo responses)
        if timeout is None:
            import os
            timeout = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "60"))
        self.timeout = timeout
        self.proxy = proxy
        self.region = region
        self._ddgs = None

    def _get_client(self):
        """Get or create DDGS client."""
        if self._ddgs is None:
            DDGS = _get_ddgs()
            self._ddgs = DDGS(timeout=self.timeout, proxy=self.proxy)
        return self._ddgs

    async def search(
        self,
        query: str,
        max_results: int = 10,
        country_tld: str = None,
    ) -> List[SearchResult]:
        """
        Execute a DuckDuckGo search.

        Args:
            query: Search query string
            max_results: Maximum results (default 10)
            country_tld: Optional country TLD for region-specific search (BUG-049)
                        e.g., "py" for Paraguay, "ar" for Argentina

        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to DuckDuckGo")
            return []

        # Determine region: use country_tld if provided, else default region
        search_region = get_ddg_region(country_tld) if country_tld else self.region
        
        try:
            ddgs = self._get_client()

            # Run sync DDGS in thread pool
            # Request more results than needed to account for DuckDuckGo's
            # tendency to return fewer results (TECH-030)
            request_count = max(max_results * 2, 15)
            
            logger.debug(f"DuckDuckGo search region: {search_region} (BUG-049)")

            loop = asyncio.get_event_loop()
            raw_results = await loop.run_in_executor(
                None,
                lambda: list(ddgs.text(
                    query,
                    region=search_region,
                    max_results=request_count,
                    safesearch="moderate",
                    backend="auto"  # Use auto backend for better result coverage (TECH-030)
                ))
            )

            # Trim to requested amount
            raw_results = raw_results[:max_results]

            results = []
            for r in raw_results:
                result = SearchResult(
                    title=r.get("title", "No Title"),
                    url=r.get("href", r.get("link", "")),
                    snippet=r.get("body", r.get("snippet", "")),
                    source=self.name,
                    raw_data=r
                )
                results.append(result)

            logger.info(f"DuckDuckGo found {len(results)} results for '{query[:50]}...'")
            return results

        except Exception as e:
            error_str = str(e).lower()

            # Check for rate limiting (expanded patterns for BUG-053)
            rate_limit_patterns = [
                "ratelimit", "rate limit", "rate-limit",
                "too many requests", "429", "throttl",
                "blocked", "captcha",
            ]
            if any(p in error_str for p in rate_limit_patterns):
                logger.warning(f"DuckDuckGo rate limited for '{query[:30]}...'")
                raise RateLimitError(self.name, query)

            # Other errors
            logger.error(f"DuckDuckGo search failed: {e}")
            raise SearchError(str(e), self.name, query)

    def is_available(self) -> bool:
        """
        DuckDuckGo is always available (no API key required).
        """
        try:
            _get_ddgs()
            return True
        except ImportError:
            return False

    async def search_news(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search DuckDuckGo news.

        Args:
            query: Search query string
            max_results: Maximum results

        Returns:
            List of SearchResult objects with news articles
        """
        if not query or not query.strip():
            return []

        try:
            ddgs = self._get_client()

            loop = asyncio.get_event_loop()
            raw_results = await loop.run_in_executor(
                None,
                lambda: list(ddgs.news(query, max_results=max_results))
            )

            results = []
            for r in raw_results:
                result = SearchResult(
                    title=r.get("title", "No Title"),
                    url=r.get("url", r.get("link", "")),
                    snippet=r.get("body", r.get("excerpt", "")),
                    source=f"{self.name}_news",
                    published_date=r.get("date"),
                    raw_data=r
                )
                results.append(result)

            logger.info(f"DuckDuckGo News found {len(results)} results for '{query[:50]}...'")
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo news search failed: {e}")
            raise SearchError(str(e), self.name, query)
