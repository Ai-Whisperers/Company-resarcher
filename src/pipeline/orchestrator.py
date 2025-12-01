"""
Pipeline Orchestrator - Replacement for the LangGraph-based ResearchOrchestrator.

This module provides a simpler, more testable orchestrator that uses the
Pipeline architecture instead of LangGraph's state machine.

Benefits over LangGraph approach:
1. Explicit typed stages instead of implicit state mutations
2. Built-in retry, timeout, and cancellation support
3. Easier to test with dependency injection
4. Better error reporting and observability
5. No complex graph compilation step

Usage:
    from src.pipeline.orchestrator import PipelineOrchestrator

    orchestrator = PipelineOrchestrator()
    result = await orchestrator.conduct_research("Acme Corp", "https://acme.com")

    if result["status"] == "success":
        print(result["phases"])
"""

from __future__ import annotations

import threading
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from ..core.types import CompanyProfile
from ..core.logger import setup_logger
from ..services.html_cache import get_html_cache

from .context import RequestContext, create_context
from .research_pipeline import (
    ResearchPipeline,
    ResearchPipelineConfig,
)
from .pipeline import PipelineStatus

logger = setup_logger(__name__)


class PipelineOrchestrator:
    """
    Main orchestrator for the research process using the Pipeline architecture.

    This replaces the LangGraph-based ResearchOrchestrator with a simpler,
    more testable design that uses explicit typed stages.

    Example:
        orchestrator = PipelineOrchestrator()

        result = await orchestrator.conduct_research(
            company_name="Acme Corp",
            url="https://acme.com",
        )

        if result["status"] == "success":
            for phase in result["phases"]:
                print(f"{phase['phase_name']}: {len(phase['sources'])} sources")
    """

    def __init__(
        self,
        research_types: Optional[List[str]] = None,
        parallel: bool = True,
        timeout_seconds: float = 600.0,
        max_retries: int = 2,
    ):
        """
        Initialize the orchestrator.

        Args:
            research_types: Which research types to perform (default: all)
            parallel: Run research phases in parallel (default: True)
            timeout_seconds: Total timeout for research (default: 600s)
            max_retries: Maximum retry attempts for failed stages (default: 2)
        """
        self._config = ResearchPipelineConfig(
            research_types=research_types or [
                "market",
                "financial",
                "competitor",
                "brand",
                "sales",
            ],
            parallel_phases=parallel,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        self._pipeline = ResearchPipeline(self._config)

    async def conduct_research(
        self,
        company_name: str,
        url: str,
        industry: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for the research process.

        Args:
            company_name: Name of the company to research
            url: Company website URL
            industry: Company's industry (optional)
            extra_context: Additional context for prompts

        Returns:
            Dictionary with research results:
            {
                "status": "success" | "partial_success" | "failed",
                "company_name": str,
                "phases": List[Dict],  # Phase results
                "errors": List[str],   # Any errors encountered
                "warnings": List[str], # Any warnings
                "duration_seconds": float,
                "request_id": str,
            }
        """
        logger.info(f"Starting research for {company_name} ({url})")

        # Create company profile with country and industry enrichment (BUG-049, BUG-050)
        company = CompanyProfile(
            name=company_name,
            website=url,
            industry=industry,
        ).with_enriched_context()

        if company.country != "Global":
            logger.info(f"Detected country from URL: {company.country}")
        if company.industry and not industry:
            logger.info(f"Inferred industry from domain: {company.industry}")

        # Initialize HTML cache with company name for saving scraped content
        html_cache = get_html_cache()
        html_cache.set_company(company_name)

        # Create context
        ctx = create_context(timeout_seconds=self._config.timeout_seconds)

        try:
            # Execute pipeline
            result = await self._pipeline.research(
                company=company,
                ctx=ctx,
                extra_context=extra_context,
            )

            # Save HTML cache index after research completes
            try:
                html_cache.save_index()
            except Exception as cache_err:
                logger.debug(f"HTML cache index save error (non-fatal): {cache_err}")

            # Convert to dictionary format for backward compatibility
            if result.is_success and result.output:
                output = result.output
                return {
                    "status": "success",
                    "company_name": company_name,
                    "website": url,
                    "phases": [
                        {
                            "phase_name": phase.phase_name,
                            "markdown_content": phase.markdown_content,
                            "sources": [
                                {
                                    "title": s.title,
                                    "url": s.url,
                                    "source_type": s.source_type,
                                }
                                for s in phase.sources
                            ],
                            "errors": phase.errors,
                            "warnings": phase.warnings,
                        }
                        for phase in output.phases
                    ],
                    "errors": output.errors,
                    "warnings": output.warnings,
                    "duration_seconds": result.duration_seconds,
                    "request_id": result.request_id,
                }

            elif result.status == PipelineStatus.PARTIAL_SUCCESS and result.output:
                output = result.output
                return {
                    "status": "partial_success",
                    "company_name": company_name,
                    "website": url,
                    "phases": [
                        {
                            "phase_name": phase.phase_name,
                            "markdown_content": phase.markdown_content,
                            "sources": [
                                {
                                    "title": s.title,
                                    "url": s.url,
                                    "source_type": s.source_type,
                                }
                                for s in phase.sources
                            ],
                            "errors": phase.errors,
                            "warnings": phase.warnings,
                        }
                        for phase in output.phases
                    ],
                    "errors": output.errors + ([str(result.error)] if result.error else []),
                    "warnings": output.warnings,
                    "failed_stage": result.failed_stage,
                    "duration_seconds": result.duration_seconds,
                    "request_id": result.request_id,
                }

            else:
                return {
                    "status": "failed",
                    "company_name": company_name,
                    "website": url,
                    "phases": [],
                    "errors": [str(result.error)] if result.error else ["Unknown error"],
                    "warnings": [],
                    "failed_stage": result.failed_stage,
                    "duration_seconds": result.duration_seconds,
                    "request_id": result.request_id,
                }

        except KeyboardInterrupt:
            logger.info("Research interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Error during research execution: {e}", exc_info=True)
            return {
                "status": "failed",
                "company_name": company_name,
                "website": url,
                "phases": [],
                "errors": [str(e)],
                "warnings": [],
                "request_id": ctx.request_id,
            }

    async def research_single_phase(
        self,
        company_name: str,
        url: str,
        research_type: str,
        industry: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct a single type of research.

        Args:
            company_name: Name of the company
            url: Company website URL
            research_type: Type of research (market, financial, competitor, brand, sales)
            industry: Company's industry (optional)

        Returns:
            Dictionary with single phase result
        """
        company = CompanyProfile(
            name=company_name,
            website=url,
            industry=industry,
        )

        ctx = create_context(timeout_seconds=self._config.timeout_seconds / 2)

        result = await self._pipeline.research_single(
            company=company,
            research_type=research_type,
            ctx=ctx,
        )

        if result.is_success and result.output and result.output.phases:
            phase = result.output.phases[0]
            return {
                "status": "success",
                "phase_name": phase.phase_name,
                "markdown_content": phase.markdown_content,
                "sources": [asdict(s) for s in phase.sources],
                "request_id": result.request_id,
            }
        else:
            return {
                "status": "failed",
                "error": str(result.error) if result.error else "Unknown error",
                "request_id": result.request_id,
            }


# =============================================================================
# Singleton Pattern (for backward compatibility)
# =============================================================================

_orchestrator: Optional[PipelineOrchestrator] = None
_orchestrator_lock = threading.Lock()


def get_pipeline_orchestrator(
    research_types: Optional[List[str]] = None,
    parallel: bool = True,
    timeout_seconds: float = 600.0,
) -> PipelineOrchestrator:
    """
    Get or create the singleton orchestrator instance (thread-safe).

    Note: Once created, the orchestrator configuration is fixed.
    To use different settings, create a new instance directly.

    Args:
        research_types: Which research types to perform
        parallel: Run phases in parallel
        timeout_seconds: Total timeout for research

    Returns:
        PipelineOrchestrator instance
    """
    global _orchestrator
    with _orchestrator_lock:
        if _orchestrator is None:
            _orchestrator = PipelineOrchestrator(
                research_types=research_types,
                parallel=parallel,
                timeout_seconds=timeout_seconds,
            )
        return _orchestrator


def reset_pipeline_orchestrator() -> None:
    """Reset the singleton orchestrator (useful for testing)."""
    global _orchestrator
    with _orchestrator_lock:
        _orchestrator = None


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PipelineOrchestrator",
    "get_pipeline_orchestrator",
    "reset_pipeline_orchestrator",
]
