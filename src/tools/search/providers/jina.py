"""
Jina AI Search Provider - FREE (10M tokens).

Uses Jina AI's free Reader API for web search and content extraction.
- Search: https://s.jina.ai/?q=query
- Read: https://r.jina.ai/url

Cost: FREE for first 10M tokens, then ~$0.02/M tokens
No API key required for basic usage.
"""

import asyncio
from typing import List, Optional
from urllib.parse import quote_plus

import aiohttp

from ..base import SearchProvider, SearchResult, SearchError, RateLimitError
from src.core.logging import setup_logger
from src.core.network.http_client import get_http_client

logger = setup_logger("search.jina")


class JinaSearchProvider(SearchProvider):
    """
    Jina AI search provider - FREE (10M tokens).

    Priority: 2 (second choice after DuckDuckGo)
    Cost: FREE (10M tokens), then $0.02/M tokens
    Rate Limit: Generous free tier
    Quality: Good, with built-in content extraction
    Bonus: Can also read/extract content from URLs
    """

    name = "jina"
    priority = 2

    # Jina API endpoints
    SEARCH_URL = "https://s.jina.ai/"
    READER_URL = "https://r.jina.ai/"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Jina provider.

        Args:
            api_key: Optional API key (for higher limits)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> dict:
        """Get request headers."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "CompanyResearcher/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Execute a Jina search.

        Args:
            query: Search query string
            max_results: Maximum results (Jina returns top 5 by default)

        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to Jina")
            return []

        try:
            encoded_query = quote_plus(query)
            url = f"{self.SEARCH_URL}?q={encoded_query}"

            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.get(
                url,
                rate_limit_key="jina",
                headers=self._get_headers(),
            )

            async with response:
                if response.status == 429:
                    raise RateLimitError(self.name, query)

                if response.status != 200:
                    text = await response.text()
                    raise SearchError(
                        f"HTTP {response.status}: {text[:200]}",
                        self.name,
                        query
                    )

                # Try to parse as JSON, fall back to text
                content_type = response.headers.get("Content-Type", "")

                if "application/json" in content_type:
                    data = await response.json()
                    return self._parse_json_results(data, max_results)
                else:
                    # Jina returns markdown by default
                    text = await response.text()
                    return self._parse_markdown_results(text, query, max_results)

        except aiohttp.ClientError as e:
            logger.error(f"Jina network error: {e}")
            raise SearchError(f"Network error: {e}", self.name, query)
        except asyncio.TimeoutError:
            logger.error(f"Jina request timed out for '{query[:30]}...'")
            raise SearchError("Request timed out", self.name, query)

    def _parse_json_results(self, data: dict, max_results: int) -> List[SearchResult]:
        """Parse JSON response from Jina."""
        results = []

        # Handle different response formats
        items = data.get("data", data.get("results", []))
        if isinstance(items, dict):
            items = [items]

        for item in items[:max_results]:
            result = SearchResult(
                title=item.get("title", "No Title"),
                url=item.get("url", item.get("link", "")),
                snippet=item.get("description", item.get("content", ""))[:500],
                source=self.name,
                raw_data=item
            )
            results.append(result)

        logger.info(f"Jina found {len(results)} results")
        return results

    def _parse_markdown_results(
        self, text: str, query: str, max_results: int
    ) -> List[SearchResult]:
        """
        Parse markdown response from Jina.
        Jina returns search results as formatted markdown.
        """
        results = []

        # Split by result sections (usually separated by ---)
        sections = text.split("---")

        for section in sections[:max_results]:
            if not section.strip():
                continue

            lines = section.strip().split("\n")
            title = ""
            url = ""
            snippet_lines = []

            for line in lines:
                line = line.strip()
                if line.startswith("# ") or line.startswith("## "):
                    title = line.lstrip("#").strip()
                elif line.startswith("http://") or line.startswith("https://"):
                    url = line
                elif line.startswith("[") and "](" in line:
                    # Markdown link format: [title](url)
                    try:
                        title = line.split("[")[1].split("]")[0]
                        url = line.split("](")[1].split(")")[0]
                    except (IndexError, ValueError):
                        pass
                elif line and not line.startswith("Source:"):
                    snippet_lines.append(line)

            if url:
                results.append(SearchResult(
                    title=title or "Search Result",
                    url=url,
                    snippet=" ".join(snippet_lines)[:500],
                    source=self.name,
                ))

        logger.info(f"Jina parsed {len(results)} results from markdown")
        return results

    async def read_url(self, url: str) -> str:
        """
        Use Jina Reader to extract content from a URL.

        This is a bonus feature - extracts clean text from any webpage.

        Args:
            url: The URL to read

        Returns:
            Extracted text content (markdown formatted)
        """
        try:
            reader_url = f"{self.READER_URL}{url}"

            # Use unified HTTP client with rate limiting
            client = get_http_client()
            response = await client.get(
                reader_url,
                rate_limit_key="jina",
                headers=self._get_headers(),
            )

            async with response:
                if response.status == 429:
                    raise RateLimitError(self.name)

                if response.status != 200:
                    text = await response.text()
                    raise SearchError(f"HTTP {response.status}: {text[:200]}", self.name)

                content = await response.text()
                logger.info(f"Jina extracted {len(content)} chars from {url[:50]}...")
                return content

        except aiohttp.ClientError as e:
            logger.error(f"Jina Reader error: {e}")
            raise SearchError(f"Failed to read URL: {e}", self.name)

    def is_available(self) -> bool:
        """
        Jina is always available (free tier, no API key required).
        """
        return True
