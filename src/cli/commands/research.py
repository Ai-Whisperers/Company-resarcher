import logging
from typing import Any, Optional
from pathlib import Path

from src.pipeline.orchestrator import PipelineOrchestrator
from src.core.logging import setup_logger
from src.lib.output.output_manager import OutputManager
from src.services.data import (
    get_source_tracker,
    reset_source_tracker,
    get_cross_company_reader,
    get_financial_data_service,
)
from src.core.types.base import CompanyProfile, ResearchSource
from src.lib.tracking.cli_run_registry import get_cli_run_registry
from src.core.logging.progress import get_progress_tracker
from src.cli.handlers.progress import create_cli_progress_callback
from src.cli.handlers.logging import CLILogHandler

logger = setup_logger("cli.commands.research")

# Maps old phase names to primary output section and file
PHASE_TO_OUTPUT: dict[str, tuple[str, str]] = {
    "market": ("01-Market-Intelligence", "01-Market-Size-Growth.md"),
    "financial": ("06-Data-Room", "01-Financials.md"),
    "competitor": ("03-Competitive-Landscape", "01-Competitor-List.md"),
    "brand": ("04-Brand-Strategy", "01-Positioning.md"),
    "sales": ("08-Sales-Intelligence", "05-Sales-Strategy.md"),
}


def convert_phases_to_structured_output(
    phases: list[dict[str, Any]],
) -> dict[str, str]:
    """
    Convert research phases to structured folder output.

    Maps old flat file structure to new hierarchical structure:
    - market.md -> 01-Market-Intelligence/01-Market-Size-Growth.md
    - financial.md -> 06-Data-Room/01-Financials.md
    - etc.

    Also generates source tracking files.

    Args:
        phases: List of phase results from research

    Returns:
        Dictionary mapping relative paths to content
    """
    drafts = {}

    # Reset source tracker for new research
    reset_source_tracker()
    source_tracker = get_source_tracker()

    for phase in phases:
        phase_name = phase["phase_name"]
        content = phase["markdown_content"]
        sources = phase.get("sources", [])

        # Get output mapping
        if phase_name in PHASE_TO_OUTPUT:
            section, filename = PHASE_TO_OUTPUT[phase_name]
            output_path = f"{section}/{filename}"
        else:
            # Fallback for unknown phases
            output_path = f"99-Other/{phase_name}.md"

        drafts[output_path] = content

        # Track sources for this section
        for src_data in sources:
            source = ResearchSource(
                url=src_data.get("url", ""),
                title=src_data.get("title", "Unknown"),
                content="",  # Content not preserved in phase output
                source_type=src_data.get("source_type", "web"),
            )
            source_tracker.track_source(source, section)

    # Add source tracking files
    source_files = source_tracker.get_output_files()
    drafts.update(source_files)

    return drafts


async def run_standard_research(
    company_name: str,
    url: str,
    industry: str | None,
    parallel: bool,
) -> None:
    """Run standard 5-phase research."""
    orchestrator = PipelineOrchestrator(parallel=parallel)
    result = await orchestrator.conduct_research(company_name, url, industry=industry)
    print("\n--- RESEARCH COMPLETE ---")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Phases completed: {len(result.get('phases', []))}")

    if result.get("phases"):
        # Use OutputManager to save structured reports
        output_manager = OutputManager()

        # Convert phases to new structured folder format
        drafts = convert_phases_to_structured_output(
            phases=result["phases"],
        )

        output_manager.save_research_output(company_name, drafts)
        logger.info(f"Saved {len(drafts)} files to output directory")

        # Log the folder structure
        sections = set()
        for path in drafts.keys():
            if "/" in path:
                sections.add(path.split("/")[0])
        logger.info(
            f"Created {len(sections)} section folders: "
            f"{', '.join(sorted(sections))}"
        )
    else:
        logger.warning("No phases found in result!")
        if result.get("errors"):
            for error in result["errors"]:
                logger.error(f"Error: {error}")


