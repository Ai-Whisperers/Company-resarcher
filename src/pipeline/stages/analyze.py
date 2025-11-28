"""
AnalyzeStage - Generate AI analysis from fetched content.

This stage uses the AI client to analyze content and produce
structured insights.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...core.result import Result, Ok, Err
from ...services.json_parser_helper import robust_json_parse

from ..context import RequestContext
from ..stage import Stage, StageError

from .fetch import FetchOutput


# =============================================================================
# Input/Output Types
# =============================================================================


@dataclass
class AnalyzeInput:
    """
    Input for the AnalyzeStage.

    Attributes:
        content: Content to analyze (from FetchOutput or raw text)
        analysis_type: Type of analysis to perform
        company_name: Name of the company being analyzed
        additional_context: Extra context for the analysis
    """

    content: str
    analysis_type: str = "general"  # general, financial, market, competitor
    company_name: str = ""
    additional_context: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_fetch_output(
        cls,
        fetch_output: FetchOutput,
        analysis_type: str = "general",
        company_name: str = "",
        max_content_length: int = 50000,
    ) -> "AnalyzeInput":
        """Create AnalyzeInput from FetchOutput."""
        # Combine all fetched content
        combined = []
        for item in fetch_output.content:
            source_text = f"Source: {item.title}\nURL: {item.url}\n"
            # Truncate individual content to avoid one source dominating
            content_preview = item.content[:5000] if item.content else ""
            combined.append(f"{source_text}Content:\n{content_preview}")

        full_content = "\n\n---\n\n".join(combined)

        # Truncate total if needed
        if len(full_content) > max_content_length:
            full_content = full_content[:max_content_length] + "\n\n[Content truncated]"

        return cls(
            content=full_content,
            analysis_type=analysis_type,
            company_name=company_name,
            additional_context={
                "source_count": len(fetch_output.content),
                "failed_sources": len(fetch_output.failed_urls),
            },
        )


@dataclass
class AnalysisSection:
    """A section of the analysis output."""

    title: str
    content: str
    confidence: float = 0.8  # 0-1 confidence in this section


@dataclass
class AnalyzeOutput:
    """
    Output from the AnalyzeStage.

    Attributes:
        summary: Executive summary of the analysis
        sections: Detailed analysis sections
        key_findings: List of key findings
        raw_response: Raw AI response for debugging
        analysis_type: Type of analysis performed
    """

    summary: str = ""
    sections: List[AnalysisSection] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    raw_response: str = ""
    analysis_type: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility."""
        return {
            "summary": self.summary,
            "sections": [
                {"title": s.title, "content": s.content, "confidence": s.confidence}
                for s in self.sections
            ],
            "key_findings": self.key_findings,
            "analysis_type": self.analysis_type,
        }


# =============================================================================
# Analysis Prompts
# =============================================================================

ANALYSIS_PROMPTS = {
    "general": """Analyze the following content about {company_name} and provide a structured analysis.

Content:
{content}

Provide your analysis as JSON with this structure:
{{
    "summary": "Executive summary (2-3 sentences)",
    "sections": [
        {{"title": "Section Title", "content": "Detailed analysis", "confidence": 0.8}}
    ],
    "key_findings": ["Finding 1", "Finding 2", "Finding 3"]
}}

Focus on actionable insights and be specific about what you found.""",

    "financial": """Analyze the following financial information about {company_name}.

Content:
{content}

Provide your analysis as JSON with this structure:
{{
    "summary": "Financial overview (2-3 sentences)",
    "sections": [
        {{"title": "Revenue & Growth", "content": "Analysis", "confidence": 0.8}},
        {{"title": "Profitability", "content": "Analysis", "confidence": 0.8}},
        {{"title": "Financial Health", "content": "Analysis", "confidence": 0.8}}
    ],
    "key_findings": ["Key financial insight 1", "Key financial insight 2"]
}}""",

    "market": """Analyze the market context for {company_name} based on the following content.

Content:
{content}

Provide your analysis as JSON with this structure:
{{
    "summary": "Market position overview (2-3 sentences)",
    "sections": [
        {{"title": "Market Size & Trends", "content": "Analysis", "confidence": 0.8}},
        {{"title": "Competitive Position", "content": "Analysis", "confidence": 0.8}},
        {{"title": "Growth Opportunities", "content": "Analysis", "confidence": 0.8}}
    ],
    "key_findings": ["Market insight 1", "Market insight 2"]
}}""",

    "competitor": """Analyze the competitive landscape for {company_name} based on the following content.

Content:
{content}

Provide your analysis as JSON with this structure:
{{
    "summary": "Competitive overview (2-3 sentences)",
    "sections": [
        {{"title": "Key Competitors", "content": "Analysis", "confidence": 0.8}},
        {{"title": "Competitive Advantages", "content": "Analysis", "confidence": 0.8}},
        {{"title": "Competitive Threats", "content": "Analysis", "confidence": 0.8}}
    ],
    "key_findings": ["Competitive insight 1", "Competitive insight 2"]
}}""",
}


