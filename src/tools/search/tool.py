"""
SearchTool - Main search interface for the Company Researcher.

This module provides backward-compatible search functionality while
internally using the new SearchManager with multiple providers and fallback.

Features:
- Multiple provider fallback (DuckDuckGo → Jina → Serper → Tavily)
- Query fallback for empty results (simplify, translate, broaden)
- Automatic retry with alternative query formulations
- Rate limiting and circuit breaker protection

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
from src.domain.models.base import SearchResults
from src.core.result import Result, Ok, Err
from src.core.result import SearchError as ResultSearchError

# Import new search manager
from .manager import SearchManager, get_search_manager
from .base import SearchError as ProviderSearchError, RateLimitError

# Import fallback manager for query retry
from src.lib.resilience.search_fallback import get_fallback_queries

# Import adaptive timeout manager
from src.lib.resilience.adaptive_timeout import (
    get_adaptive_timeout_manager,
    get_adaptive_search_timeout,
    AdaptiveTimeoutManager,
)
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field

logger = setup_logger("search_tool")
settings = get_settings()

# Configurable search timeout (default 45 seconds - increased from 30 for better success rate)
SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "45"))

# Enable adaptive timeout (adjusts based on query success patterns)
ENABLE_ADAPTIVE_TIMEOUT = os.getenv("ENABLE_ADAPTIVE_TIMEOUT", "true").lower() == "true"

# Enable query fallback for empty results
ENABLE_QUERY_FALLBACK = os.getenv("ENABLE_QUERY_FALLBACK", "true").lower() == "true"
MAX_FALLBACK_QUERIES = int(os.getenv("MAX_FALLBACK_QUERIES", "2"))

# Maximum query length to prevent abuse
MAX_QUERY_LENGTH = 500

# Whitelisted search operators for unsafe mode (safe to use for research)
# These operators help with targeted research without exposing internal data
ALLOWED_OPERATORS = frozenset(
    {
        "site:",  # Restrict to specific domain
        "filetype:",  # Restrict to specific file type (pdf, doc, etc.)
        "-",  # Exclude terms
        '"',  # Exact phrase matching
    }
)

# Dangerous operators that should always be removed
# These can leak internal data or be abused for SSRF/injection
DANGEROUS_OPERATORS = frozenset(
    {
        "cache:",  # Access Google's cached version - can expose old content
        "related:",  # Find related sites - limited use, can be abused
        "inurl:",  # Match URL patterns - can be used for path enumeration
        "intext:",  # Search page content - too broad, potential for abuse
        "intitle:",  # Search titles - too broad, potential for abuse
        "link:",  # Find linking pages - deprecated, unreliable
        "info:",  # Get info about URL - can expose metadata
        "define:",  # Dictionary lookup - not useful for research
    }
)


def _validate_operator_values(query: str) -> str:
    """
    Validate operator values to prevent injection.

    Ensures operator values don't contain shell metacharacters or
    other potentially dangerous patterns.
    """
    # Pattern to find operator:value pairs
    operator_pattern = re.compile(r"(\w+:)([^\s]+)")

    def sanitize_value(match):
        operator = match.group(1)
        value = match.group(2)

        # Remove shell metacharacters from values
        # Allow only alphanumeric, dots, hyphens, underscores, and slashes for URLs
        safe_value = re.sub(r"[;&|`$(){}[\]<>\\]", "", value)

        return f"{operator}{safe_value}"

    return operator_pattern.sub(sanitize_value, query)


def sanitize_search_query(query: str, safe_mode: bool = True) -> str:
    """
    Sanitize search query to prevent injection and abuse.

    - Limits length to prevent DoS
    - Removes search operator keywords that could be abused
    - In safe_mode: removes ALL operators
    - In unsafe_mode: only allows whitelisted operators (site:, filetype:, -, ")
    - Normalizes whitespace
    - Removes control characters

    Args:
        query: Raw search query string
        safe_mode: If True (default), removes ALL advanced search operators.
                   If False, allows only whitelisted operators (site:, filetype:, -, ").
                   Only trusted agents (e.g., DeepResearchAgent) should use safe_mode=False.

    Returns:
        Sanitized query string
    """
    # Limit length
    query = query[:MAX_QUERY_LENGTH]

    # Remove control characters
    query = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", query)

    if safe_mode:
        # Remove ALL search operators in safe mode
        all_operators = list(ALLOWED_OPERATORS) + list(DANGEROUS_OPERATORS)
        for op in all_operators:
            if op in ('"', "-"):
                continue  # These are common characters, only remove as operators
            query = re.sub(re.escape(op), "", query, flags=re.IGNORECASE)
    else:
        # In unsafe mode, remove only dangerous operators but validate values
        for op in DANGEROUS_OPERATORS:
            query = re.sub(re.escape(op), "", query, flags=re.IGNORECASE)
        # Validate remaining operator values to prevent injection
        query = _validate_operator_values(query)

    # Normalize whitespace
    query = " ".join(query.split())

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
        company: str = "",
        country: str = "",
        enable_fallback: bool = ENABLE_QUERY_FALLBACK,
        enable_adaptive_timeout: bool = ENABLE_ADAPTIVE_TIMEOUT,
        section: str = "",
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
            company: Company name for context-aware fallback queries
            country: Country for context-aware fallback queries
            enable_fallback: Whether to use query fallback on empty results
            enable_adaptive_timeout: Whether to use adaptive timeout based on query patterns
            section: Research section for adaptive timeout tracking
        """
        self.preferred_provider = preferred_provider
        self.safe_mode = safe_mode
        self.company = company
        self.country = country
        self.enable_fallback = enable_fallback
        self.enable_adaptive_timeout = enable_adaptive_timeout
        self.section = section
        self._manager: Optional[SearchManager] = None
        self._timeout_manager: Optional[AdaptiveTimeoutManager] = None

    @property
    def timeout_manager(self) -> AdaptiveTimeoutManager:
        """Lazy-load adaptive timeout manager."""
        if self._timeout_manager is None:
            self._timeout_manager = get_adaptive_timeout_manager()
        return self._timeout_manager

    def _get_timeout(self, query: str) -> int:
        """Get timeout for a query (adaptive or fixed)."""
        if self.enable_adaptive_timeout:
            return self.timeout_manager.get_timeout(query, self.section)
        return SEARCH_TIMEOUT_SECONDS

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

        Features:
        - Adaptive timeout based on query pattern success rates
        - Query fallback for empty results
        - Automatic provider fallback

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of search result dictionaries
        """
        import time

        start_time = time.time()

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

        # Get adaptive timeout for this query
        timeout = self._get_timeout(query)

        try:
            # Use SearchManager with automatic fallback
            results = await asyncio.wait_for(
                self.manager.search(
                    query,
                    max_results=max_results,
                    preferred_provider=self.preferred_provider,
                ),
                timeout=timeout,
            )

            # If no results and fallback is enabled, try alternative queries
            if not results and self.enable_fallback:
                fallback_queries = get_fallback_queries(
                    query,
                    company=self.company,
                    country=self.country,
                    max_fallbacks=MAX_FALLBACK_QUERIES,
                )

                for fallback_query in fallback_queries:
                    logger.info(f"Trying fallback query: '{fallback_query}'")
                    try:
                        fallback_timeout = self._get_timeout(fallback_query)
                        results = await asyncio.wait_for(
                            self.manager.search(
                                fallback_query,
                                max_results=max_results,
                                preferred_provider=self.preferred_provider,
                            ),
                            timeout=fallback_timeout,
                        )
                        if results:
                            logger.info(f"Fallback query succeeded: '{fallback_query}'")
                            break
                    except Exception as fallback_err:
                        logger.debug(f"Fallback query failed: {fallback_err}")
                        continue

            # Convert SearchResult objects to dictionaries for backward compatibility
            dict_results = []
            for r in results:
                dict_results.append(
                    {
                        "url": r.url,
                        "title": r.title,
                        "content": r.snippet,  # Map snippet to content for compatibility
                        "snippet": r.snippet,
                        "source": r.source,
                        "published_date": r.published_date,
                        "score": r.score,
                    }
                )

            # Record success with adaptive timeout manager
            elapsed = time.time() - start_time
            if self.enable_adaptive_timeout:
                if dict_results:
                    self.timeout_manager.record_success(
                        query, self.section, elapsed, len(dict_results)
                    )
                else:
                    self.timeout_manager.record_failure(
                        query, self.section, is_empty=True
                    )

            logger.info(
                f"Found {len(dict_results)} results for '{query}' (provider: {results[0].source if results else 'none'}, timeout: {timeout}s)"
            )
            return dict_results

        except asyncio.TimeoutError:
            # Record timeout with adaptive timeout manager
            if self.enable_adaptive_timeout:
                self.timeout_manager.record_failure(
                    query, self.section, is_timeout=True
                )
            logger.error(f"Search timed out after {timeout}s for '{query}'")
            return []
        except ProviderSearchError as e:
            if self.enable_adaptive_timeout:
                self.timeout_manager.record_failure(query, self.section)
            logger.error(f"Search failed for '{query}': {e}")
            return []
        except Exception as e:
            if self.enable_adaptive_timeout:
                self.timeout_manager.record_failure(query, self.section)
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
            return Err(
                ResultSearchError.invalid_query(query or "", "Empty or invalid query")
            )

        # Sanitize query to prevent injection
        query = sanitize_search_query(query, safe_mode=self.safe_mode)
        if not query:
            return Err(
                ResultSearchError.invalid_query(query, "Query empty after sanitization")
            )

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
                timeout=SEARCH_TIMEOUT_SECONDS,
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
            logger.error(
                f"Search timed out after {SEARCH_TIMEOUT_SECONDS}s for '{query}'"
            )
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
                timeout=SEARCH_TIMEOUT_SECONDS
                * max_pages,  # Longer timeout for multiple pages
            )

            # Convert to dictionaries for backward compatibility
            dict_results = []
            for r in results:
                dict_results.append(
                    {
                        "url": r.url,
                        "title": r.title,
                        "content": r.snippet,
                        "snippet": r.snippet,
                        "source": r.source,
                        "published_date": r.published_date,
                        "score": r.score,
                    }
                )

            logger.info(
                f"Paginated search found {len(dict_results)} total results for '{query}'"
            )
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

    async def search_parallel(
        self,
        query: str,
        max_results: int = 10,
        providers: Optional[List[str]] = None,
        timeout_seconds: float = 30.0,
        min_providers_for_success: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Execute search across multiple engines in parallel and combine results.

        This method queries all available search engines simultaneously instead of
        sequentially, significantly reducing search time (especially when DuckDuckGo
        is slow with its 60s timeout).

        Args:
            query: The search query
            max_results: Maximum total results to return (deduplicated)
            providers: Optional list of provider names to use
            timeout_seconds: Timeout for the entire parallel search operation
            min_providers_for_success: Minimum providers that must succeed

        Returns:
            Combined, deduplicated list of search result dictionaries

        Features:
        - Runs DuckDuckGo, Jina, Serper, etc. in parallel
        - Combines results and deduplicates by URL
        - Returns as soon as min_providers_for_success respond
        """
        if not query or not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid search query provided")
            return []

        query = sanitize_search_query(query, safe_mode=self.safe_mode)
        if not query:
            return []

        try:
            results = await self.manager.search_parallel(
                query,
                max_results=max_results,
                providers=providers,
                timeout_seconds=timeout_seconds,
                min_providers_for_success=min_providers_for_success,
            )

            # Convert to dictionaries for backward compatibility
            dict_results = []
            for r in results:
                dict_results.append(
                    {
                        "url": r.url,
                        "title": r.title,
                        "content": r.snippet,
                        "snippet": r.snippet,
                        "source": r.source,
                        "published_date": r.published_date,
                        "score": r.score,
                    }
                )

            logger.info(
                f"Parallel search found {len(dict_results)} results for '{query}'"
            )
            return dict_results

        except Exception as e:
            logger.error(f"Parallel search error for '{query}': {e}")
            return []

    async def search_distributed(
        self,
        queries: List[str],
        max_results_per_query: int = 5,
        timeout_seconds: float = 60.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute MULTIPLE queries using a queue-based pull architecture.

        This method uses a central queue that provider workers pull from:
        - All queries go into a shared asyncio.Queue
        - Each provider has a worker that pulls queries when ready
        - Faster providers (Serper 3000 RPM) naturally handle more queries
        - Slower providers (DuckDuckGo 30 RPM) handle fewer but still contribute
        - Failed queries are requeued for retry by a different provider

        This is 2-3x faster than running queries sequentially because:
        1. Fast providers aren't waiting while slow ones process
        2. Rate limits are respected per-provider
        3. Load balancing is automatic based on actual throughput

        Args:
            queries: List of search queries to execute
            max_results_per_query: Results per query (default 5)
            timeout_seconds: Timeout for entire operation

        Returns:
            Dict mapping query -> list of result dictionaries
        """
        if not queries:
            return {}

        # Sanitize all queries
        sanitized_queries = []
        for q in queries:
            if q and isinstance(q, str) and q.strip():
                sanitized = sanitize_search_query(q, safe_mode=self.safe_mode)
                if sanitized:
                    sanitized_queries.append(sanitized)

        if not sanitized_queries:
            return {}

        try:
            results = await self.manager.search_distributed(
                sanitized_queries,
                max_results_per_query=max_results_per_query,
                timeout_seconds=timeout_seconds,
            )

            # Convert SearchResult objects to dictionaries
            dict_results = {}
            for query, search_results in results.items():
                dict_results[query] = [
                    {
                        "url": r.url,
                        "title": r.title,
                        "content": r.snippet,
                        "snippet": r.snippet,
                        "source": r.source,
                        "published_date": r.published_date,
                        "score": r.score,
                    }
                    for r in search_results
                ]

            logger.info(
                f"Distributed search complete: {len([r for r in dict_results.values() if r])}/{len(sanitized_queries)} queries successful"
            )
            return dict_results

        except Exception as e:
            logger.error(f"Distributed search error: {e}")
            return {}

    def to_langchain_tool(self) -> Tool:
        """
        Convert this tool to a LangChain-compatible Tool.

        Returns:
            Tool: A LangChain Tool instance that wraps this SearchTool.
        """

        class SearchInput(BaseModel):
            query: str = Field(description="The search query to execute.")

        async def _asearch(query: str) -> str:
            """Async search wrapper that returns a string representation of results."""
            results = await self.search(query)
            if not results:
                return "No results found."

            # Format results as a string
            output = []
            for i, res in enumerate(results, 1):
                output.append(
                    f"{i}. {res.get('title', 'No Title')}\n   URL: {res.get('url', 'No URL')}\n   Snippet: {res.get('snippet', 'No snippet')}\n"
                )

            return "\n".join(output)

        def _search(query: str) -> str:
            """Sync search wrapper (not recommended, but required by BaseTool)."""
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(_asearch(query))

        return Tool(
            name="web_search",
            description="Useful for searching the internet for current events, company data, and general information.",
            func=_search,
            coroutine=_asearch,
            args_schema=SearchInput,
        )
