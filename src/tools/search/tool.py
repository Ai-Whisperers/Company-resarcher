"""
SearchTool - Main search interface for the Company Researcher.

This module provides backward-compatible search functionality while
internally using the new SearchManager with multiple providers and fallback.

Provider Priority (free first):
1. DuckDuckGo (FREE) - No API key needed
2. Jina AI (FREE) - 10M tokens free
3. Serper.dev (Paid) - If SERPER_API_KEY configured
4. Tavily (Paid) - If TAVILY_API_KEY configured
"""

import asyncio
import os
import re
from typing import List, Dict, Any, Optional
from src.core.config import get_settings
from src.core.logging import setup_logger
from src.core.types.base import ResearchSource
from src.core.models.base import SearchResults
from src.core.result import Result, Ok, Err
from src.core.result import SearchError as ResultSearchError

# Import new search manager
from .manager import SearchManager, get_search_manager
from .base import SearchError as ProviderSearchError, RateLimitError

logger = setup_logger("search_tool")
settings = get_settings()

# Configurable search timeout (default 45 seconds - increased from 30 for better success rate)
SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "45"))

# Maximum query length to prevent abuse
MAX_QUERY_LENGTH = 500


def sanitize_search_query(query: str, safe_mode: bool = True) -> str:
    """
    Sanitize search query to prevent injection and abuse.

    - Limits length to prevent DoS
    - Removes search operator keywords that could be abused (if safe_mode=True)
    - Normalizes whitespace
    - Removes control characters

    Args:
        query: Raw search query string
        safe_mode: If True (default), removes advanced search operators.
                   If False, allows operators like site:, filetype:, etc.
                   Only trusted agents (e.g., DeepResearchAgent) should use safe_mode=False.

    Returns:
        Sanitized query string
    """
    # Limit length
    query = query[:MAX_QUERY_LENGTH]

    # Remove control characters
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)

    # Remove common search operators that could be abused (unless safe_mode is disabled)
    # These can leak internal data or manipulate results
    if safe_mode:
        operators = ['site:', 'inurl:', 'filetype:', 'intitle:', 'intext:', 'cache:', 'related:']
        for op in operators:
            query = re.sub(re.escape(op), '', query, flags=re.IGNORECASE)

    # Normalize whitespace
    query = ' '.join(query.split())

    return query


