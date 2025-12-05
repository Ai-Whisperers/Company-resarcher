"""
Tavily Search Provider - Existing provider wrapped in new interface.

Cost: 1,000 free/month, then $0.008/request ($8/1K)
Quality: Excellent, AI-optimized results
"""

import asyncio
import os
from typing import List, Optional
from src.tools.search.base import SearchProvider, SearchResult, SearchError, RateLimitError
from src.core.logging import setup_logger
from src.core.config import get_settings

logger = setup_logger("search.tavily")

# Import timeout from environment
SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "30"))


class TavilyProvider(SearchProvider):
    """
    Tavily search provider - AI-optimized search results.

    Priority: 5 (fifth choice, most expensive)
    Cost: 1,000 free/month, then $8/1K
    Quality: Excellent (AI-optimized)
    """

    name = "tavily"
    priority = 5  # Lower priority due to cost

    def __init__(self, api_key: Optional[str] = None, timeout: int = None):
        """
        Initialize Tavily provider.

        Args:
            api_key: Tavily API key (or uses TAVILY_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self.timeout = timeout or SEARCH_TIMEOUT_SECONDS
        self._client = None

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from init or environment."""
        if self._api_key:
            return self._api_key
        settings = get_settings()
        if settings.TAVILY_API_KEY:
            return settings.TAVILY_API_KEY.get_secret_value()
        return None

    def _get_client(self):
        """Lazy load Tavily client."""
        if self._client is None:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                raise SearchError(
                    "tavily-python not installed. Install with: pip install tavily-python",
                    self.name
                )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        include_images: bool = False,
        include_raw_content: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Execute a Tavily search with enhanced options (INT-007).

        Args:
            query: Search query string
            max_results: Maximum results (default 10)
            include_images: Include image URLs in results
            include_raw_content: Include full raw HTML content
            include_domains: Only include results from these domains
            exclude_domains: Exclude results from these domains

        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            raise SearchError("Tavily API key not configured", self.name, query)

        if not query or not query.strip():
            logger.warning("Empty query provided to Tavily")
            return []

        try:
            client = self._get_client()

            # Build search kwargs
            search_kwargs = {
                "query": query,
                "search_depth": "advanced",
                "max_results": min(max_results, 20),  # Tavily max is 20
                "include_raw_content": include_raw_content,
                "include_images": include_images,
            }

            # Add domain filtering if specified
            if include_domains:
                search_kwargs["include_domains"] = include_domains
            if exclude_domains:
                search_kwargs["exclude_domains"] = exclude_domains

            # Run in thread because Tavily client is synchronous
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.search,
                    **search_kwargs
                ),
                timeout=self.timeout
            )

            results = []
            for item in response.get("results", []):
                raw_data = dict(item)

                # Add images to raw_data if available
                if include_images and "images" in response:
                    raw_data["images"] = response.get("images", [])

                results.append(SearchResult(
                    title=item.get("title", "No Title"),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=self.name,
                    score=item.get("score"),
                    raw_data=raw_data
                ))

            logger.info(f"Tavily found {len(results)} results for '{query[:50]}...'")
            return results

        except asyncio.TimeoutError:
            logger.error(f"Tavily timed out after {self.timeout}s for '{query[:30]}...'")
            raise SearchError("Request timed out", self.name, query)
        except Exception as e:
            error_str = str(e).lower()

            # Check for rate limiting / quota exceeded (expanded patterns for BUG-038)
            rate_limit_patterns = [
                "usage limit",
                "rate limit",
                "ratelimit",
                "quota",
                "exceeds your plan",
                "exceeded your plan",
                "upgrade your plan",
                "too many requests",
                "limit exceeded",
                "limit reached",
                "api limit",
                "daily limit",
                "monthly limit",
                "request limit",
                "credits",
                "429",
                "throttl",  # throttle, throttled, throttling
            ]
            if any(pattern in error_str for pattern in rate_limit_patterns):
                logger.warning(f"Tavily rate limited: {e}")
                raise RateLimitError(self.name, query)

            logger.error(f"Tavily search failed: {e}")
            raise SearchError(str(e), self.name, query)

    async def search_with_images(
        self,
        query: str,
        max_results: int = 10,
    ) -> dict:
        """
        Search and return both results and images.

        Args:
            query: Search query string
            max_results: Maximum results

        Returns:
            Dictionary with 'results' and 'images' keys
        """
        if not self.api_key:
            raise SearchError("Tavily API key not configured", self.name, query)

        try:
            client = self._get_client()

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.search,
                    query=query,
                    search_depth="advanced",
                    max_results=min(max_results, 20),
                    include_images=True,
                ),
                timeout=self.timeout
            )

            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", "No Title"),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=self.name,
                    score=item.get("score"),
                    raw_data=item
                ))

            return {
                "results": results,
                "images": response.get("images", []),
            }

        except Exception as e:
            logger.error(f"Tavily search_with_images failed: {e}")
            raise SearchError(str(e), self.name, query)

    async def search_news(
        self,
        query: str,
        max_results: int = 10,
        days: int = 7,
    ) -> List[SearchResult]:
        """
        Search for recent news articles.

        Args:
            query: Search query string
            max_results: Maximum results
            days: Number of days to look back (default 7)

        Returns:
            List of SearchResult objects from news sources
        """
        if not self.api_key:
            raise SearchError("Tavily API key not configured", self.name, query)

        try:
            client = self._get_client()

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.search,
                    query=query,
                    search_depth="advanced",
                    max_results=min(max_results, 20),
                    topic="news",
                    days=days,
                ),
                timeout=self.timeout
            )

            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", "No Title"),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=self.name,
                    score=item.get("score"),
                    raw_data=item
                ))

            logger.info(f"Tavily news search found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Tavily news search failed: {e}")
            raise SearchError(str(e), self.name, query)

    def is_available(self) -> bool:
        """Check if Tavily API key is configured."""
        return bool(self.api_key)
