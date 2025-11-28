"""
Research Pipeline - Orchestrates the complete company research process.

This is the main entry point for conducting research using the Pipeline architecture.
It replaces the LangGraph-based orchestrator with a simpler, more testable design.

Usage:
    from src.pipeline import ResearchPipeline

    # Create pipeline
    pipeline = ResearchPipeline()

    # Create company profile
    company = CompanyProfile(
        name="Acme Corp",
        website="https://acme.com",
        industry="Technology",
    )

    # Run research
    result = await pipeline.research(company)

    if result.is_success:
        for phase in result.output.phases:
            print(f"{phase.phase_name}: {len(phase.sources)} sources")
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.result import Result, Ok, Err
from ..core.types import CompanyProfile, ResearchPhaseResult

from .context import RequestContext, create_context
from .pipeline import Pipeline, PipelineConfig, PipelineResult, PipelineStatus
from .stage import Stage, StageError, StageResult, ParallelStage
from .stages.research import (
    ResearchInput,
    ResearchOutput,
    ResearchPhaseStage,
)


# =============================================================================
# Research Pipeline Configuration
# =============================================================================


@dataclass
class ResearchPipelineConfig:
    """
    Configuration for the research pipeline.

    Attributes:
        research_types: Which research types to perform
        parallel_phases: Run research phases in parallel (faster but uses more resources)
        max_sources_per_query: Maximum sources to fetch per search query
        timeout_seconds: Total timeout for the entire research process
        max_retries: Maximum retry attempts for failed stages
    """

    research_types: List[str] = field(default_factory=lambda: [
        "market",
        "financial",
        "competitor",
        "brand",
        "sales",
    ])
    parallel_phases: bool = True
    max_sources_per_query: int = 3
    timeout_seconds: float = 600.0  # 10 minutes default
    max_retries: int = 2


# =============================================================================
# Parallel Research Stage
# =============================================================================


class ParallelResearchStage(Stage[ResearchInput, ResearchOutput]):
    """
    Runs multiple research phases in parallel.

    This stage executes all configured research types concurrently,
    collecting results as they complete.
    """

    def __init__(
        self,
        research_types: List[str],
        max_sources_per_query: int = 3,
    ):
        self._research_types = research_types
        self._max_sources = max_sources_per_query
        self._phase_stages = [
            ResearchPhaseStage(rt, max_sources_per_query)
            for rt in research_types
        ]

    @property
    def name(self) -> str:
        return "parallel_research"

    async def execute(
        self,
        input: ResearchInput,
        ctx: RequestContext,
    ) -> Result[ResearchOutput, StageError]:
        ctx.logger.info(
            f"Starting parallel research",
            research_types=self._research_types,
        )

        # Run all phases in parallel
        tasks = [
            stage.run(input, ctx)
            for stage in self._phase_stages
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        phases: List[ResearchPhaseResult] = []
        errors: List[str] = []
        warnings: List[str] = []

        for i, result in enumerate(results):
            research_type = self._research_types[i]

            if isinstance(result, Exception):
                errors.append(f"{research_type}: {result}")
                ctx.logger.error(f"Phase {research_type} raised exception", error=str(result))

            elif result.is_ok:
                phase_result = result.unwrap().output
                phases.append(phase_result)
                ctx.logger.info(f"Phase {research_type} completed", sources=len(phase_result.sources))

            else:
                error = result.unwrap_err()
                errors.append(f"{research_type}: {error.message}")
                ctx.logger.warning(f"Phase {research_type} failed", error=error.message)

        ctx.logger.info(
            f"Parallel research completed",
            successful_phases=len(phases),
            failed_phases=len(errors),
        )

        # Return partial results even if some phases failed
        if not phases:
            return Err(StageError.partial_failure(
                self.name,
                "All research phases failed",
                details={"errors": errors},
            ))

        return Ok(ResearchOutput(
            company=input.company,
            phases=phases,
            errors=errors,
            warnings=warnings,
        ))


# =============================================================================
# Sequential Research Stage
# =============================================================================


class SequentialResearchStage(Stage[ResearchInput, ResearchOutput]):
    """
    Runs research phases sequentially.

    This stage executes research types one at a time, which is slower
    but uses fewer resources and provides better progress tracking.
    """

    def __init__(
        self,
        research_types: List[str],
        max_sources_per_query: int = 3,
    ):
        self._research_types = research_types
        self._max_sources = max_sources_per_query

    @property
    def name(self) -> str:
        return "sequential_research"

    async def execute(
        self,
        input: ResearchInput,
        ctx: RequestContext,
    ) -> Result[ResearchOutput, StageError]:
        phases: List[ResearchPhaseResult] = []
        errors: List[str] = []
        warnings: List[str] = []

        for research_type in self._research_types:
            # Check cancellation
            if ctx.cancellation.is_cancelled:
                warnings.append(f"Cancelled before {research_type}")
                break

            # Check timeout
            if not ctx.timeout_budget.has_time_remaining(min_required=30.0):
                warnings.append(f"Timeout before {research_type}")
                break

            ctx.logger.info(f"Starting phase: {research_type}")

            stage = ResearchPhaseStage(research_type, self._max_sources)
            result = await stage.run(input, ctx)

            if result.is_ok:
                phases.append(result.unwrap().output)
                ctx.logger.info(f"Completed phase: {research_type}")
            else:
                errors.append(f"{research_type}: {result.unwrap_err().message}")
                ctx.logger.warning(f"Phase failed: {research_type}")

        if not phases:
            return Err(StageError.partial_failure(
                self.name,
                "All research phases failed",
                details={"errors": errors},
            ))

        return Ok(ResearchOutput(
            company=input.company,
            phases=phases,
            errors=errors,
            warnings=warnings,
        ))


# =============================================================================
# Research Pipeline
# =============================================================================


class ResearchPipeline:
    """
    Main entry point for conducting company research.

    This pipeline orchestrates the complete research process:
    1. Generates search queries based on company profile
    2. Executes searches and fetches content
    3. Analyzes content using LLM
    4. Generates structured reports

    Example:
        pipeline = ResearchPipeline()

        company = CompanyProfile(
            name="Acme Corp",
            website="https://acme.com",
        )

        result = await pipeline.research(company)

        if result.is_success:
            output = result.output
            for phase in output.phases:
                print(phase.markdown_content)
    """

    def __init__(self, config: Optional[ResearchPipelineConfig] = None):
        """
        Initialize the research pipeline.

        Args:
            config: Pipeline configuration (uses defaults if not provided)
        """
        self.config = config or ResearchPipelineConfig()

        # Create the main research stage
        if self.config.parallel_phases:
            self._research_stage = ParallelResearchStage(
                research_types=self.config.research_types,
                max_sources_per_query=self.config.max_sources_per_query,
            )
        else:
            self._research_stage = SequentialResearchStage(
                research_types=self.config.research_types,
                max_sources_per_query=self.config.max_sources_per_query,
            )

        # Create the underlying pipeline
        self._pipeline = Pipeline(
            stages=[self._research_stage],
            config=PipelineConfig(
                max_retries=self.config.max_retries,
                timeout_seconds=self.config.timeout_seconds,
                checkpoint_enabled=True,
            ),
        )

    async def research(
        self,
        company: CompanyProfile,
        ctx: Optional[RequestContext] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult[ResearchOutput]:
        """
        Conduct research on a company.

        Args:
            company: The company to research
            ctx: Request context (created if not provided)
            extra_context: Additional context for prompts

        Returns:
            PipelineResult containing ResearchOutput with all phase results
        """
        # Create context if not provided
        if ctx is None:
            ctx = create_context(timeout_seconds=self.config.timeout_seconds)

        ctx.logger.info(
            f"Starting research for {company.name}",
            research_types=self.config.research_types,
            parallel=self.config.parallel_phases,
        )

        # Create input
        input = ResearchInput(
            company=company,
            research_types=self.config.research_types,
            max_sources_per_query=self.config.max_sources_per_query,
            extra_context=extra_context or {},
        )

        # Execute pipeline
        result = await self._pipeline.execute(input, ctx)

        ctx.logger.info(
            f"Research completed for {company.name}",
            status=result.status.value,
            phases=len(result.output.phases) if result.output else 0,
        )

        return result

    async def research_single(
        self,
        company: CompanyProfile,
        research_type: str,
        ctx: Optional[RequestContext] = None,
    ) -> PipelineResult[ResearchOutput]:
        """
        Conduct a single type of research on a company.

        Args:
            company: The company to research
            research_type: The type of research to perform
            ctx: Request context (created if not provided)

        Returns:
            PipelineResult containing ResearchOutput with single phase result
        """
        # Create a single-phase pipeline
        stage = ResearchPhaseStage(research_type, self.config.max_sources_per_query)

        if ctx is None:
            ctx = create_context(timeout_seconds=self.config.timeout_seconds / 2)

        input = ResearchInput(
            company=company,
            research_types=[research_type],
            max_sources_per_query=self.config.max_sources_per_query,
        )

        # Run the single stage
        result = await stage.run(input, ctx)

        if result.is_ok:
            phase_result = result.unwrap().output
            return PipelineResult(
                status=PipelineStatus.SUCCESS,
                output=ResearchOutput(
                    company=company,
                    phases=[phase_result],
                ),
                completed_stages=[result.unwrap()],
                started_at=result.unwrap().started_at,
                completed_at=result.unwrap().completed_at,
                request_id=ctx.request_id,
            )
        else:
            return PipelineResult(
                status=PipelineStatus.FAILED,
                error=result.unwrap_err(),
                failed_stage=research_type,
                request_id=ctx.request_id,
            )


# =============================================================================
# Factory Functions
# =============================================================================


def create_research_pipeline(
    research_types: Optional[List[str]] = None,
    parallel: bool = True,
    timeout_seconds: float = 600.0,
) -> ResearchPipeline:
    """
    Create a research pipeline with custom configuration.

    Args:
        research_types: Which research types to perform (default: all)
        parallel: Run phases in parallel (default: True)
        timeout_seconds: Total timeout (default: 600s)

    Returns:
        Configured ResearchPipeline instance
    """
    config = ResearchPipelineConfig(
        research_types=research_types or [
            "market",
            "financial",
            "competitor",
            "brand",
            "sales",
        ],
        parallel_phases=parallel,
        timeout_seconds=timeout_seconds,
    )
    return ResearchPipeline(config)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ResearchPipelineConfig",
    "ParallelResearchStage",
    "SequentialResearchStage",
    "ResearchPipeline",
    "create_research_pipeline",
]
