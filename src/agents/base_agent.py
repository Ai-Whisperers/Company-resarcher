from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path
import asyncio
import json
import os

import jinja2
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..core.types import CompanyProfile, ResearchPhaseResult, ResearchSource
from ..tools import get_shared_search_tool, get_shared_browser_tool
from ..core.ai_client import get_ai_manager, AIClientManager
from ..core.template_renderer import get_template_renderer, TemplateRenderer
from ..core.logger import setup_logger
from ..core.exceptions import AIError, AIRateLimitError, AITimeoutError
from ..services.json_parser_helper import robust_json_parse

if TYPE_CHECKING:
    from ..core.container import Container
    from ..tools.search import SearchTool
    from ..tools.browser import BrowserTool

logger = setup_logger("base_agent")

# Maximum concurrent queries per agent (configurable via environment)
MAX_CONCURRENT_QUERIES = int(os.getenv("AGENT_MAX_CONCURRENT_QUERIES", "5"))

# LLM call configuration (configurable via environment)
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))


class BaseAgent(ABC):
    """
    Abstract base class for all research agents.

    Supports two initialization patterns:
    1. Direct injection (legacy): Pass dependencies directly to __init__
    2. Container injection (recommended): Use from_container() class method

    Example (legacy):
        agent = MyAgent(client=ai_manager, search_tool=search)

    Example (container):
        from src.core.container import get_container
        agent = MyAgent.from_container(get_container())
    """

    def __init__(
        self,
        client: Optional["AIClientManager"] = None,
        name: Optional[str] = None,
        prompt_template: Optional[str] = None,
        search_tool: Optional["SearchTool"] = None,
        browser_tool: Optional["BrowserTool"] = None,
        renderer: Optional["TemplateRenderer"] = None,
    ):
        # Use shared tools by default for resource efficiency
        self.search_tool = search_tool or get_shared_search_tool()
        self.browser_tool = browser_tool or get_shared_browser_tool()
        # Allow injection, fallback to singleton for backward compatibility
        self.ai = client if client else get_ai_manager()
        self.renderer = renderer if renderer else get_template_renderer()
        self.agent_name = name if name else self.__class__.__name__
        self.prompt_template = prompt_template

    @classmethod
    def from_container(cls, container: "Container", **kwargs) -> "BaseAgent":
        """
        Create an agent instance using dependencies from a DI container.

        This is the recommended way to create agents for better testability.

        Args:
            container: The DI container to resolve dependencies from
            **kwargs: Additional arguments passed to __init__ (e.g., name, prompt_template)

        Returns:
            A new agent instance with dependencies resolved from the container

        Example:
            from src.core.container import get_container
            agent = MarketAnalyst.from_container(get_container())

            # For testing with mocks:
            container.override(AIClientManager, mock_ai)
            agent = MarketAnalyst.from_container(container)
        """
        # Import here to avoid circular imports
        from ..core.container import Container
        from ..tools.search import SearchTool
        from ..tools.browser import BrowserTool

        return cls(
            client=container.resolve(AIClientManager),
            search_tool=container.resolve(SearchTool),
            browser_tool=container.resolve(BrowserTool),
            renderer=container.resolve(TemplateRenderer),
            **kwargs,
        )

    @abstractmethod
    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Execute the research logic for this agent.
        """
        pass

    async def _safe_generate(
        self,
        prompt: str,
        response_format: str = "json",
        timeout: float = None,
    ) -> str:
        """
        Safely invoke the AI with retry logic and timeout handling.

        Args:
            prompt: The prompt to send to the AI
            response_format: Expected response format ("json" or "text")
            timeout: Timeout in seconds (defaults to LLM_TIMEOUT_SECONDS)

        Returns:
            The AI response content

        Raises:
            AITimeoutError: If the request times out after all retries
            AIError: If the AI request fails after all retries
        """
        timeout = timeout or LLM_TIMEOUT_SECONDS

        @retry(
            stop=stop_after_attempt(LLM_MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type((AIRateLimitError, asyncio.TimeoutError)),
            before_sleep=before_sleep_log(logger, log_level=20),  # INFO level
            reraise=True,
        )
        async def _invoke_with_retry():
            try:
                return await asyncio.wait_for(
                    self.ai.generate(prompt, response_format=response_format),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"[{self.agent_name}] LLM call timed out after {timeout}s, retrying..."
                )
                raise
            except AIRateLimitError as e:
                logger.warning(
                    f"[{self.agent_name}] Rate limited: {e}, retrying with backoff..."
                )
                raise

        try:
            return await _invoke_with_retry()
        except asyncio.TimeoutError:
            raise AITimeoutError(
                provider=self.ai.get_provider_name() if hasattr(self.ai, 'get_provider_name') else "unknown",
                timeout_seconds=int(timeout),
            )
        except Exception as e:
            logger.error(f"[{self.agent_name}] AI generation failed after retries: {e}")
            raise

    async def _gather_data(self, queries: List[str]) -> List[ResearchSource]:
        """
        Gather data for multiple queries IN PARALLEL with bounded concurrency.
        Uses semaphore to prevent spawning too many concurrent requests.
        """
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_QUERIES)

        async def fetch_query(query: str) -> List[ResearchSource]:
            """Fetch data for a single query with rate limiting."""
            async with semaphore:
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

        # Execute all queries in parallel (bounded by semaphore)
        logger.info(f"[{self.agent_name}] Fetching {len(queries)} queries (max {MAX_CONCURRENT_QUERIES} concurrent)")
        results = await asyncio.gather(*[fetch_query(q) for q in queries], return_exceptions=True)

        # Process results with error tracking
        all_sources = []
        failed_count = 0
        for query, result in zip(queries, results):
            if isinstance(result, Exception):
                logger.error(f"[{self.agent_name}] Query '{query}' raised exception: {result}")
                failed_count += 1
            elif result:
                all_sources.extend(result)

        # Log summary
        success_count = len(queries) - failed_count
        logger.info(f"[{self.agent_name}] Gathered {len(all_sources)} sources from {success_count}/{len(queries)} successful queries")
        if failed_count > 0:
            logger.warning(f"[{self.agent_name}] {failed_count} queries failed")

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

        # 3. Generate & Parse (with retry and timeout handling)
        content_json_str = ""
        try:
            content_json_str = await self._safe_generate(prompt, response_format="json")
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
