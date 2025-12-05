"""
Serper.dev Search Provider - PAID but cheap Google results.

Cost: 2,500 free queries, then $1.00/1K queries
Speed: 1-2 seconds (fastest)
Quality: Google-quality results
"""

import asyncio
from typing import List, Optional

import aiohttp

from src.tools.search.base import SearchProvider, SearchResult, SearchError, RateLimitError
from src.core.logging import setup_logger
from src.core.config import get_settings
from src.infrastructure.network.http_client import get_http_client

logger = setup_logger("search.serper")


class SerperProvider(SearchProvider):
    """
    Serper.dev search provider - Fast, cheap Google results.

    Priority: 4 (fourth choice, paid)
    Cost: 2,500 free, then $1.00/1K → $0.30/1K at scale
    Rate Limit: 300 queries/second
    Quality: Excellent (Google results)
    """

    name = "serper"
    priority = 4

    API_URL = "https://google.serper.dev/search"
    NEWS_URL = "https://google.serper.dev/news"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize Serper provider.

        Args:
            api_key: Serper API key (or uses SERPER_API_KEY env var)
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
        # Check for SERPER_API_KEY in settings
        serper_key = getattr(settings, "SERPER_API_KEY", None)
        if serper_key:
            return (
                serper_key.get_secret_value()
                if hasattr(serper_key, "get_secret_value")
                else serper_key
            )
        return None

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Execute a Serper (Google) search.

        Args:
            query: Search query string
            max_results: Maximum results (default 10)

        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            raise SearchError("Serper API key not configured", self.name, query)

        if not query or not query.strip():
            logger.warning("Empty query provided to Serper")
            return []

        try:
            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.post(
                self.API_URL,
                rate_limit_key="serper",
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": min(max_results, 100),  # Serper max is 100
                },
            )

            async with response:
                if response.status == 429:
                    raise RateLimitError(self.name, query)

                if response.status == 401:
                    raise SearchError("Invalid API key", self.name, query)

                if response.status != 200:
                    text = await response.text()
                    raise SearchError(
                        f"HTTP {response.status}: {text[:200]}", self.name, query
                    )

                data = await response.json()
                return self._parse_results(data, max_results)

        except aiohttp.ClientError as e:
            # Sanitize error message to prevent API key leakage
            # Some aiohttp exceptions may include request headers in their repr
            safe_error = str(type(e).__name__)
            logger.error(f"Serper network error: {safe_error}")
            raise SearchError(f"Network error: {safe_error}", self.name, query)
        except asyncio.TimeoutError:
            logger.error(f"Serper request timed out for '{query[:30]}...'")
            raise SearchError("Request timed out", self.name, query)

    def _parse_results(self, data: dict, max_results: int) -> List[SearchResult]:
        """Parse Serper API response."""
        results = []

        # Organic results
        for item in data.get("organic", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", "No Title"),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    score=item.get("position"),
                    raw_data=item,
                )
            )

        # Include knowledge graph if present
        kg = data.get("knowledgeGraph")
        if kg and len(results) < max_results:
            results.insert(
                0,
                SearchResult(
                    title=kg.get("title", "Knowledge Graph"),
                    url=kg.get("website", kg.get("descriptionLink", "")),
                    snippet=kg.get("description", ""),
                    source=f"{self.name}_kg",
                    raw_data=kg,
                ),
            )

        logger.info(f"Serper found {len(results)} results for query")
        return results[:max_results]

    async def search_news(
        self, query: str, max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search Google News via Serper.

        Args:
            query: Search query string
            max_results: Maximum results

        Returns:
            List of SearchResult objects with news articles
        """
        if not self.api_key:
            raise SearchError("Serper API key not configured", self.name, query)

        try:
            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.post(
                self.NEWS_URL,
                rate_limit_key="serper",
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": min(max_results, 100),
                },
            )

            async with response:
                if response.status != 200:
                    raise SearchError(f"HTTP {response.status}", self.name, query)

                data = await response.json()

                results = []
                for item in data.get("news", [])[:max_results]:
                    results.append(
                        SearchResult(
                            title=item.get("title", "No Title"),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source=f"{self.name}_news",
                            published_date=item.get("date"),
                            raw_data=item,
                        )
                    )

                logger.info(f"Serper News found {len(results)} results")
                return results

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # Sanitize error message to prevent API key leakage
            safe_error = str(type(e).__name__)
            logger.error(f"Serper news search failed: {safe_error}")
            raise SearchError(safe_error, self.name, query)

    def is_available(self) -> bool:
        """Check if Serper API key is configured."""
        return bool(self.api_key)
