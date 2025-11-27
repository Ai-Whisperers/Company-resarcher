"""
Local Search Tool - Uses DuckDuckGo for free web searching.
"""

from typing import List, Dict, Any
from duckduckgo_search import DDGS
from ..core.logger import setup_logger

logger = setup_logger("local_search")


class LocalSearchTool:
    """
    Executes searches using DuckDuckGo (free, no API key required).
    Acts as a drop-in replacement for SearchTool.
    """

    def __init__(self):
        self.ddgs = DDGS()

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute a search query using DuckDuckGo.

        Args:
            query: The search query string
            max_results: Maximum number of results to return

        Returns:
            List of dictionaries containing 'url', 'content', and 'title'
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to LocalSearchTool")
            return []

        # Cap max_results to avoid excessive requests
        max_results = min(max(1, max_results), 20)

        logger.info(f"Searching DuckDuckGo for: {query} (max={max_results})")

        try:
            # DDGS.text() is synchronous, but we can run it directly since it's fast enough
            # or wrap it in run_in_executor if needed. For now, direct call.
            results = self.ddgs.text(query, max_results=max_results)

            # Normalize to match SearchTool output format
            normalized_results = []
            for r in results:
                normalized_results.append(
                    {
                        "url": r.get("href", ""),
                        "title": r.get("title", ""),
                        "content": r.get("body", ""),
                        "score": 1.0,  # DDG doesn't provide score, default to 1.0
                    }
                )

            logger.info(f"Found {len(normalized_results)} results")
            return normalized_results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