async def run_profile_research(
    profile: dict[str, Any],
    parallel: bool = True,
    batch_id: Optional[str] = None,
    batch_index: Optional[int] = None,
    batch_total: Optional[int] = None,
) -> dict[str, Any]:
    """
    Run research using a loaded profile configuration.

    Args:
        profile: Company profile dictionary from YAML
        parallel: Whether to run phases in parallel
        batch_id: Optional batch ID for grouped runs
        batch_index: Position in batch (1-indexed)
        batch_total: Total companies in batch

    Returns:
        Research result dictionary
    """
    company_name = profile["name"]
    url = profile.get("website", "")
    industry = profile.get("industry")
    country = profile.get("country", "Global")
    research_types = profile.get(
        "research_focus",
        ["market", "financial", "competitor", "brand", "sales"],
    )

    # Register with CLI run registry for dashboard visibility
    registry = get_cli_run_registry()
    run_id = registry.register_run(
        company_name=company_name,
        website=url,
        industry=industry,
        country=country,
        research_types=research_types,
        batch_id=batch_id,
        batch_index=batch_index,
        batch_total=batch_total,
    )

    # Register progress callback for dashboard live updates
    progress_tracker = get_progress_tracker()
    progress_callback = create_cli_progress_callback(run_id, registry)
    progress_tracker.register_callback(progress_callback)

    # Add log handler for dashboard log streaming
    log_handler = CLILogHandler(run_id, registry)
    log_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)

    logger.info(f"Starting research for {company_name}")
    logger.info(f"  Website: {url}")
    logger.info(f"  Industry: {industry}")
    logger.info(f"  Country: {country}")

    try:
        orchestrator = PipelineOrchestrator(parallel=parallel)
        result = await orchestrator.conduct_research(
            company_name, url, industry=industry
        )

        if result.get("phases"):
            output_manager = OutputManager()
            drafts = convert_phases_to_structured_output(phases=result["phases"])
            output_manager.save_research_output(company_name, drafts)
            logger.info(f"Saved {len(drafts)} files for {company_name}")

        # Mark run as completed
        registry.complete_run(run_id, success=result.get("status") == "completed")

    except Exception as e:
        # Mark run as failed
        registry.complete_run(run_id, success=False, error=str(e))
        raise
    finally:
        # Unregister the callback and remove log handler
        progress_tracker.unregister_callback(progress_callback)
        root_logger.removeHandler(log_handler)

    if not result.get("phases"):
        logger.warning(f"No phases completed for {company_name}")

    return result


async def run_enriched_research(
    profile: dict[str, Any],
    related_companies: list[str],
    parallel: bool = True,
) -> dict[str, Any]:
    """
    Run research with cross-company enrichment (Phase 2).

    Loads cached HTML from related companies to provide additional context.
    """
    company_name = profile["name"]
    url = profile.get("website", "")
    industry = profile.get("industry")

    logger.info(f"Starting ENRICHED research for {company_name}")
    logger.info(f"Cross-referencing {len(related_companies)} related companies")

    # Load cross-company context
    cross_reader = get_cross_company_reader()
    competitor_caches = cross_reader.load_market_cache(
        company_names=related_companies,
        exclude_company=company_name,
    )

    # Build enrichment context
    enrichment_context = ""
    if competitor_caches:
        enrichment_context = cross_reader.get_competitor_context(
            competitor_caches,
            company_name,
        )
        logger.info(f"Built enrichment context: {len(enrichment_context)} chars")

    # Create orchestrator with enrichment context
    orchestrator = PipelineOrchestrator(parallel=parallel)
    result = await orchestrator.conduct_research(
        company_name,
        url,
        industry=industry,
        extra_context=(
            {"cross_company_data": enrichment_context} if enrichment_context else None
        ),
    )

    if result.get("phases"):
        output_manager = OutputManager()
        drafts = convert_phases_to_structured_output(phases=result["phases"])

        # Add enrichment note
        enrichment_note = f"""# Cross-Company Enrichment

This research was enriched with data from {len(competitor_caches)} related companies:
{chr(10).join(f'- {c.company_name} ({c.file_count} sources)' 
              for c in competitor_caches)}

Total cross-referenced sources: {sum(c.file_count for c in competitor_caches)}
"""
        drafts["99-Sources/enrichment-context.md"] = enrichment_note

        output_manager.save_research_output(company_name, drafts)
        logger.info(f"Saved enriched research for {company_name}")

    return result


