"""
Follow-up Question Generator - Generates follow-up questions based on research results.

This service analyzes completed research to:
- Identify knowledge gaps in the reports
- Generate targeted follow-up questions
- Suggest deeper research areas
- Integrate with interactive mode for user-guided exploration

Usage:
    from src.services.followup_generator import FollowupGenerator

    generator = FollowupGenerator()
    followups = await generator.generate_followups(research_result)

    for question in followups.questions:
        print(f"- {question.text} (priority: {question.priority})")
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from ...core.logging import setup_logger
from ...core.ai import get_ai_manager

logger = setup_logger("followup_generator")


class QuestionPriority(str, Enum):
    """Priority level for follow-up questions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QuestionCategory(str, Enum):
    """Category of follow-up question."""
    KNOWLEDGE_GAP = "knowledge_gap"
    DEEPER_ANALYSIS = "deeper_analysis"
    VERIFICATION = "verification"
    EXPANSION = "expansion"
    CLARIFICATION = "clarification"


@dataclass
class FollowupQuestion:
    """A single follow-up question with metadata."""
    text: str
    priority: QuestionPriority
    category: QuestionCategory
    phase: str  # Which research phase this relates to
    context: str = ""  # Why this question is important
    suggested_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "priority": self.priority.value,
            "category": self.category.value,
            "phase": self.phase,
            "context": self.context,
            "suggested_sources": self.suggested_sources,
        }


@dataclass
class FollowupResult:
    """Result of follow-up question generation."""
    questions: List[FollowupQuestion]
    company_name: str
    knowledge_gaps: List[str]
    suggested_research_areas: List[str]
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "questions": [q.to_dict() for q in self.questions],
            "company_name": self.company_name,
            "knowledge_gaps": self.knowledge_gaps,
            "suggested_research_areas": self.suggested_research_areas,
            "generated_at": self.generated_at.isoformat(),
            "total_questions": len(self.questions),
            "high_priority_count": sum(
                1 for q in self.questions if q.priority == QuestionPriority.HIGH
            ),
        }

    def get_by_priority(self, priority: QuestionPriority) -> List[FollowupQuestion]:
        """Get questions filtered by priority."""
        return [q for q in self.questions if q.priority == priority]

    def get_by_category(self, category: QuestionCategory) -> List[FollowupQuestion]:
        """Get questions filtered by category."""
        return [q for q in self.questions if q.category == category]

    def get_by_phase(self, phase: str) -> List[FollowupQuestion]:
        """Get questions filtered by research phase."""
        return [q for q in self.questions if q.phase == phase]


