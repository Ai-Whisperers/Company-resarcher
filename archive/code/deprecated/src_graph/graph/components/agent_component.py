from langflow.custom import CustomComponent
from langflow.field_typing import Data
from typing import Optional, Dict, Any
from src.agents.factory import AgentFactory
from src.core.types import CompanyProfile


class AgentComponent(CustomComponent):
    display_name = "Research Agent"
    description = "Instantiate and run a specific research agent."
    icon = "bot"

    def build_config(self):
        return {
            "agent_type": {
                "display_name": "Agent Type",
                "options": ["financial", "market", "competitor", "brand", "sales"],
                "value": "financial",
            },
            "company_name": {
                "display_name": "Company Name",
                "info": "Name of the company to research.",
            },
            "industry": {
                "display_name": "Industry",
                "info": "Industry of the company (optional).",
            },
        }

    def build(
        self,
        agent_type: str,
        company_name: str,
        industry: Optional[str] = None,
    ) -> Data:
        # Create agent using factory
        agent = AgentFactory.create_agent(agent_type)

        # Create company profile
        company = CompanyProfile(name=company_name, industry=industry)

        # Run async code in sync context
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Execute research
        result = loop.run_until_complete(agent.research(company))

        # Convert result to Data
        return Data(
            data={
                "phase": result.phase_name,
                "content": result.markdown_content,
                "sources": [s.dict() for s in result.sources],
                "errors": result.errors,
                "warnings": result.warnings,
            }
        )
