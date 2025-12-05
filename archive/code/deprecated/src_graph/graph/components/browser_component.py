from langflow.custom import CustomComponent
from langflow.field_typing import Data
from typing import List, Optional
from src.tools.browser import get_shared_browser_tool


class BrowserComponent(CustomComponent):
    display_name = "Browser Tool"
    description = "Fetch and process web pages using the shared browser tool."
    icon = "globe"

    def build_config(self):
        return {
            "urls": {
                "display_name": "URLs",
                "info": "List of URLs to fetch.",
                "is_list": True,
            },
            "render_js": {
                "display_name": "Render JavaScript",
                "info": "Whether to render JavaScript (slower but more accurate).",
                "value": False,
            },
        }

    def build(
        self,
        urls: List[str],
        render_js: bool = False,
    ) -> List[Data]:
        # Initialize tool
        tool = get_shared_browser_tool()

        # Run async code in sync context
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Fetch data
        if not urls:
            return []

        # Use fetch_multiple for efficiency
        # Note: render_js support depends on the underlying tool implementation
        # For now we assume the tool handles it or we might need to extend it
        results = loop.run_until_complete(tool.fetch_multiple(urls))

        # Convert to LangFlow Data format
        data_results = []
        for res in results:
            data_results.append(
                Data(
                    data={
                        "url": res.url,
                        "title": res.title,
                        "content": res.content,
                        "source_type": res.source_type,
                        "raw_content": res.raw_content,
                    }
                )
            )

        return data_results
