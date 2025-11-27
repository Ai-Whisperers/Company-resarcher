import asyncio
import os
from typing import List, Dict, Any
from tavily import TavilyClient
from ..core.config import get_settings
from ..core.logger import setup_logger
from ..core.types import ResearchSource

logger = setup_logger("search_tool")
settings = get_settings()

# Configurable search timeout (default 30 seconds)
SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "30"))


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
