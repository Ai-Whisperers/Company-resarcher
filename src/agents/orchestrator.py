import asyncio
from datetime import datetime
from typing import List, Dict, Any
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.logger import setup_logger
from ..core.research_phases import RESEARCH_PHASES
from ..tools.file_manager import FileManager
from .base_agent import BaseAgent

# from .specialists import MarketAnalyst, BrandAuditor, CompetitorScout # Deprecated

logger = setup_logger("orchestrator")


class ResearchOrchestrator:
    """
    Orchestrates the entire research process using specialized agents
    and the defined research phases.
    """

    def __init__(self):
        self.file_manager = FileManager()
        self.agents = {}

        # Initialize agents for all phases
        from .generic_agent import GenericResearchAgent

        for phase_id, config in RESEARCH_PHASES.items():
            self.agents[phase_id] = GenericResearchAgent(phase_id, config)

    async def run_research(self, company_name: str, industry: str) -> None:
        """
        Run the full research pipeline for a company.
        """
        start_time = datetime.now()
        logger.info(f"Starting research for {company_name} ({industry})")

        # 1. Setup Company Profile
        company = CompanyProfile(
            name=company_name,
            industry=industry,
            target_audience=f"{industry} consumers",  # Default
            country="Global",  # Default
        )

        # 2. Initialize Output Structure
        self.file_manager.setup_company_folder(company_name)

        # 3. Execute Research Phases
        # We iterate through the defined phases in order
        sorted_phases = sorted(RESEARCH_PHASES.items(), key=lambda x: x[1]["priority"])

        results = []

        for phase_id, phase_config in sorted_phases:
            logger.info(f"Starting Phase: {phase_config['name']}")

            # Determine which agent to use
            agent = self.agents.get(phase_id)

            if agent:
                try:
                    # We inject the specific queries from the phase config into the agent
                    # This requires updating the agent interface or passing it here
                    # For now, let's assume the specialist agents have their own logic,
                    # BUT we should ideally pass the 'query_templates' to them.

                    # Let's update the agent's research method to accept phase_config if possible
                    # Or we can just let the specialized agents do their thing for now
                    # and eventually migrate them to be fully data-driven.

                    # To make it truly data-driven as per the reference repo:
                    # We should probably have a 'GenericResearchAgent' that takes the queries.
                    # But since we have specific classes, let's stick to them for the main 3,
                    # and maybe skip the others for this MVP or implement a generic fallback.

                    result = await agent.research(company)

                    # Save Result
                    await self.file_manager.save_report(company_name, result)
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error in phase {phase_id}: {e}")
            else:
                logger.warning(f"No agent assigned for phase {phase_id}, skipping.")

        # 4. Generate Executive Summary (Final Synthesis)
        # TODO: Implement this using the collected results

        duration = datetime.now() - start_time
        logger.info(f"Research completed in {duration}")
