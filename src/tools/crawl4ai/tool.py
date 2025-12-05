from typing import Dict, Any, Optional, List
from src.tools.framework.base import BaseTool, ToolConfig
from src.tools.framework.errors import ToolError


class Crawl4AIConfig(ToolConfig):
    """Configuration for Crawl4AI tool"""

    max_pages: int = 10
    depth: int = 1
    javascript: bool = True
    timeout: int = 30


class Crawl4AITool(BaseTool[Dict[str, Any], Dict[str, Any]]):
    """
    Tool for advanced web crawling using Crawl4AI.
    Supports deep crawling, JavaScript rendering, and structured extraction.
    """

    def __init__(self, config: Optional[Crawl4AIConfig] = None):
        super().__init__(config or Crawl4AIConfig())
        self._crawler = None  # Initialize lazily

    async def _initialize_crawler(self):
        """Lazy initialization of the crawler instance"""
        if not self._crawler:
            try:
                # Import here to avoid hard dependency if not installed
                from crawl4ai import AsyncWebCrawler

                self._crawler = AsyncWebCrawler()
                await self._crawler.start()
            except ImportError:
                raise ToolError(
                    "crawl4ai package not installed. Please install with: pip install crawl4ai"
                )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the crawl operation.

        Args:
            input_data: {
                "url": str,
                "max_pages": int (optional),
                "depth": int (optional)
            }
        """
        await self._initialize_crawler()

        url = input_data.get("url")
        if not url:
            raise ToolError("URL is required")

        try:
            # TODO: Implement actual crawling logic with BFS/DFS strategies
            # This is a placeholder for the initial structure
            result = await self._crawler.arun(url=url)

            return {
                "url": url,
                "content": result.markdown,
                "metadata": result.metadata,
                "links": result.links,
            }
        except Exception as e:
            raise ToolError(f"Crawling failed: {str(e)}")

    async def cleanup(self):
        """Cleanup crawler resources"""
        if self._crawler:
            await self._crawler.close()
            self._crawler = None
