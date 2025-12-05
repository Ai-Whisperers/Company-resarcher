"""
Legacy ResearchOrchestrator using LangGraph.

.. deprecated::
    This module is DEPRECATED. Use `src.pipeline.orchestrator.PipelineOrchestrator` instead.
"""

import threading
import warnings
from typing import Dict, Any, Optional, TYPE_CHECKING

from src.core.logging import setup_logger
from src.infrastructure.ai import BaseAIClient
from .factory import AgentFactory

# Lazy imports to avoid circular import
if TYPE_CHECKING:
    from src.graph.graph_builder import ResearchGraph
    from src.graph.state import ResearchState

logger = setup_logger(__name__)

# Emit deprecation warning
warnings.warn(
    "src.agents.orchestrator.ResearchOrchestrator is deprecated. "
    "Use src.pipeline.orchestrator.PipelineOrchestrator instead.",
    DeprecationWarning,
    stacklevel=2,
)


class ResearchOrchestrator:
    """
    Main orchestrator for the research process.
    Uses dependency injection for all agents.
    """

    def __init__(
        self, ai_client: Optional[BaseAIClient] = None, use_local_tools: bool = False
    ):
        """
        Initialize the orchestrator with dependency injection.

        .. deprecated::
            Use `src.pipeline.orchestrator.PipelineOrchestrator` instead.

        Args:
            ai_client: Optional AI client. If None, uses global manager.
            use_local_tools: Use free local tools (DuckDuckGo) instead of paid APIs
        """
        # Lazy import to avoid circular import
        from src.graph.graph_builder import ResearchGraph

        # Create agent factory with dependency injection
        factory = AgentFactory(ai_client=ai_client, use_local_tools=use_local_tools)

        # Create all agents
        specialists = factory.create_specialists()
        insight_gen = factory.create_insight_generator()
        writer = factory.create_report_writer()
        critic = factory.create_critic()

        # Build the graph with injected agents
        graph = ResearchGraph(
            agents=specialists,
            insight_generator=insight_gen,
            report_writer=writer,
            critic=critic,
        )

        self.graph = graph.compile()

    async def conduct_research(self, company_name: str, url: str) -> Dict[str, Any]:
        """
        Main entry point for the research process.

        .. deprecated::
            Use `src.pipeline.orchestrator.PipelineOrchestrator.conduct_research` instead.

        Args:
            company_name: Name of the company to research
            url: Company website URL

        Returns:
            Final research state as a dictionary
        """
        # Lazy import to avoid circular import
        from src.graph.state import ResearchState

        logger.info(f"Starting research for {company_name} ({url})")

        # Initialize state
        initial_state = ResearchState(company_name=company_name, website=url)

        # Run graph
        try:
            final_state_dict = await self.graph.ainvoke(initial_state.model_dump())

            # Convert back to Pydantic model
            final_state = ResearchState(**final_state_dict)

            logger.info("Research process completed successfully.")
            return final_state.model_dump()

        except KeyboardInterrupt:
            logger.info("Research interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Error during research execution: {str(e)}", exc_info=True)
            raise


# Thread-safe lazy singleton instance
_orchestrator: Optional["ResearchOrchestrator"] = None
_orchestrator_lock = threading.Lock()


def get_orchestrator(
    ai_client: Optional[BaseAIClient] = None, use_local_tools: bool = False
) -> ResearchOrchestrator:
    """
    Get or create the singleton orchestrator instance (thread-safe).

    Note: Once created, the orchestrator configuration is fixed.
    To use different settings, create a new instance directly.

    Args:
        ai_client: Optional AI client. If None, uses global manager.
        use_local_tools: Use free local tools (DuckDuckGo) instead of paid APIs

    Returns:
        ResearchOrchestrator instance
    """
    global _orchestrator
    with _orchestrator_lock:
        if _orchestrator is None:
            _orchestrator = ResearchOrchestrator(
                ai_client=ai_client, use_local_tools=use_local_tools
            )
        return _orchestrator


def reset_orchestrator() -> None:
    """Reset the singleton orchestrator (useful for testing)."""
    global _orchestrator
    with _orchestrator_lock:
        _orchestrator = None
