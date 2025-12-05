"""
Research Planning Stage - AI-first research intelligence brief generation.

This stage runs BEFORE any web scraping to generate a ResearchIntelligenceBrief
that guides all subsequent stages with company-specific knowledge.

The brief provides:
- Targeted search queries (instead of generic templates)
- Entity disambiguation hints (to filter wrong companies)
- Relevance criteria (to prioritize sources)
- Predicted gaps (to set expectations)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import jinja2

from src.core.result import Result, Ok, Err
from src.core.types import CompanyProfile, ResearchIntelligenceBrief, create_empty_brief
from src.infrastructure.content import robust_json_parse

from src.pipeline.context import RequestContext
from src.pipeline.stage import Stage, StageError

# Progress tracking for dashboard updates
from src.core.logging.progress import get_progress_tracker


# =============================================================================
# Planning Input/Output Types
# =============================================================================


class PlanningInput:
    """Input for the research planning stage."""

    def __init__(
        self,
        company: CompanyProfile,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        self.company = company
        self.extra_context = extra_context or {}


# =============================================================================
# Research Planning Stage
# =============================================================================


class ResearchPlanningStage(Stage[PlanningInput, ResearchIntelligenceBrief]):
    """
    AI-first stage that creates a Research Intelligence Brief.

    This stage uses AI to analyze the company profile and generate
    a comprehensive research plan BEFORE any web scraping begins.

    The generated brief guides:
    - QueryGenerationStage: Uses priority_queries for targeted search
    - ComprehensiveFilter: Uses entity_identifiers and exclusion_patterns
    - AnalysisStage: Uses predicted_gaps for gap-aware synthesis

    Example:
        stage = ResearchPlanningStage()
        input = PlanningInput(company=company_profile)
        result = await stage.execute(input, ctx)

        if result.is_ok:
            brief = result.unwrap()
            # Use brief.priority_queries for search
            # Use brief.entity_identifiers for filtering
    """

    def __init__(self):
        self._template: Optional[jinja2.Template] = None
        self._prompts_dir = Path(__file__).parent.parent.parent / "prompts"

    @property
    def name(self) -> str:
        return "research_planning"

    def _load_template(self) -> jinja2.Template:
        """Load the research planning prompt template."""
        if self._template is None:
            template_path = self._prompts_dir / "research_planning.txt"
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            self._template = jinja2.Template(template_content)
        return self._template

    def _build_prompt(self, input: PlanningInput) -> str:
        """Build the AI prompt from company profile."""
        template = self._load_template()

        # Prepare template context
        context = {
            "company": input.company,
            **input.extra_context,
        }

        return template.render(**context)

    async def execute(
        self,
        input: PlanningInput,
        ctx: RequestContext,
    ) -> Result[ResearchIntelligenceBrief, StageError]:
        """
        Execute the research planning stage.

        Uses AI to generate a ResearchIntelligenceBrief based on
        the company profile. This brief will guide all subsequent
        research stages.
        """
        ctx.logger.info(
            f"Generating research intelligence brief for: {input.company.name}"
        )

        # Update progress tracker
        tracker = get_progress_tracker()
        if tracker:
            tracker.start_task(f"Planning research for {input.company.name}")

        try:
            # Build the prompt
            prompt = self._build_prompt(input)

            # Check timeout budget
            if not ctx.timeout_budget.has_time_remaining(min_required=10.0):
                ctx.logger.warning("Timeout budget too low for planning, using empty brief")
                return Ok(create_empty_brief())

            # Call AI to generate the brief
            ctx.logger.debug("Calling AI for research planning...")

            response = await ctx.ai_client.generate(
                prompt=prompt,
                system="You are a research strategist. Return only valid JSON.",
                temperature=0.7,
                max_tokens=4096,
                response_format="json_object",
            )

            # Parse the response
            parsed = robust_json_parse(response)

            if parsed is None:
                ctx.logger.warning(
                    "Failed to parse AI response for research planning",
                    raw_response=response[:500] if response else "empty",
                )
                # Return empty brief instead of failing
                return Ok(create_empty_brief())

            # Create the brief from parsed data
            try:
                brief = ResearchIntelligenceBrief.from_dict(parsed)
            except Exception as e:
                ctx.logger.warning(
                    f"Failed to create brief from parsed data: {e}",
                    parsed_keys=list(parsed.keys()) if isinstance(parsed, dict) else "not_dict",
                )
                # Try to salvage what we can
                brief = self._create_partial_brief(parsed, input.company)

            ctx.logger.info(
                f"Research brief generated",
                confidence=brief.confidence_score,
                query_types=list(brief.priority_queries.keys()),
                entity_identifiers=len(brief.entity_identifiers),
            )

            # Update progress
            if tracker:
                tracker.complete_task(f"Planning research for {input.company.name}")

            return Ok(brief)

        except Exception as e:
            ctx.logger.exception(f"Research planning failed: {e}")

            # Don't fail the pipeline - return empty brief
            ctx.logger.warning("Falling back to empty brief due to planning failure")
            return Ok(create_empty_brief())

    def _create_partial_brief(
        self,
        parsed: Dict[str, Any],
        company: CompanyProfile,
    ) -> ResearchIntelligenceBrief:
        """Create a partial brief from whatever data we could parse."""
        brief = create_empty_brief()

        # Try to extract what we can
        if isinstance(parsed, dict):
            # Extract priority queries if available
            if "priority_queries" in parsed and isinstance(parsed["priority_queries"], dict):
                try:
                    from src.core.types.research_brief import PriorityQuery
                    for key, queries in parsed["priority_queries"].items():
                        if isinstance(queries, list):
                            brief.priority_queries[key] = [
                                PriorityQuery(**q) if isinstance(q, dict) else PriorityQuery(query=str(q))
                                for q in queries
                            ]
                except Exception:
                    pass

            # Extract relevance keywords
            if "relevance_keywords" in parsed and isinstance(parsed["relevance_keywords"], list):
                brief.relevance_keywords = [str(k) for k in parsed["relevance_keywords"]]

            # Extract target domains
            if "target_domains" in parsed and isinstance(parsed["target_domains"], list):
                brief.target_domains = [str(d) for d in parsed["target_domains"]]

            # Extract language hints
            if "language_hints" in parsed and isinstance(parsed["language_hints"], list):
                brief.language_hints = [str(l) for l in parsed["language_hints"]]

            # Extract key questions
            if "key_questions" in parsed and isinstance(parsed["key_questions"], list):
                brief.key_questions = [str(q) for q in parsed["key_questions"]]

            # Set confidence to partial
            brief.confidence_score = 0.3
            brief.reasoning = "Partial brief - some fields could not be parsed"

        return brief


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PlanningInput",
    "ResearchPlanningStage",
]
