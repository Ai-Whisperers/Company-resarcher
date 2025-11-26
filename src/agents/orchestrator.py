import asyncio
from typing import Dict, Any, List
from src.core.logger import setup_logger
from src.graph.graph_builder import build_graph
from src.graph.state import ResearchState

logger = setup_logger(__name__)


class ResearchOrchestrator:
    def __init__(self):
        self.graph = build_graph()

    async def conduct_research(self, company_name: str, url: str) -> Dict[str, Any]:
        """
        Main entry point for the research process.
        Initializes the state and runs the LangGraph workflow.
        """
        logger.info(f"Starting research for {company_name} ({url})")

        # Initialize State
        initial_state = ResearchState(company_name=company_name, website=url)

        # Run Graph
        try:
            # ainvoke returns the final state dict
            final_state_dict = await self.graph.ainvoke(initial_state.model_dump())

            # Convert back to Pydantic model for type safety (optional, but good practice)
            final_state = ResearchState(**final_state_dict)

            logger.info("Research process completed successfully.")
            return final_state.model_dump()

        except Exception as e:
            logger.error(f"Error during research execution: {str(e)}")
            raise e


# Singleton instance (optional, but useful if we want to cache the graph build)
orchestrator = ResearchOrchestrator()
