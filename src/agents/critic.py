import json
from typing import Dict, Any
from dataclasses import dataclass

from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.models import StrategicInsights
from ..core.logging import setup_logger
from ..services.content import robust_json_parse
from ..services.security import sanitize_company_name

logger = setup_logger("critic")


@dataclass
class CritiqueResult:
    """Result from the critique process."""

    status: str  # "APPROVE" or "REJECT"
    feedback: str
    score: int
    approved: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CritiqueResult":
        """Create from dictionary."""
        status = data.get("status", "APPROVE")
        return cls(
            status=status,
            feedback=data.get("feedback", "No feedback provided."),
            score=data.get("score", 5),
            approved=status == "APPROVE",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "status": self.status,
            "feedback": self.feedback,
            "score": self.score,
        }


class LogicCritic(BaseAgent):
    """
    The 'Devil's Advocate' agent.
    Reviews the generated insights and drafts for logical fallacies, missing data, or weak arguments.
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Satisfy BaseAgent abstract method.
        In practice, use critique() or critique_typed().
        """
        return ResearchPhaseResult(
            phase_name="Logic Critic", markdown_content="", sources=[]
        )

    async def critique_typed(
        self,
        company: CompanyProfile,
        insights: StrategicInsights,
        drafts: Dict[str, str],
    ) -> CritiqueResult:
        """
        Review research report using typed models (recommended).

        Args:
            company: Company profile
            insights: Typed strategic insights
            drafts: Dictionary of draft documents

        Returns:
            CritiqueResult with approval status and feedback
        """
        # Convert to dict for internal processing
        result_dict = await self.critique(
            company=company,
            insights=insights.to_legacy_dict(),
            drafts=drafts,
        )
        return CritiqueResult.from_dict(result_dict)

    async def critique(
        self, company: CompanyProfile, insights: Dict[str, Any], drafts: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Review research report (legacy Dict[str, Any] version).

        For new code, prefer critique_typed() which provides type safety.
        """

        context = f"""
        Insights:
        {insights}

        Drafts:
        {drafts}
        """

        safe_name = sanitize_company_name(company.name)
        prompt = f"""
        You are a Senior Editor and Logic Critic. Review the research report for {safe_name}.
        Identify any logical contradictions, weak arguments, or missing critical data points.
        
        If the report is solid, approve it.
        If there are major issues, reject it and provide specific feedback for improvement.

        Return a JSON object with the following structure:
        {{
            "status": "APPROVE",
            "feedback": "Detailed feedback on what to fix (if status is REJECT)",
            "score": 8
        }}

        Note: status must be exactly "APPROVE" or "REJECT" (string value).

        Data:
        {context}
        """

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
        except Exception as e:
            logger.error(f"Unexpected error in critic: {e}", exc_info=True)
            data = {
                "status": "APPROVE",
                "feedback": "Error during critique, passing by default.",
                "score": 5,
            }

        return data
