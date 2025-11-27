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
    """

    def __init__(self):
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute a search query.
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        if max_results < 1 or max_results > 20:
            logger.warning(f"Invalid max_results: {max_results}. Clamping to 1-20.")
            max_results = max(1, min(20, max_results))

        try:
            # Run in executor because Tavily client is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=max_results,
                    include_raw_content=False,
                ),
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
            )
            sources.append(source)

        return sources
