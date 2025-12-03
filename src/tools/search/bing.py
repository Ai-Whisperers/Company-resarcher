"""
Bing Search Provider - Microsoft's search engine (powers Edge browser search).

Uses Bing Web Search API v7.
https://docs.microsoft.com/en-us/bing/search-apis/bing-web-search/overview

Cost: 1,000 free calls/month (F0 tier), then pay-as-you-go
Quality: Excellent - Microsoft's own search index
"""

import asyncio
import aiohttp
from typing import List, Optional
from .base import SearchProvider, SearchResult, SearchError, RateLimitError
from ...core.logger import setup_logger
from ...core.config import get_settings

logger = setup_logger("search.bing")


class BingSearchProvider(SearchProvider):
    """
    Bing Search provider - Microsoft search (powers Edge).

    Priority: 4 (same tier as Serper)
    Cost: 1,000 free/month, then pay-as-you-go
    Rate Limit: 3 calls/second (free tier)
    Quality: Excellent (Microsoft's own index)
    """

    name = "bing"
    priority = 4  # Same tier as Serper (Google via API)

    API_URL = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize Bing Search provider.

        Args:
            api_key: Bing Search API key (or uses BING_API_KEY env var)
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
        key = getattr(settings, "BING_API_KEY", None)
        if key:
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Execute a Bing Search query.

        Args:
            query: Search query string
            max_results: Maximum results (default 10, max 50)

        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            raise SearchError("Bing Search API key not configured", self.name, query)

        if not query or not query.strip():
            logger.warning("Empty query provided to Bing Search")
            return []

        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key,
            }

            params = {
                "q": query,
                "count": min(max_results, 50),  # Bing max is 50 per request
                "mkt": "en-US",  # Market for results
                "safeSearch": "Moderate",
                "textFormat": "Raw",  # Return raw text, not HTML decorated
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.API_URL,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:

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
                        raise SearchError("API key expired or quota exceeded", self.name, query)

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
            logger.error(f"Bing Search network error: {e}")
            raise SearchError(f"Network error: {e}", self.name, query)
        except asyncio.TimeoutError:
            logger.error(f"Bing Search request timed out for '{query[:30]}...'")
            raise SearchError("Request timed out", self.name, query)

    def _parse_results(self, data: dict, max_results: int) -> List[SearchResult]:
        """Parse Bing Search API response."""
        results = []

        # Web pages
        web_pages = data.get("webPages", {})
        for item in web_pages.get("value", [])[:max_results]:
            results.append(SearchResult(
                title=item.get("name", "No Title"),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                source=self.name,
                published_date=item.get("dateLastCrawled"),
                raw_data=item,
            ))

        # Include computation if present (for math/unit queries)
        computation = data.get("computation")
        if computation and len(results) < max_results:
            results.insert(0, SearchResult(
                title=f"Computation: {computation.get('expression', '')}",
                url="",
                snippet=f"= {computation.get('value', '')}",
                source=f"{self.name}_computation",
                raw_data=computation,
            ))

        # Include time zone if present
        time_zone = data.get("timeZone")
        if time_zone and len(results) < max_results:
            primary = time_zone.get("primaryCityTime", {})
            results.insert(0, SearchResult(
                title=f"Time in {primary.get('location', 'Unknown')}",
                url="",
                snippet=primary.get("time", ""),
                source=f"{self.name}_timezone",
                raw_data=time_zone,
            ))

        logger.info(f"Bing Search found {len(results)} results for query")
        return results[:max_results]

    async def search_news(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search Bing News.

        Args:
            query: Search query string
            max_results: Maximum results

        Returns:
            List of SearchResult objects with news articles
        """
        if not self.api_key:
            raise SearchError("Bing Search API key not configured", self.name, query)

        news_url = "https://api.bing.microsoft.com/v7.0/news/search"

        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key,
            }

            params = {
                "q": query,
                "count": min(max_results, 100),  # News allows more results
                "mkt": "en-US",
                "safeSearch": "Moderate",
                "freshness": "Week",  # Last week's news
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    news_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:

                    if response.status == 429:
                        raise RateLimitError(self.name, query)

                    if response.status != 200:
                        text = await response.text()
                        raise SearchError(f"HTTP {response.status}", self.name, query)

                    data = await response.json()

                    results = []
                    for item in data.get("value", [])[:max_results]:
                        results.append(SearchResult(
                            title=item.get("name", "No Title"),
                            url=item.get("url", ""),
                            snippet=item.get("description", ""),
                            source=f"{self.name}_news",
                            published_date=item.get("datePublished"),
                            raw_data=item,
                        ))

                    logger.info(f"Bing News found {len(results)} results")
                    return results

        except Exception as e:
            logger.error(f"Bing News search failed: {e}")
            raise SearchError(str(e), self.name, query)

    async def search_images(
        self, query: str, max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search Bing Images.

        Args:
            query: Search query string
            max_results: Maximum results

        Returns:
            List of SearchResult objects with image URLs
        """
        if not self.api_key:
            raise SearchError("Bing Search API key not configured", self.name, query)

        images_url = "https://api.bing.microsoft.com/v7.0/images/search"

        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key,
            }

            params = {
                "q": query,
                "count": min(max_results, 150),  # Images allows many results
                "mkt": "en-US",
                "safeSearch": "Moderate",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    images_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:

                    if response.status == 429:
                        raise RateLimitError(self.name, query)

                    if response.status != 200:
                        text = await response.text()
                        raise SearchError(f"HTTP {response.status}", self.name, query)

                    data = await response.json()

                    results = []
                    for item in data.get("value", [])[:max_results]:
                        results.append(SearchResult(
                            title=item.get("name", "No Title"),
                            url=item.get("contentUrl", item.get("thumbnailUrl", "")),
                            snippet=item.get("hostPageDisplayUrl", ""),
                            source=f"{self.name}_images",
                            raw_data=item,
                        ))

                    logger.info(f"Bing Images found {len(results)} results")
                    return results

        except Exception as e:
            logger.error(f"Bing Image search failed: {e}")
            raise SearchError(str(e), self.name, query)

    def is_available(self) -> bool:
        """Check if Bing Search API key is configured."""
        return bool(self.api_key)
