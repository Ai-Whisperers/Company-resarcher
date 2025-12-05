"""
Brave Search Provider - Privacy-focused search with generous free tier.

Uses Brave's Web Search API for independent search results.
https://brave.com/search/api/

Cost: 2,000 free queries/month, then $5/1K queries ($3/1K at scale)
Quality: Excellent - independent index, not relying on Google/Bing
Privacy: No user tracking
"""

import asyncio
from typing import List, Optional

import aiohttp

from src.tools.search.base import SearchProvider, SearchResult, SearchError, RateLimitError
from src.core.logging import setup_logger
from src.core.config import get_settings
from src.infrastructure.network.http_client import get_http_client

logger = setup_logger("search.brave")


class BraveSearchProvider(SearchProvider):
    """
    Brave Search provider - Privacy-focused with free tier.

    Priority: 3 (alongside LangSearch, before expensive paid providers)
    Cost: 2,000 free/month, then $5/1K → $3/1K at scale
    Rate Limit: 1 request/second on free tier, 20/second on paid
    Quality: Excellent (independent index)
    """

    name = "brave"
    priority = 3  # Same as LangSearch

    API_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize Brave Search provider.

        Args:
            api_key: Brave Search API key (or uses BRAVE_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self.timeout = timeout

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from init or environment."""
        if self._api_key:
            return self._api_key
        settings = get_settings()
        key = getattr(settings, "BRAVE_API_KEY", None)
        if key:
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Execute a Brave Search query.

        Args:
            query: Search query string
            max_results: Maximum results (default 10, max 20)

        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            raise SearchError("Brave Search API key not configured", self.name, query)

        if not query or not query.strip():
            logger.warning("Empty query provided to Brave Search")
            return []

        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key,
            }

            params = {
                "q": query,
                "count": min(max_results, 20),  # Brave max is 20 per request
                "text_decorations": "false",  # Don't include bold markers
                "search_lang": "en",
                "safesearch": "moderate",
            }

            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.get(
                self.API_URL,
                rate_limit_key="brave",
                headers=headers,
                params=params,
            )

            async with response:
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        self.name,
                        query,
                        int(retry_after) if retry_after else 60,
                    )

                if response.status == 401:
                    raise SearchError("Invalid API key", self.name, query)

                if response.status == 403:
                    raise SearchError(
                        "API key expired or quota exceeded", self.name, query
                    )

                if response.status != 200:
                    text = await response.text()
                    raise SearchError(
                        f"HTTP {response.status}: {text[:200]}",
                        self.name,
                        query,
                    )

                data = await response.json()
                return self._parse_results(data, max_results)

        except aiohttp.ClientError as e:
            logger.error(f"Brave Search network error: {e}")
            raise SearchError(f"Network error: {e}", self.name, query)
        except asyncio.TimeoutError:
            logger.error(f"Brave Search request timed out for '{query[:30]}...'")
            raise SearchError("Request timed out", self.name, query)

    def _parse_results(self, data: dict, max_results: int) -> List[SearchResult]:
        """Parse Brave Search API response."""
        results = []

        # Web results
        web = data.get("web", {})
        for item in web.get("results", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", "No Title"),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source=self.name,
                    published_date=item.get("age"),  # e.g., "2 days ago"
                    raw_data=item,
                )
            )

        # Include featured snippet if present
        featured = data.get("featured_snippet")
        if featured and len(results) < max_results:
            results.insert(
                0,
                SearchResult(
                    title=featured.get("title", "Featured Snippet"),
                    url=featured.get("url", ""),
                    snippet=featured.get("description", ""),
                    source=f"{self.name}_featured",
                    raw_data=featured,
                ),
            )

        # Include knowledge graph / infobox if present
        infobox = data.get("infobox")
        if infobox and len(results) < max_results:
            results.insert(
                0,
                SearchResult(
                    title=infobox.get("title", "Infobox"),
                    url=infobox.get("url", ""),
                    snippet=infobox.get("description", ""),
                    source=f"{self.name}_infobox",
                    raw_data=infobox,
                ),
            )

        logger.info(f"Brave Search found {len(results)} results for query")
        return results[:max_results]

    async def search_news(
        self, query: str, max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search Brave News.

        Args:
            query: Search query string
            max_results: Maximum results

        Returns:
            List of SearchResult objects with news articles
        """
        if not self.api_key:
            raise SearchError("Brave Search API key not configured", self.name, query)

        news_url = "https://api.search.brave.com/res/v1/news/search"

        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key,
            }

            params = {
                "q": query,
                "count": min(max_results, 20),
            }

            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.get(
                news_url,
                rate_limit_key="brave",
                headers=headers,
                params=params,
            )

            async with response:
                if response.status == 429:
                    raise RateLimitError(self.name, query)

                if response.status != 200:
                    raise SearchError(f"HTTP {response.status}", self.name, query)

                data = await response.json()

                results = []
                for item in data.get("results", [])[:max_results]:
                    results.append(
                        SearchResult(
                            title=item.get("title", "No Title"),
                            url=item.get("url", ""),
                            snippet=item.get("description", ""),
                            source=f"{self.name}_news",
                            published_date=item.get("age"),
                            raw_data=item,
                        )
                    )

                logger.info(f"Brave News found {len(results)} results")
                return results

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Brave News search failed: {e}")
            raise SearchError(str(e), self.name, query)

    def is_available(self) -> bool:
        """Check if Brave Search API key is configured."""
        return bool(self.api_key)
