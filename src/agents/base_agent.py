from abc import ABC, abstractmethod
from typing import List, Dict, Any
import asyncio
from ..core.types import CompanyProfile, ResearchPhaseResult, ResearchSource
from ..tools import get_shared_search_tool, get_shared_browser_tool
from ..core.ai_client import get_ai_manager
from ..core.template_renderer import get_template_renderer
from ..core.logger import setup_logger

logger = setup_logger("base_agent")


class BaseAgent(ABC):
    """
    Abstract base class for all research agents.
    """

    def __init__(
        self,
        client=None,
        name: str = None,
        prompt_template: str = None,
        search_tool=None,
        browser_tool=None,
    ):
        # Use shared tools by default for resource efficiency
        self.search_tool = search_tool or get_shared_search_tool()
        self.browser_tool = browser_tool or get_shared_browser_tool()
        # Allow injection, fallback to singleton for backward compatibility
        self.ai = client if client else get_ai_manager()
        self.renderer = get_template_renderer()
        self.agent_name = name if name else self.__class__.__name__
        self.prompt_template = prompt_template

    @abstractmethod
    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Execute the research logic for this agent.
        """
        pass

    async def _gather_data(self, queries: List[str]) -> List[ResearchSource]:
        """
        Gather data for multiple queries IN PARALLEL.
        This is 5-10x faster than sequential processing.
        """

        async def fetch_query(query: str) -> List[ResearchSource]:
            """Fetch data for a single query."""
            logger.info(f"[{self.agent_name}] Searching: {query}")
            try:
                # Get search results
                search_results = await self.search_tool.search(query, max_results=3)

                # Extract URLs
                urls = [r["url"] for r in search_results if "url" in r]

                # Fetch content
                if urls:
                    return await self.browser_tool.fetch_multiple(urls)
                return []
            except Exception as e:
                logger.error(f"Error fetching query '{query}': {e}")
                return []

        # Execute all queries in parallel
        logger.info(f"[{self.agent_name}] Fetching {len(queries)} queries in parallel")
        results = await asyncio.gather(*[fetch_query(q) for q in queries])

        # Flatten results
        all_sources = [source for sublist in results for source in sublist]
        logger.info(f"[{self.agent_name}] Gathered {len(all_sources)} sources total")

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

    async def execute_research_cycle(
        self,
        company: CompanyProfile,
        queries: List[str],
        prompt_file: str,
        output_template: str,
        extra_context: Dict[str, Any] = None,
    ) -> ResearchPhaseResult:
        """
        Executes the standard research cycle:
        1. Gather data from queries
        2. Load prompt from file
        3. Generate JSON response
        4. Render Markdown report
        """
        # 1. Gather Data
        sources = await self._gather_data(queries)
        context = "\n\n".join(
            [f"Source: {s.title}\nContent: {s.content[:2000]}" for s in sources]
        )

        # 2. Load Prompt
        from pathlib import Path
        import jinja2

        prompt_path = Path(__file__).parent.parent / "prompts" / prompt_file
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_str = f.read()

        # Render Prompt with Jinja2
        template = jinja2.Template(prompt_template_str)
        prompt_context = {
            "company": company,
            "context": context,
            **(extra_context or {}),
        }
        prompt = template.render(**prompt_context)

        # 3. Generate & Parse
        import json
        from ..services.json_parser_helper import robust_json_parse
        from ..core.exceptions import AIError, AIResponseError

        content_json_str = ""
        try:
            content_json_str = await self.ai.generate(prompt, response_format="json")
            data = robust_json_parse(content_json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"JSON parsing failed for {self.agent_name}: {e}", exc_info=True
            )
            data = {"error": str(e), "raw_output": content_json_str}
        except AIError as e:
            logger.error(f"AI provider error in {self.agent_name}: {e}", exc_info=True)
            raise  # Re-raise AI errors so caller can handle
        except KeyboardInterrupt:
            raise  # Always allow keyboard interrupt
        except Exception as e:
            logger.error(f"Unexpected error in {self.agent_name}: {e}", exc_info=True)
            data = {"error": str(e), "raw_output": content_json_str}

        # 4. Render Report
        try:
            markdown_content = self._render(output_template, data, sources)
        except KeyboardInterrupt:
            raise  # Always allow keyboard interrupt
        except Exception as e:
            logger.error(
                f"Template rendering failed for {self.agent_name}: {e}", exc_info=True
            )
            markdown_content = (
                f"# Error Generating Report\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )

        return ResearchPhaseResult(
            phase_name=self.agent_name.replace("Agent", "").replace("Analyst", ""),
            markdown_content=markdown_content,
            sources=sources,
        )

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
