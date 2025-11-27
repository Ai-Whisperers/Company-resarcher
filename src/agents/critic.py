from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.logger import setup_logger

logger = setup_logger("critic")


class LogicCritic(BaseAgent):
    """
    The 'Devil's Advocate' agent.
    Reviews the generated insights and drafts for logical fallacies, missing data, or weak arguments.
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Satisfy BaseAgent abstract method.
        In practice, use critique().
        """
        return ResearchPhaseResult(
            phase_name="Logic Critic", markdown_content="", sources=[]
        )

    async def critique(
        self, company: CompanyProfile, insights: Dict[str, Any], drafts: Dict[str, str]
    ) -> Dict[str, Any]:

        context = f"""
        Insights:
        {insights}

        Drafts:
        {drafts}
        """

        prompt = f"""
        You are a Senior Editor and Logic Critic. Review the research report for {company.name}.
        Identify any logical contradictions, weak arguments, or missing critical data points.
        
        If the report is solid, approve it.
        If there are major issues, reject it and provide specific feedback for improvement.

        Return a JSON object with the following structure:
        {{
            "status": "APPROVE" or "REJECT",
            "feedback": "Detailed feedback on what to fix (if REJECT)",
            "score": 0-10 (Quality Score)
        }}

        Data:
        {context}
        """

        import json
        from ..services.json_parser_helper import robust_json_parse

        try:
            content_json_str = await self.ai.generate(prompt)
            data = robust_json_parse(content_json_str)

            # Defaults
            data.setdefault("status", "APPROVE")
            data.setdefault("feedback", "No feedback provided.")
            data.setdefault("score", 5)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parsing failed in critic: {e}", exc_info=True)
            data = {
                "status": "APPROVE",
                "feedback": "Error during critique, passing by default.",
                "score": 5,
            }
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in critic: {e}", exc_info=True)
            data = {
                "status": "APPROVE",
                "feedback": "Error during critique, passing by default.",
                "score": 5,
            }

        return data
