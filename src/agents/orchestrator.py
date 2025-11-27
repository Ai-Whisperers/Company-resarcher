from typing import Dict, Any
from src.core.logger import setup_logger
from src.graph.graph_builder import ResearchGraph
from src.graph.state import ResearchState
from src.agents.factory import get_agent_factory
from src.core.ai_client import BaseAIClient

logger = setup_logger(__name__)


class ResearchOrchestrator:
    """
    Main orchestrator for the research process.
    Uses dependency injection for all agents.
    """

    def __init__(self, ai_client: BaseAIClient = None, use_local_tools: bool = False):
        """
        Initialize the orchestrator with dependency injection.

        Args:
            ai_client: Optional AI client. If None, uses global manager.
            use_local_tools: Use free local tools (DuckDuckGo) instead of paid APIs
        """
        # Create agent factory
        # Pass use_local_tools to the factory constructor via get_agent_factory
        # We need to update get_agent_factory signature or call AgentFactory directly
        # Since get_agent_factory is a helper, let's instantiate directly for clarity here
        # or update the helper. Let's update the helper call if possible, but get_agent_factory
        # signature in factory.py is: def get_agent_factory(ai_client: BaseAIClient = None) -> AgentFactory

        # Let's import AgentFactory directly to be safe and explicit
        from src.agents.factory import AgentFactory

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

        Args:
            company_name: Name of the company to research
            url: Company website URL

        Returns:
            Final research state as a dictionary
        """
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


# Singleton instance (optional)
orchestrator = ResearchOrchestrator()