# =============================================================================
# AnalyzeStage
# =============================================================================


class AnalyzeStage(Stage[AnalyzeInput, AnalyzeOutput]):
    """
    Generate AI analysis from content.

    This stage:
    1. Constructs a prompt based on analysis type
    2. Calls the AI client via context
    3. Parses the JSON response
    4. Returns typed AnalyzeOutput
    """

    @property
    def name(self) -> str:
        return "analyze"

    def validate_input(self, input: AnalyzeInput) -> Optional[StageError]:
        """Validate analysis input."""
        if not input.content or not input.content.strip():
            return StageError.invalid_input(
                message="No content provided for analysis",
            )

        if input.analysis_type not in ANALYSIS_PROMPTS:
            return StageError.invalid_input(
                message=f"Unknown analysis type: {input.analysis_type}",
                details={"valid_types": list(ANALYSIS_PROMPTS.keys())},
            )

        return None

    async def execute(
        self,
        input: AnalyzeInput,
        ctx: RequestContext,
    ) -> Result[AnalyzeOutput, StageError]:
        """Execute AI analysis."""
        ctx.logger.info(
            f"Generating analysis",
            analysis_type=input.analysis_type,
            content_length=len(input.content),
        )

        # Build prompt
        prompt_template = ANALYSIS_PROMPTS.get(input.analysis_type, ANALYSIS_PROMPTS["general"])
        prompt = prompt_template.format(
            company_name=input.company_name or "the company",
            content=input.content,
        )

        # Call AI using context's client
        try:
            if hasattr(ctx.ai_client, "generate_safe"):
                result = await ctx.ai_client.generate_safe(
                    prompt=prompt,
                    response_format="json",
                    temperature=0.3,  # Lower temperature for more consistent output
                )

                if result.is_err:
                    error = result.unwrap_err()
                    return Err(
                        StageError.ai_error(
                            message=str(error),
                            retryable=getattr(error, "recoverable", True),
                            details={"error_code": getattr(error, "code", "UNKNOWN")},
                        )
                    )

                raw_response = result.unwrap()
            else:
                raw_response = await ctx.ai_client.generate(
                    prompt=prompt,
                    response_format="json",
                )

        except Exception as e:
            ctx.logger.exception(f"AI call failed: {e}")
            return Err(
                StageError.ai_error(
                    message=f"AI generation failed: {str(e)}",
                    retryable=True,
                )
            )

        # Parse response
        try:
            data = robust_json_parse(raw_response)
        except Exception as e:
            ctx.logger.warning(f"Failed to parse AI response: {e}")
            return Err(
                StageError.parse_error(
                    message=f"Failed to parse AI response: {e}",
                    raw_output=raw_response[:500] if raw_response else None,
                )
            )

        # Build output
        sections = []
        for section_data in data.get("sections", []):
            sections.append(
                AnalysisSection(
                    title=section_data.get("title", ""),
                    content=section_data.get("content", ""),
                    confidence=section_data.get("confidence", 0.8),
                )
            )

        output = AnalyzeOutput(
            summary=data.get("summary", ""),
            sections=sections,
            key_findings=data.get("key_findings", []),
            raw_response=raw_response,
            analysis_type=input.analysis_type,
        )

        ctx.logger.info(
            f"Analysis complete",
            sections=len(output.sections),
            findings=len(output.key_findings),
        )

        return Ok(output)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AnalyzeStage",
    "AnalyzeInput",
    "AnalyzeOutput",
    "AnalysisSection",
]
