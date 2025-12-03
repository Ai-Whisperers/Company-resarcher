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
from ..tools.github_tool import GitHubTool, GitHubPresence
from ..tools.opencorporates_tool import OpenCorporatesTool, CorporateRegistryData
from ..tools.whois_tool import WhoisTool, DomainAnalysis

from .context import create_context
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

    async def research_github_presence(
        self,
        company_name: str,
    ) -> Dict[str, Any]:
        """
        Analyze company's GitHub presence for tech stack insights.

        This is an optional enhancement that provides:
        - Tech stack discovery (languages, frameworks)
        - Engineering team activity metrics
        - Open source project analysis

        Args:
            company_name: Name of the company to analyze

        Returns:
            Dictionary with GitHub analysis results:
            {
                "status": "success" | "not_found" | "unavailable",
                "organization": dict | None,
                "tech_stack": dict | None,
                "activity": dict | None,
                "markdown_report": str,
            }
        """
        github = GitHubTool()

        if not github.is_available():
            logger.info("GitHub API not configured, skipping tech stack analysis")
            return {
                "status": "unavailable",
                "message": "GitHub API token not configured",
                "organization": None,
                "tech_stack": None,
                "activity": None,
                "markdown_report": "",
            }

        try:
            presence = await github.get_github_presence(company_name)

            if not presence.found:
                logger.info(f"No GitHub organization found for {company_name}")
                return {
                    "status": "not_found",
                    "message": f"No GitHub organization found for {company_name}",
                    "organization": None,
                    "tech_stack": None,
                    "activity": None,
                    "markdown_report": github.format_for_research(presence),
                }

            # Build result dictionary
            org_dict = None
            if presence.org:
                org_dict = {
                    "name": presence.org.name,
                    "login": presence.org.login,
                    "description": presence.org.description,
                    "public_repos": presence.org.public_repos,
                    "followers": presence.org.followers,
                    "location": presence.org.location,
                    "blog": presence.org.blog,
                    "html_url": presence.org.html_url,
                }

            tech_dict = None
            if presence.tech_stack:
                tech_dict = {
                    "primary_languages": presence.tech_stack.primary_languages,
                    "frameworks": presence.tech_stack.frameworks,
                    "topics": presence.tech_stack.topics,
                    "total_repos": presence.tech_stack.total_repos,
                    "total_stars": presence.tech_stack.total_stars,
                    "active_repos": presence.tech_stack.active_repos,
                }

            activity_dict = None
            if presence.activity:
                activity_dict = {
                    "repos_updated": presence.activity.repos_updated,
                    "repos_created": presence.activity.repos_created,
                    "most_active": presence.activity.most_active,
                    "period_days": presence.activity.period_days,
                }

            logger.info(
                f"GitHub analysis complete for {company_name}: "
                f"{presence.tech_stack.total_repos if presence.tech_stack else 0} repos, "
                f"{len(presence.tech_stack.primary_languages) if presence.tech_stack else 0} languages"
            )

            return {
                "status": "success",
                "organization": org_dict,
                "tech_stack": tech_dict,
                "activity": activity_dict,
                "markdown_report": github.format_for_research(presence),
            }

        except Exception as e:
            logger.error(f"GitHub analysis failed for {company_name}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "organization": None,
                "tech_stack": None,
                "activity": None,
                "markdown_report": f"## GitHub Presence\n\n*Error: {e}*\n",
            }
        finally:
            await github.close()

    async def research_corporate_registry(
        self,
        company_name: str,
        country: Optional[str] = None,
        website: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Research company's corporate registry and domain ownership.

        This provides:
        - Official registration data from OpenCorporates
        - Officers and directors
        - Domain ownership via WHOIS

        Args:
            company_name: Name of the company
            country: Country for jurisdiction-specific search
            website: Company website for domain lookup

        Returns:
            Dictionary with corporate registry results:
            {
                "status": "success" | "partial" | "not_found",
                "registration": dict | None,
                "officers": list | None,
                "domain": dict | None,
                "markdown_report": str,
            }
        """
        results: Dict[str, Any] = {
            "status": "not_found",
            "registration": None,
            "officers": None,
            "domain": None,
            "markdown_report": "",
        }

        markdown_parts = []

        # OpenCorporates lookup
        try:
            oc = OpenCorporatesTool()
            registry_data = await oc.get_full_company_data(company_name, country)

            if registry_data.found and registry_data.company:
                company = registry_data.company
                results["registration"] = {
                    "name": company.name,
                    "company_number": company.company_number,
                    "jurisdiction": company.jurisdiction_code,
                    "status": company.status,
                    "incorporation_date": company.incorporation_date,
                    "registered_address": company.registered_address,
                    "opencorporates_url": company.opencorporates_url,
                }
                results["officers"] = [
                    {
                        "name": o.name,
                        "position": o.position,
                        "start_date": o.start_date,
                    }
                    for o in registry_data.officers
                ]
                results["status"] = "success"
                markdown_parts.append(oc.format_for_research(registry_data))
                logger.info(
                    f"Corporate registry found for {company_name}: "
                    f"{company.jurisdiction_code}/{company.company_number}"
                )
            else:
                logger.info(f"No corporate registry data found for {company_name}")
                markdown_parts.append("## Corporate Registry\n\n*No registry data found.*\n")

            await oc.close()

        except Exception as e:
            logger.error(f"OpenCorporates lookup failed: {e}")
            markdown_parts.append(f"## Corporate Registry\n\n*Error: {e}*\n")

        # WHOIS lookup
        if website:
            try:
                whois = WhoisTool()

                if whois.is_available():
                    domain_analysis = await whois.analyze_domain(website)

                    if domain_analysis.found and domain_analysis.info:
                        info = domain_analysis.info
                        results["domain"] = {
                            "domain_name": info.domain_name,
                            "registrar": info.registrar,
                            "creation_date": info.creation_date.isoformat() if info.creation_date else None,
                            "expiration_date": info.expiration_date.isoformat() if info.expiration_date else None,
                            "registrant_organization": info.registrant_organization,
                            "registrant_country": info.registrant_country,
                            "age_years": domain_analysis.age_years,
                            "is_active": domain_analysis.is_active,
                        }
                        if results["status"] != "success":
                            results["status"] = "partial"
                        markdown_parts.append(whois.format_for_research(domain_analysis))
                        logger.info(
                            f"Domain info for {website}: age={domain_analysis.age_years}y, "
                            f"registrant={info.registrant_organization or 'private'}"
                        )
                    else:
                        markdown_parts.append("## Domain Ownership\n\n*No WHOIS data found.*\n")
                else:
                    logger.info("WHOIS API not configured, skipping domain lookup")
                    markdown_parts.append("## Domain Ownership\n\n*WHOIS API not configured.*\n")

                await whois.close()

            except Exception as e:
                logger.error(f"WHOIS lookup failed: {e}")
                markdown_parts.append(f"## Domain Ownership\n\n*Error: {e}*\n")

        results["markdown_report"] = "\n\n".join(markdown_parts)
        return results


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