class SearchTool:
    """
    Unified search tool with automatic provider fallback.

    Uses multiple search providers in priority order:
    1. DuckDuckGo (FREE)
    2. Jina AI (FREE)
    3. Serper.dev (if configured)
    4. Tavily (if configured)

    Automatically falls back to next provider if one fails.
    """

    def __init__(
        self,
        preferred_provider: Optional[str] = None,
        safe_mode: bool = True,
    ):
        """
        Initialize SearchTool.

        Args:
            preferred_provider: Force a specific provider (optional).
                               Options: "duckduckgo", "jina", "serper", "tavily"
            safe_mode: If True (default), removes advanced search operators
                       (site:, filetype:, etc.) from queries. Set to False
                       for trusted agents like DeepResearchAgent that need
                       these operators for targeted research.
        """
        self.preferred_provider = preferred_provider
        self.safe_mode = safe_mode
        self._manager: Optional[SearchManager] = None

    @property
    def manager(self) -> SearchManager:
        """Lazy-load SearchManager."""
        if self._manager is None:
            self._manager = get_search_manager()
        return self._manager

    async def search_typed(self, query: str, max_results: int = 5) -> SearchResults:
        """
        Execute a search query and return typed results (recommended).

        Args:
            query: Search query string
            max_results: Maximum number of results (1-20)

        Returns:
            SearchResults with typed SearchResult items
        """
        raw_results = await self.search(query, max_results)
        return SearchResults.from_list(query, raw_results)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute a search query with automatic fallback.

        This method tries providers in priority order (free first).
        If all providers fail, returns empty list.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of search result dictionaries
        """
        # Handle None and empty string safely
        if not query or not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid search query provided")
            return []

        # Sanitize query to prevent injection
        query = sanitize_search_query(query, safe_mode=self.safe_mode)
        if not query:
            logger.warning("Query empty after sanitization")
            return []

        if max_results < 1 or max_results > 20:
            logger.warning(f"Invalid max_results: {max_results}. Clamping to 1-20.")
            max_results = max(1, min(20, max_results))

        try:
            # Use SearchManager with automatic fallback
            results = await asyncio.wait_for(
                self.manager.search(
                    query,
                    max_results=max_results,
                    preferred_provider=self.preferred_provider,
                ),
                timeout=SEARCH_TIMEOUT_SECONDS
            )

            # Convert SearchResult objects to dictionaries for backward compatibility
            dict_results = []
            for r in results:
                dict_results.append({
                    "url": r.url,
                    "title": r.title,
                    "content": r.snippet,  # Map snippet to content for compatibility
                    "snippet": r.snippet,
                    "source": r.source,
                    "published_date": r.published_date,
                    "score": r.score,
                })

            logger.info(f"Found {len(dict_results)} results for '{query}' (provider: {results[0].source if results else 'none'})")
            return dict_results

        except asyncio.TimeoutError:
            logger.error(f"Search timed out after {SEARCH_TIMEOUT_SECONDS}s for '{query}'")
            return []
        except ProviderSearchError as e:
            logger.error(f"Search failed for '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected search error for '{query}': {e}")
            return []

    async def search_and_parse(
        self, query: str, max_results: int = 5
    ) -> List[ResearchSource]:
        """
        Search and convert results directly to ResearchSource objects.
        """
        raw_results = await self.search(query, max_results)
        sources = []

        for result in raw_results:
            source = ResearchSource(
                url=result.get("url", ""),
                title=result.get("title", "No Title"),
                content=result.get("content", result.get("snippet", "")),
                source_type="web",
            )
            sources.append(source)

        return sources

    async def search_safe(
        self, query: str, max_results: int = 5
    ) -> Result[List[Dict[str, Any]], ResultSearchError]:
        """
        Execute a search query with explicit error handling via Result type.

        Returns Ok(results) on success, Err(SearchError) on failure.
        This is the recommended method for new code.

        Example:
            result = await search_tool.search_safe("company news")
            if result.is_ok:
                for item in result.unwrap():
                    print(item["title"])
            else:
                print(f"Search failed: {result.unwrap_err()}")

            # Or with default:
            results = result.unwrap_or([])
        """
        # Handle None and empty string safely
        if not query or not isinstance(query, str) or not query.strip():
            return Err(ResultSearchError.invalid_query(query or "", "Empty or invalid query"))

        # Sanitize query to prevent injection
        query = sanitize_search_query(query, safe_mode=self.safe_mode)
        if not query:
            return Err(ResultSearchError.invalid_query(query, "Query empty after sanitization"))

        if max_results < 1 or max_results > 20:
            logger.warning(f"Invalid max_results: {max_results}. Clamping to 1-20.")
            max_results = max(1, min(20, max_results))

        try:
            results = await asyncio.wait_for(
                self.manager.search(
                    query,
                    max_results=max_results,
                    preferred_provider=self.preferred_provider,
                ),
                timeout=SEARCH_TIMEOUT_SECONDS
            )

            if not results:
                return Err(ResultSearchError.no_results(query))

            # Convert to dict format
            dict_results = [
                {
                    "url": r.url,
                    "title": r.title,
                    "content": r.snippet,
                    "snippet": r.snippet,
                    "source": r.source,
                }
                for r in results
            ]

            return Ok(dict_results)

        except asyncio.TimeoutError:
            logger.error(f"Search timed out after {SEARCH_TIMEOUT_SECONDS}s for '{query}'")
            return Err(ResultSearchError.timeout(query))
        except RateLimitError as e:
            logger.error(f"All providers rate limited for '{query}'")
            return Err(ResultSearchError.api_error(query, str(e)))
        except ProviderSearchError as e:
            logger.error(f"Search failed for '{query}': {e}")
            return Err(ResultSearchError.api_error(query, str(e)))
        except Exception as e:
            logger.error(f"Search failed for '{query}': {str(e)}")
            return Err(ResultSearchError.api_error(query, str(e)))

    async def search_typed_safe(
        self, query: str, max_results: int = 5
    ) -> Result[SearchResults, ResultSearchError]:
        """
        Execute a search query and return typed SearchResults with Result error handling.

        Combines type safety with explicit error handling.

        Example:
            result = await search_tool.search_typed_safe("company news")
            match = result.map(lambda sr: sr.results[0].title if sr.results else "No results")
            print(match.unwrap_or("Search failed"))
        """
        raw_result = await self.search_safe(query, max_results)

        # Use map to transform Ok values while preserving Err
        return raw_result.map(lambda results: SearchResults.from_list(query, results))

    async def search_paginated(
        self,
        query: str,
        results_per_page: int = 10,
        max_pages: int = 3,
        page_delay_seconds: float = 1.0,
        deduplicate: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute a paginated search across multiple pages (TECH-003).

        This method fetches results across multiple "pages" to get deeper
        search results beyond the first page.

        Args:
            query: Search query string
            results_per_page: Results per page (default 10)
            max_pages: Maximum pages to fetch (default 3)
            page_delay_seconds: Delay between pages for rate limiting
            deduplicate: Remove duplicate URLs (default True)

        Returns:
            List of search result dictionaries from all pages
        """
        if not query or not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid search query provided")
            return []

        query = sanitize_search_query(query, safe_mode=self.safe_mode)
        if not query:
            logger.warning("Query empty after sanitization")
            return []

        try:
            results = await asyncio.wait_for(
                self.manager.search_paginated(
                    query,
                    results_per_page=results_per_page,
                    max_pages=max_pages,
                    page_delay_seconds=page_delay_seconds,
                    preferred_provider=self.preferred_provider,
                    deduplicate=deduplicate,
                ),
                timeout=SEARCH_TIMEOUT_SECONDS * max_pages  # Longer timeout for multiple pages
            )

            # Convert to dictionaries for backward compatibility
            dict_results = []
            for r in results:
                dict_results.append({
                    "url": r.url,
                    "title": r.title,
                    "content": r.snippet,
                    "snippet": r.snippet,
                    "source": r.source,
                    "published_date": r.published_date,
                    "score": r.score,
                })

            logger.info(f"Paginated search found {len(dict_results)} total results for '{query}'")
            return dict_results

        except asyncio.TimeoutError:
            logger.error(f"Paginated search timed out for '{query}'")
            return []
        except Exception as e:
            logger.error(f"Paginated search error for '{query}': {e}")
            return []

    def get_available_providers(self) -> List[str]:
        """Get list of available search providers."""
        return self.manager.get_available_providers()

    def get_provider_stats(self) -> Dict[str, Any]:
        """Get search provider statistics."""
        return self.manager.get_stats()

    def get_status(self) -> Dict[str, Any]:
        """Get status of all search providers."""
        return self.manager.get_status()