async def run_comprehensive_research(
    company_name: str,
    url: str,
    industry: str | None,
    ticker: str | None = None,
    exchange: str | None = None,
    parent_ticker: str | None = None,
    parent_company: str | None = None,
) -> None:
    """
    Run comprehensive research with 200+ queries and 1000+ sources.

    This mode generates all 52+ output files across all 10 sections.
    If ticker info is provided, also fetches financial data from Alpha Vantage.
    """
    from src.pipeline.comprehensive_research import (
        ComprehensiveResearchService,
        ContentGenerator,
    )
    from src.tools import get_shared_search_tool, get_shared_browser_tool
    from src.infrastructure.ai.ai_client import get_ai_manager

    # Get shared tools
    search_tool = get_shared_search_tool()
    browser_tool = get_shared_browser_tool()
    ai_client = get_ai_manager()

    # Create company profile with ticker info (INT-002)
    company = CompanyProfile(
        name=company_name,
        website=url,
        industry=industry or "General",
        country="Global",
        ticker=ticker,
        exchange=exchange,
        parent_ticker=parent_ticker,
        parent_company=parent_company,
    )

    # Initialize comprehensive research service
    research_service = ComprehensiveResearchService(
        search_tool=search_tool,
        browser_tool=browser_tool,
        ai_client=ai_client,
    )

    print("\n--- STARTING COMPREHENSIVE RESEARCH ---")
    print(f"Company: {company_name}")
    print(f"Industry: {industry or 'Not specified'}")
    if company.has_financial_data_available():
        print(f"Ticker: {company.get_effective_ticker()}")
    print("Executing 200+ queries across 10 sections...")

    # Execute comprehensive research
    result = await research_service.research_all_sections(company)

    print("\n--- RESEARCH PHASE COMPLETE ---")
    print(f"Total sources collected: {result.total_sources}")
    print(f"Total queries executed: {result.total_queries}")
    print(f"Duration: {result.duration_seconds:.1f} seconds")

    # Generate content for all files
    print("\n--- GENERATING OUTPUT FILES ---")
    content_generator = ContentGenerator(ai_client=ai_client)
    drafts = await content_generator.generate_all_files(result)

    # INT-002: Fetch financial data from Alpha Vantage if ticker available
    if company.has_financial_data_available():
        try:
            financial_service = get_financial_data_service()
            if financial_service.is_available():
                print(
                    f"\n--- FETCHING FINANCIAL DATA ({company.get_effective_ticker()}) ---"
                )
                financial_result = await financial_service.fetch_financial_data(company)
                if financial_result and financial_result.has_data:
                    import tempfile

                    with tempfile.TemporaryDirectory() as tmpdir:
                        reports = await financial_service.generate_reports(
                            financial_result, Path(tmpdir)
                        )
                        for report_name, report_path in reports.items():
                            content = report_path.read_text(encoding="utf-8")
                            drafts[
                                f"06-Data-Room/financial_data/{report_path.name}"
                            ] = content
                    print(f"Financial data: {len(reports)} reports generated")
                    if financial_result.is_parent_data:
                        print(
                            f"  (Data from parent company: "
                            f"{financial_result.parent_name})"
                        )
                else:
                    print(
                        f"Financial data: No data available for "
                        f"{company.get_effective_ticker()}"
                    )
        except Exception as fin_err:
            logger.warning(f"Financial data fetch failed: {fin_err}")

    # Save output
    output_manager = OutputManager()
    output_manager.save_research_output(company_name, drafts)

    # Log the folder structure
    sections = set()
    for path in drafts.keys():
        if "/" in path:
            sections.add(path.split("/")[0])

    print("\n--- COMPREHENSIVE RESEARCH COMPLETE ---")
    print(f"Generated {len(drafts)} files")
    print(f"Across {len(sections)} section folders: {', '.join(sorted(sections))}")
    logger.info(f"Saved {len(drafts)} files to output directory")