class FollowupGenerator:
    """
    Generates follow-up questions based on research results.

    Analyzes completed research to identify gaps, suggest deeper analysis,
    and generate targeted questions for further investigation.
    """

    # Prompt template for generating follow-up questions
    FOLLOWUP_PROMPT = """Analyze the following research results for {company_name} and generate follow-up questions.

## Research Results Summary

{research_summary}

## Your Task

Based on the research above, identify:

1. **Knowledge Gaps**: What important information is missing or incomplete?
2. **Deeper Analysis Needed**: What areas would benefit from more investigation?
3. **Verification Needed**: What claims should be verified with additional sources?
4. **Expansion Opportunities**: What related topics should be explored?

Generate 5-10 targeted follow-up questions. For each question, specify:
- The question text
- Priority (high/medium/low)
- Category (knowledge_gap/deeper_analysis/verification/expansion/clarification)
- Which research phase it relates to (market/financial/competitor/brand/sales)
- Brief context on why this question matters

Respond in JSON format:
{{
    "knowledge_gaps": ["gap1", "gap2"],
    "suggested_research_areas": ["area1", "area2"],
    "questions": [
        {{
            "text": "Question text here?",
            "priority": "high",
            "category": "knowledge_gap",
            "phase": "market",
            "context": "This matters because..."
        }}
    ]
}}
"""

    def __init__(self, ai_client=None):
        """
        Initialize the follow-up generator.

        Args:
            ai_client: AI client for generating questions (uses default if None)
        """
        self._ai_client = ai_client

    @property
    def ai_client(self):
        """Lazy-load AI client."""
        if self._ai_client is None:
            self._ai_client = get_ai_manager()
        return self._ai_client

    async def generate_followups(
        self,
        research_result: Dict[str, Any],
        max_questions: int = 10,
    ) -> FollowupResult:
        """
        Generate follow-up questions from research results.

        Args:
            research_result: The research result dictionary from PipelineOrchestrator
            max_questions: Maximum number of questions to generate

        Returns:
            FollowupResult with questions and analysis
        """
        company_name = research_result.get("company_name", "Unknown Company")

        # Build research summary
        summary = self._build_research_summary(research_result)

        # Generate follow-ups using AI
        prompt = self.FOLLOWUP_PROMPT.format(
            company_name=company_name,
            research_summary=summary,
        )

        try:
            response = await self.ai_client.generate(prompt)

            if response.is_err:
                logger.error(f"AI generation failed: {response.unwrap_err()}")
                return self._create_fallback_result(company_name, research_result)

            # Parse response
            parsed = self._parse_response(response.unwrap(), company_name)

            # Limit questions
            if len(parsed.questions) > max_questions:
                # Keep highest priority questions
                parsed.questions.sort(
                    key=lambda q: (
                        0 if q.priority == QuestionPriority.HIGH else
                        1 if q.priority == QuestionPriority.MEDIUM else 2
                    )
                )
                parsed.questions = parsed.questions[:max_questions]

            return parsed

        except Exception as e:
            logger.error(f"Error generating follow-ups: {e}")
            return self._create_fallback_result(company_name, research_result)

    def _build_research_summary(self, research_result: Dict[str, Any]) -> str:
        """Build a summary of the research for the prompt."""
        sections = []

        phases = research_result.get("phases", [])
        for phase in phases:
            phase_name = phase.get("phase_name", "unknown")
            content = phase.get("markdown_content", "")
            sources = phase.get("sources", [])
            errors = phase.get("errors", [])
            warnings = phase.get("warnings", [])

            # Truncate content if too long
            if len(content) > 2000:
                content = content[:2000] + "... [truncated]"

            section = f"### {phase_name.title()} Research\n\n"
            section += f"**Content:**\n{content}\n\n"
            section += f"**Sources Used:** {len(sources)}\n"

            if errors:
                section += f"**Errors:** {', '.join(errors)}\n"
            if warnings:
                section += f"**Warnings:** {', '.join(warnings)}\n"

            sections.append(section)

        # Add overall status
        status = research_result.get("status", "unknown")
        overall_errors = research_result.get("errors", [])

        summary = f"**Overall Status:** {status}\n"
        if overall_errors:
            summary += f"**Overall Errors:** {', '.join(overall_errors)}\n"
        summary += "\n---\n\n"
        summary += "\n---\n\n".join(sections)

        return summary

    def _parse_response(self, response: str, company_name: str) -> FollowupResult:
        """Parse AI response into FollowupResult."""
        import json

        # Try to extract JSON from response
        try:
            # Find JSON block
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return self._create_fallback_result(company_name, {})

        # Extract knowledge gaps and research areas
        knowledge_gaps = data.get("knowledge_gaps", [])
        suggested_areas = data.get("suggested_research_areas", [])

        # Parse questions
        questions = []
        for q in data.get("questions", []):
            try:
                question = FollowupQuestion(
                    text=q.get("text", ""),
                    priority=QuestionPriority(q.get("priority", "medium")),
                    category=QuestionCategory(q.get("category", "knowledge_gap")),
                    phase=q.get("phase", "general"),
                    context=q.get("context", ""),
                    suggested_sources=q.get("suggested_sources", []),
                )
                if question.text:  # Only add if has text
                    questions.append(question)
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse question: {e}")
                continue

        return FollowupResult(
            questions=questions,
            company_name=company_name,
            knowledge_gaps=knowledge_gaps,
            suggested_research_areas=suggested_areas,
        )

    def _create_fallback_result(
        self,
        company_name: str,
        research_result: Dict[str, Any],
    ) -> FollowupResult:
        """Create fallback result when AI generation fails."""
        # Generate basic questions based on phases
        questions = []
        phases = research_result.get("phases", [])

        phase_questions = {
            "market": [
                ("What is the total addressable market (TAM) for {company}?", QuestionPriority.HIGH),
                ("What are the key market trends affecting {company}?", QuestionPriority.MEDIUM),
            ],
            "financial": [
                ("What is {company}'s revenue growth rate?", QuestionPriority.HIGH),
                ("What are {company}'s key financial metrics?", QuestionPriority.MEDIUM),
            ],
            "competitor": [
                ("Who are {company}'s main competitors?", QuestionPriority.HIGH),
                ("What is {company}'s competitive advantage?", QuestionPriority.MEDIUM),
            ],
            "brand": [
                ("What is {company}'s brand positioning?", QuestionPriority.MEDIUM),
                ("What is the customer sentiment towards {company}?", QuestionPriority.LOW),
            ],
            "sales": [
                ("What are {company}'s primary sales channels?", QuestionPriority.MEDIUM),
                ("What is {company}'s pricing strategy?", QuestionPriority.MEDIUM),
            ],
        }

        # Check which phases have data and generate questions for gaps
        completed_phases = {p.get("phase_name") for p in phases if p.get("markdown_content")}

        for phase, phase_qs in phase_questions.items():
            if phase not in completed_phases:
                for text_template, priority in phase_qs:
                    questions.append(FollowupQuestion(
                        text=text_template.format(company=company_name),
                        priority=priority,
                        category=QuestionCategory.KNOWLEDGE_GAP,
                        phase=phase,
                        context=f"No data found for {phase} research phase",
                    ))

        # Add general follow-up questions
        questions.append(FollowupQuestion(
            text=f"What are the key risks facing {company_name}?",
            priority=QuestionPriority.HIGH,
            category=QuestionCategory.DEEPER_ANALYSIS,
            phase="general",
            context="Risk assessment is critical for investment decisions",
        ))

        return FollowupResult(
            questions=questions,
            company_name=company_name,
            knowledge_gaps=["Unable to analyze - AI generation failed"],
            suggested_research_areas=[
                "Market size and growth",
                "Competitive positioning",
                "Financial health",
                "Risk factors",
            ],
        )

    async def generate_for_phase(
        self,
        phase_name: str,
        phase_content: str,
        company_name: str,
        max_questions: int = 5,
    ) -> List[FollowupQuestion]:
        """
        Generate follow-up questions for a specific research phase.

        Args:
            phase_name: Name of the research phase
            phase_content: Content from that phase
            company_name: Company name
            max_questions: Maximum questions to generate

        Returns:
            List of follow-up questions for this phase
        """
        prompt = f"""Analyze this {phase_name} research for {company_name} and generate {max_questions} follow-up questions.

## Research Content
{phase_content[:3000]}

Generate targeted follow-up questions to fill knowledge gaps or deepen understanding.
Respond in JSON format with a "questions" array containing objects with "text", "priority", and "context" fields.
"""

        try:
            response = await self.ai_client.generate(prompt)

            if response.is_err:
                return []

            # Parse response
            import json
            response_text = response.unwrap()
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start >= 0 and end > start:
                data = json.loads(response_text[start:end])
                questions = []

                for q in data.get("questions", [])[:max_questions]:
                    questions.append(FollowupQuestion(
                        text=q.get("text", ""),
                        priority=QuestionPriority(q.get("priority", "medium")),
                        category=QuestionCategory.DEEPER_ANALYSIS,
                        phase=phase_name,
                        context=q.get("context", ""),
                    ))

                return questions

        except Exception as e:
            logger.error(f"Error generating phase follow-ups: {e}")

        return []


# =============================================================================
# Factory Functions
# =============================================================================


def get_followup_generator(ai_client=None) -> FollowupGenerator:
    """
    Get a follow-up generator instance.

    Args:
        ai_client: Optional AI client (uses default if None)

    Returns:
        FollowupGenerator instance
    """
    return FollowupGenerator(ai_client=ai_client)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "QuestionPriority",
    "QuestionCategory",
    # Data Classes
    "FollowupQuestion",
    "FollowupResult",
    # Main Class
    "FollowupGenerator",
    # Factory Functions
    "get_followup_generator",
]
