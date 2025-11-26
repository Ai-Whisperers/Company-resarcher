import asyncio
from typing import List, Dict, Any
from tavily import TavilyClient
from ..core.config import get_settings
from ..core.logger import setup_logger
from ..core.types import ResearchSource

logger = setup_logger("search_tool")
settings = get_settings()


class SearchTool:
    """
    Wrapper for the Tavily Search API.
    Provides optimized search results for LLM agents.
    """

    def __init__(self):
        if not settings.TAVILY_API_KEY:
            logger.warning(
                "TAVILY_API_KEY not found in settings. Search functionality will be limited."
            )
            self.client = None
        else:
            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    async def search(
        self, query: str, max_results: int = 5, search_depth: str = "advanced"
    ) -> List[Dict[str, Any]]:
        """
        Execute a search query.

        Args:
            query: The search query string
            max_results: Number of results to return
            search_depth: "basic" or "advanced"

        Returns:
            List of search result dictionaries
        """
        if not self.client:
            logger.error("Search attempted without valid API key")
            return []

        try:
            logger.info(f"Searching for: '{query}'")

            # Tavily client is synchronous, so we wrap it in a thread for async usage
            response = await asyncio.to_thread(
                self.client.search,
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False,
            )

            results = response.get("results", [])
            logger.info(f"Found {len(results)} results for '{query}'")
            return results

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
                reliability_score=result.get("score", 0.0),
            )
            sources.append(source)

        return sources
