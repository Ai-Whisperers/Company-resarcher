"""
LangSearch Search Provider - FREE Web Search API.

Uses LangSearch's free web search API optimized for AI applications.
Provides high-quality results with optional long-text summaries.

API Docs: https://docs.langsearch.com/api/web-search-api
Dashboard: https://langsearch.com/dashboard

Cost: FREE for individuals and small teams
Quality: Excellent (hybrid keyword + vector search with reranking)
"""

import asyncio
from typing import List, Optional

import aiohttp

from ..base import SearchProvider, SearchResult, SearchError, RateLimitError
from src.core.logging import setup_logger
from src.core.config import get_settings
from src.core.network.http_client import get_http_client

logger = setup_logger("search.langsearch")


class LangSearchProvider(SearchProvider):
    """
    LangSearch search provider - FREE, AI-optimized results.

    Priority: 3 (after DuckDuckGo and Jina, before paid providers)
    Cost: FREE for individuals/small teams
    Rate Limit: Generous free tier
    Quality: Excellent (hybrid search with semantic reranking)
    Bonus: Returns long-form summaries of content
    """

    name = "langsearch"
    priority = 3  # After free providers, before expensive paid ones

    API_URL = "https://api.langsearch.com/v1/web-search"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        include_summary: bool = True,
    ):
        """
        Initialize LangSearch provider.

        Args:
            api_key: LangSearch API key (from dashboard or LANGSEARCH_API_KEY env)
            timeout: Request timeout in seconds
            include_summary: Whether to include long-form summaries (recommended)
        """
        self._api_key = api_key
        self.timeout = timeout
        self.include_summary = include_summary

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from init or environment."""
        if self._api_key:
            return self._api_key
        settings = get_settings()
        # Try to get from settings
        key = getattr(settings, "LANGSEARCH_API_KEY", None)
        if key:
            # Handle SecretStr if used
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        if not self.api_key:
            raise SearchError("LangSearch API key not configured", self.name)
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Execute a LangSearch web search.

        Args:
            query: Search query string
            max_results: Maximum results (1-10, LangSearch max)

        Returns:
            List of SearchResult objects with titles, URLs, snippets, and summaries
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to LangSearch")
            return []

        if not self.api_key:
            raise SearchError("LangSearch API key not configured", self.name, query)

        # LangSearch accepts 1-10 results
        count = min(max(1, max_results), 10)

        payload = {
            "query": query,
            "freshness": "noLimit",  # Options: oneDay, oneWeek, oneMonth, oneYear, noLimit
            "summary": self.include_summary,
            "count": count,
        }

        try:
            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.post(
                self.API_URL,
                rate_limit_key="langsearch",
                headers=self._get_headers(),
                json=payload,
            )

            async with response:
                # Check for rate limiting
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        self.name,
                        query,
                        int(retry_after) if retry_after else None,
                    )

                # Check for auth errors
                if response.status == 401:
                    raise SearchError("Invalid API key", self.name, query)

                if response.status == 403:
                    raise SearchError("Access forbidden - check API key permissions", self.name, query)

                if response.status != 200:
                    text = await response.text()
                    raise SearchError(
                        f"HTTP {response.status}: {text[:200]}",
                        self.name,
                        query,
                    )

                data = await response.json()
                return self._parse_response(data, max_results)

        except aiohttp.ClientError as e:
            logger.error(f"LangSearch network error: {e}")
            raise SearchError(f"Network error: {e}", self.name, query)
        except asyncio.TimeoutError:
            logger.error(f"LangSearch request timed out for '{query[:30]}...'")
            raise SearchError("Request timed out", self.name, query)

    def _parse_response(self, data: dict, max_results: int) -> List[SearchResult]:
        """
        Parse LangSearch API response.

        Response structure:
        {
            "code": 200,
            "log_id": "...",
            "data": {
                "_type": "SearchResponse",
                "webPages": {
                    "value": [
                        {
                            "id": "...",
                            "name": "Title",
                            "url": "https://...",
                            "snippet": "Brief excerpt",
                            "summary": "Long-form summary (if requested)",
                            "datePublished": "2024-01-01",
                            ...
                        }
                    ]
                }
            }
        }
        """
        results = []

        # Check response code
        code = data.get("code", 0)
        if code != 200:
            msg = data.get("msg", "Unknown error")
            logger.warning(f"LangSearch API returned code {code}: {msg}")
            return []

        # Extract web pages
        search_data = data.get("data", {})
        web_pages = search_data.get("webPages", {})
        items = web_pages.get("value", [])

        for item in items[:max_results]:
            # Use summary if available, otherwise snippet
            snippet = item.get("summary") or item.get("snippet", "")
            if len(snippet) > 500:
                snippet = snippet[:500] + "..."

            result = SearchResult(
                title=item.get("name", "No Title"),
                url=item.get("url", ""),
                snippet=snippet,
                source=self.name,
                published_date=item.get("datePublished"),
                score=item.get("score"),
                raw_data=item,
            )
            results.append(result)

        logger.info(f"LangSearch found {len(results)} results for query")
        return results

    async def search_with_freshness(
        self,
        query: str,
        freshness: str = "noLimit",
        max_results: int = 10,
    ) -> List[SearchResult]:
        """
        Search with time filter.

        Args:
            query: Search query
            freshness: Time filter - oneDay, oneWeek, oneMonth, oneYear, noLimit
            max_results: Maximum results

        Returns:
            List of SearchResult objects
        """
        if freshness not in ("oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"):
            logger.warning(f"Invalid freshness '{freshness}', using 'noLimit'")
            freshness = "noLimit"

        # Temporarily override for this search
        original_timeout = self.timeout
        try:
            if not self.api_key:
                raise SearchError("LangSearch API key not configured", self.name, query)

            count = min(max(1, max_results), 10)
            payload = {
                "query": query,
                "freshness": freshness,
                "summary": self.include_summary,
                "count": count,
            }

            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.post(
                self.API_URL,
                rate_limit_key="langsearch",
                headers=self._get_headers(),
                json=payload,
            )

            async with response:
                if response.status == 429:
                    raise RateLimitError(self.name, query)
                if response.status != 200:
                    text = await response.text()
                    raise SearchError(f"HTTP {response.status}: {text[:200]}", self.name, query)

                data = await response.json()
                return self._parse_response(data, max_results)

        except aiohttp.ClientError as e:
            raise SearchError(f"Network error: {e}", self.name, query)
        finally:
            self.timeout = original_timeout

    def is_available(self) -> bool:
        """Check if LangSearch API key is configured."""
        return bool(self.api_key)
