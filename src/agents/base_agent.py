from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..core.types import CompanyProfile, ResearchPhaseResult, ResearchSource
from ..tools.search import SearchTool
from ..tools.browser import BrowserTool
from ..core.ai_client import get_ai_manager
from ..core.template_renderer import get_template_renderer
from ..core.logger import setup_logger

logger = setup_logger("base_agent")


class BaseAgent(ABC):
    """
    Abstract base class for all research agents.
    """

    def __init__(self):
        self.search_tool = SearchTool()
        self.browser_tool = BrowserTool()
        self.ai = get_ai_manager()
        self.renderer = get_template_renderer()
        self.agent_name = self.__class__.__name__

    @abstractmethod
    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Execute the research logic for this agent.
        """
        pass

    async def _gather_data(self, queries: List[str]) -> List[ResearchSource]:
        """
        Common helper to search and fetch data.
        """
        all_sources = []
        for query in queries:
            logger.info(f"[{self.agent_name}] Searching: {query}")
            # First get search results
            search_results = await self.search_tool.search(query, max_results=3)

            # Extract URLs
            urls = [r["url"] for r in search_results if "url" in r]

            # Fetch content
            if urls:
                sources = await self.browser_tool.fetch_multiple(urls)
                all_sources.extend(sources)

        return all_sources

    def _render(
        self, template_name: str, data: Dict[str, Any], sources: List[ResearchSource]
    ) -> str:
        """
        Render the report using a Jinja2 template.
        """
        # Add common context
        data["agent_name"] = self.agent_name
        data["sources"] = [
            {"title": s.title, "url": s.url, "source_type": s.source_type}
            for s in sources
        ]

        return self.renderer.render(template_name, **data)

    def _format_markdown(
        self, title: str, content: str, sources: List[ResearchSource]
    ) -> str:
        """
        Helper to format the final markdown report.
        DEPRECATED: Use _render instead.
        """
        md = f"# {title}\n\n"
        md += f"**Agent:** {self.agent_name}\n"
        md += "---\n\n"
        md += content + "\n\n"

        md += "## Sources\n"
        for s in sources:
            md += f"- [{s.title}]({s.url})\n"

        return md
