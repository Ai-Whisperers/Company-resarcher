import asyncio
import os
from typing import List, Dict, Any
from tavily import TavilyClient
from ..core.config import get_settings
from ..core.logger import setup_logger
from ..core.types import ResearchSource
from ..core.models import SearchResults
from ..core.result import Result, Ok, Err, SearchError

logger = setup_logger("search_tool")
settings = get_settings()

# Configurable search timeout (default 30 seconds)
SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "30"))


class SearchTool:
    """
    Wrapper for the Tavily Search API.
    """

    def __init__(self):
        # Extract secret value from SecretStr for API client
        api_key = settings.TAVILY_API_KEY.get_secret_value() if settings.TAVILY_API_KEY else None
        self.client = TavilyClient(api_key=api_key)

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
        Execute a search query (legacy Dict[str, Any] version).

        For new code, prefer search_typed() which provides type safety.
        """
        # Handle None and empty string safely
        if not query or not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid search query provided")
            return []

        if max_results < 1 or max_results > 20:
            logger.warning(f"Invalid max_results: {max_results}. Clamping to 1-20.")
            max_results = max(1, min(20, max_results))

        try:
            # Run in thread because Tavily client is synchronous
            # Add timeout to prevent indefinite hangs
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.search,
                    query=query,
                    search_depth="advanced",
                    max_results=max_results,
                    include_raw_content=False,
                ),
                timeout=SEARCH_TIMEOUT_SECONDS
            )

            results = response.get("results", [])
            logger.info(f"Found {len(results)} results for '{query}'")
            return results

        except asyncio.TimeoutError:
            logger.error(f"Search timed out after {SEARCH_TIMEOUT_SECONDS}s for '{query}'")
            return []
        except Exception as e:
            logger.error(f"Search failed for '{query}': {str(e)}")
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
                content=result.get("content", ""),
                source_type="web",
            )
            sources.append(source)

        return sources

    async def search_safe(
        self, query: str, max_results: int = 5
    ) -> Result[List[Dict[str, Any]], SearchError]:
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
            return Err(SearchError.invalid_query(query or "", "Empty or invalid query"))

        if max_results < 1 or max_results > 20:
            logger.warning(f"Invalid max_results: {max_results}. Clamping to 1-20.")
            max_results = max(1, min(20, max_results))

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.search,
                    query=query,
                    search_depth="advanced",
                    max_results=max_results,
                    include_raw_content=False,
                ),
                timeout=SEARCH_TIMEOUT_SECONDS
            )

            results = response.get("results", [])
            logger.info(f"Found {len(results)} results for '{query}'")

            if not results:
                return Err(SearchError.no_results(query))

            return Ok(results)

        except asyncio.TimeoutError:
            logger.error(f"Search timed out after {SEARCH_TIMEOUT_SECONDS}s for '{query}'")
            return Err(SearchError.timeout(query))
        except Exception as e:
            logger.error(f"Search failed for '{query}': {str(e)}")
            return Err(SearchError.api_error(query, str(e)))

    async def search_typed_safe(
        self, query: str, max_results: int = 5
    ) -> Result[SearchResults, SearchError]:
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
