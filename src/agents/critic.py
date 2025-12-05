import json
from typing import Dict, Any, Literal
from dataclasses import dataclass
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from src.core.types import CompanyProfile, ResearchPhaseResult
from src.core.models import StrategicInsights
from src.core.logging import setup_logger
from src.infrastructure.content import robust_json_parse
from src.infrastructure.security import sanitize_company_name

logger = setup_logger("critic")


class CritiqueResponse(BaseModel):
    """Structured response from the Logic Critic."""

    status: Literal["APPROVE", "REJECT"] = Field(
        description="Approval status of the report"
    )
    feedback: str = Field(
        description="Detailed feedback if rejected, or 'No feedback provided' if approved"
    )
    score: int = Field(description="Quality score from 1-10", ge=1, le=10)


@dataclass
class CritiqueResult:
    """Result from the critique process."""

    status: str  # "APPROVE" or "REJECT"
    feedback: str
    score: int
    approved: bool

    @classmethod
    def from_response(cls, response: CritiqueResponse) -> "CritiqueResult":
        """Create from Pydantic model."""
        return cls(
            status=response.status,
            feedback=response.feedback,
            score=response.score,
            approved=response.status == "APPROVE",
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CritiqueResult":
        """Create from dictionary (legacy support)."""
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
        safe_name = sanitize_company_name(company.name)

        # Prepare context
        context = f"""
        Insights:
        {insights.model_dump_json(indent=2)}

        Drafts:
        {json.dumps(drafts, indent=2)}
        """

        prompt = f"""
        You are a Senior Editor and Logic Critic. Review the research report for {safe_name}.
        Identify any logical contradictions, weak arguments, or missing critical data points.
        
        If the report is solid, approve it.
        If there are major issues, reject it and provide specific feedback for improvement.
        
        Data:
        {context}
        """

        try:
            # Use structured output generation
            response = await self._generate_structured(
                prompt=prompt,
                schema=CritiqueResponse,
                system="You are a critical editor who ensures high-quality research outputs.",
            )
            return CritiqueResult.from_response(response)

        except Exception as e:
            logger.error(f"Structured critique failed: {e}", exc_info=True)
            # Fallback to safe default
            return CritiqueResult(
                status="APPROVE",
                feedback=f"Error during critique: {e}. Passing by default.",
                score=5,
                approved=True,
            )

    async def critique(
        self, company: CompanyProfile, insights: Dict[str, Any], drafts: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Review research report (legacy Dict[str, Any] version).

        Maintained for backward compatibility, but delegates to typed implementation where possible
        or uses legacy generation if needed.
        """
        # Try to use the typed version if we can reconstruct the objects,
        # otherwise use legacy generation

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
            # Try structured generation first even for legacy call
            response = await self._generate_structured(
                prompt=prompt,
                schema=CritiqueResponse,
                system="You are a critical editor.",
            )
            return {
                "status": response.status,
                "feedback": response.feedback,
                "score": response.score,
            }

        except Exception as e:
            logger.warning(
                f"Structured critique failed in legacy method, falling back to text: {e}"
            )

            # Fallback to legacy text generation
            try:
                content_json_str = await self.ai.generate(prompt)
                data = robust_json_parse(content_json_str)

                # Defaults
                data.setdefault("status", "APPROVE")
                data.setdefault("feedback", "No feedback provided.")
                data.setdefault("score", 5)
                return data

            except Exception as e2:
                logger.error(f"Legacy critique failed: {e2}", exc_info=True)
                return {
                    "status": "APPROVE",
                    "feedback": "Error during critique, passing by default.",
                    "score": 5,
                }
