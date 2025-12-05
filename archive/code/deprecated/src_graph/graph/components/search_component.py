from langflow.custom import CustomComponent
from langflow.field_typing import Data
from typing import Optional, List
from src.tools.search.tool import SearchTool


class SearchComponent(CustomComponent):
    display_name = "Company Researcher Search"
    description = "Advanced web search with fallback and adaptive timeout."
    icon = "search"

    def build_config(self):
        return {
            "query": {
                "display_name": "Search Query",
                "info": "The search query to execute.",
            },
            "max_results": {
                "display_name": "Max Results",
                "info": "Maximum number of results to return.",
                "value": 5,
            },
            "safe_mode": {
                "display_name": "Safe Mode",
                "info": "Remove advanced search operators.",
                "value": True,
            },
            "preferred_provider": {
                "display_name": "Preferred Provider",
                "options": ["duckduckgo", "jina", "serper", "tavily"],
                "value": "duckduckgo",
            },
        }

    def build(
        self,
        query: str,
        max_results: int = 5,
        safe_mode: bool = True,
        preferred_provider: Optional[str] = "duckduckgo",
    ) -> Data:
        # Initialize our internal tool
        tool = SearchTool(
            preferred_provider=preferred_provider,
            safe_mode=safe_mode,
            enable_fallback=True,
            enable_adaptive_timeout=True,
        )

        # Run synchronous search (LangFlow build method is sync)
        # We use the internal helper to run async code
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        results = loop.run_until_complete(tool.search(query, max_results=max_results))

        # Convert to LangFlow Data format
        data_results = []
        for res in results:
            data_results.append(Data(data=res))

        return data_results
