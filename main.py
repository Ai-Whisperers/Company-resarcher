import asyncio
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# CRITICAL: Load .env with override=True BEFORE any pydantic settings imports
# This ensures .env values take precedence over system environment variables
from dotenv import load_dotenv
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)

import yaml

from src.pipeline.orchestrator import PipelineOrchestrator
from src.core.logger import setup_logger, set_global_log_level
import logging
from src.core.output_manager import OutputManager
from src.utils.cli import (
    console,
    print_header,
    print_company_header,
    print_success,
    print_warning,
    print_error,
    print_info,
    print_simple_batch_summary,
    create_research_progress,
    DryRunConfig,
    DryRunContext,
)
from src.core.output_structure import (
    OutputSection,
    OUTPUT_STRUCTURE,
    RESEARCH_TYPE_SECTIONS,
    get_output_path,
)
from src.services.source_tracker import get_source_tracker, reset_source_tracker
from src.services.cross_company_reader import get_cross_company_reader
from src.services.market_consolidation import MarketConsolidator, consolidate_from_batch
from src.services.gap_analyzer import GapAnalyzer, generate_gap_report
from src.services.iterative_research import IterativeResearchService, fill_market_gaps
from src.services.incremental_research import (
    IncrementalResearchService,
    run_incremental_research,
    run_incremental_batch,
    print_incremental_report,
)
from src.services.existing_data_analyzer import get_data_analyzer
from src.services.persistent_source_registry import get_source_registry
from src.core.types import CompanyProfile
from src.core.checkpoint_manager import CheckpointManager, get_checkpoint_manager

# Note: Windows Unicode encoding is handled by src.core.logger module
# via _configure_windows_encoding() and SafeStreamHandler (CRITICAL-001)

logger = setup_logger("main")


# =============================================================================
# YAML Profile Loading
# =============================================================================


def load_company_profile(profile_path: str) -> Dict[str, Any]:
    """
    Load a company profile from a YAML file.

    Args:
        profile_path: Path to the YAML profile file

    Returns:
        Dictionary with company configuration
    """
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Extract company info from nested structure
    company = data.get("company", data)

    return {
        "name": company.get("name", path.stem),
        "website": company.get("website", ""),
        "industry": company.get("industry", ""),
        "country": company.get("country", "Global"),
        "research_focus": data.get("research", {}).get("focus_areas", [
            "market", "financial", "competitor", "brand", "sales"
        ]),
        "priority_queries": data.get("research", {}).get("priority_queries", []),
        "notes": data.get("notes", ""),
    }


def load_batch_profiles(batch_path: str) -> List[Dict[str, Any]]:
    """
    Load all company profiles from a market folder.

    Args:
        batch_path: Path to the market folder containing YAML files

    Returns:
        List of company configurations
    """
    path = Path(batch_path)
    if not path.exists():
        raise FileNotFoundError(f"Batch folder not found: {batch_path}")

    profiles = []

    # Load all YAML files except _market.yaml (market config)
    for yaml_file in sorted(path.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue  # Skip market config files

        try:
            profile = load_company_profile(str(yaml_file))
            profile["_source_file"] = str(yaml_file)
            profiles.append(profile)
            logger.info(f"Loaded profile: {profile['name']}")
        except Exception as e:
            logger.warning(f"Failed to load {yaml_file}: {e}")

    return profiles


# =============================================================================
# Research Phase to Section Mapping
# =============================================================================

# Maps old phase names to primary output section and file
PHASE_TO_OUTPUT: Dict[str, tuple[str, str]] = {
    "market": ("01-Market-Intelligence", "01-Market-Size-Growth.md"),
    "financial": ("06-Data-Room", "01-Financials.md"),
    "competitor": ("03-Competitive-Landscape", "01-Competitor-List.md"),
    "brand": ("04-Brand-Strategy", "01-Positioning.md"),
    "sales": ("08-Sales-Intelligence", "05-Sales-Strategy.md"),
}


def convert_phases_to_structured_output(
    phases: List[Dict[str, Any]],
) -> Dict[str, str]:
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
        from src.core.types import ResearchSource
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
        logger.info(f"Created {len(sections)} section folders: {', '.join(sorted(sections))}")
    else:
        logger.warning("No phases found in result!")
        if result.get("errors"):
            for error in result["errors"]:
                logger.error(f"Error: {error}")


async def run_profile_research(
    profile: Dict[str, Any],
    parallel: bool = True,
) -> Dict[str, Any]:
    """
    Run research using a loaded profile configuration.

    Args:
        profile: Company profile dictionary from YAML
        parallel: Whether to run phases in parallel

    Returns:
        Research result dictionary
    """
    company_name = profile["name"]
    url = profile.get("website", "")
    industry = profile.get("industry")
    country = profile.get("country", "Global")

    logger.info(f"Starting research for {company_name}")
    logger.info(f"  Website: {url}")
    logger.info(f"  Industry: {industry}")
    logger.info(f"  Country: {country}")

    orchestrator = PipelineOrchestrator(parallel=parallel)
    result = await orchestrator.conduct_research(
        company_name, url, industry=industry
    )

    if result.get("phases"):
        output_manager = OutputManager()
        drafts = convert_phases_to_structured_output(phases=result["phases"])
        output_manager.save_research_output(company_name, drafts)
        logger.info(f"Saved {len(drafts)} files for {company_name}")
    else:
        logger.warning(f"No phases completed for {company_name}")

    return result


async def run_batch_research(
    batch_path: str,
    parallel: bool = True,
    delay_between: int = 5,
    dry_run: Optional["DryRunContext"] = None,
    resume: bool = False,
) -> Dict[str, Any]:
    """
    Run research for all companies in a market folder.

    Args:
        batch_path: Path to the market folder
        parallel: Whether to run phases in parallel (within each company)
        delay_between: Seconds to wait between companies
        dry_run: Optional dry-run context for simulating execution
        resume: If True, skip companies already completed (checkpoint/resume)

    Returns:
        Summary of all research results
    """
    all_profiles = load_batch_profiles(batch_path)

    if not all_profiles:
        logger.error(f"No profiles found in {batch_path}")
        return {"error": "No profiles found"}

    # Initialize checkpoint manager
    checkpoint = get_checkpoint_manager(batch_path)

    # Handle resume mode
    profiles = all_profiles
    skipped_count = 0

    if resume:
        # Try to load existing checkpoint
        if checkpoint.exists():
            checkpoint.load()
            logger.info("Loaded existing checkpoint for resume")
        else:
            # No checkpoint file, but --resume was passed
            # Sync from outputs directory to detect already-completed companies
            logger.info("No checkpoint found, detecting completed companies from outputs...")
            checkpoint.initialize(all_profiles, config={"delay_between": delay_between, "parallel": parallel})
            checkpoint.sync_from_outputs(all_profiles)

        # Filter to pending companies only
        profiles = checkpoint.get_pending_companies(all_profiles)
        skipped_count = len(all_profiles) - len(profiles)

        if skipped_count > 0:
            print(f"\n{'='*60}")
            print(f"RESUME MODE: Skipping {skipped_count} completed companies")
            print(f"{'='*60}")
            stats = checkpoint.get_stats()
            print(f"  Completed: {stats.get('completed', 0)}")
            print(f"  Remaining: {len(profiles)}")
            print(f"{'='*60}\n")

        if not profiles:
            print("All companies already completed! Nothing to do.")
            return {"status": "all_complete", "skipped": skipped_count}
    else:
        # Fresh start - initialize new checkpoint
        checkpoint.initialize(all_profiles, config={"delay_between": delay_between, "parallel": parallel})

    print(f"\n{'='*60}")
    print(f"BATCH RESEARCH: {len(profiles)} companies" + (f" ({skipped_count} skipped)" if skipped_count else ""))
    print(f"{'='*60}")
    for i, p in enumerate(profiles, 1):
        print(f"  {i}. {p['name']} ({p.get('industry', 'N/A')})")
    print(f"{'='*60}\n")

    # Dry-run mode: show what would be executed without running
    if dry_run:
        print("DRY-RUN: Would execute the following research:")
        for i, profile in enumerate(profiles, 1):
            print(f"  {i}. {profile['name']}")
            print(f"     Website: {profile.get('website', 'N/A')}")
            print(f"     Industry: {profile.get('industry', 'N/A')}")
            print(f"     Focus: {', '.join(profile.get('research_focus', ['market', 'financial', 'competitor', 'brand', 'sales']))}")
        print(f"\nTotal: {len(profiles)} companies")
        print(f"Delay between: {delay_between}s")
        print(f"Mode: {'parallel' if parallel else 'sequential'}")
        return {"dry_run": True, "companies": len(profiles)}

    results = {}
    for i, profile in enumerate(profiles, 1):
        company_name = profile["name"]
        total_index = skipped_count + i  # Adjust index for display

        print(f"\n{'='*60}")
        print(f"[{total_index}/{len(all_profiles)}] Researching: {company_name}")
        print(f"{'='*60}\n")

        # Mark company as started in checkpoint
        checkpoint.mark_company_started(company_name)

        try:
            result = await run_profile_research(profile, parallel=parallel)
            results[company_name] = {
                "status": result.get("status", "unknown"),
                "phases": len(result.get("phases", [])),
            }

            # Mark company as completed in checkpoint
            # Count output files for stats
            company_dir = Path("outputs") / company_name
            file_count = len(list(company_dir.rglob("*.md"))) if company_dir.exists() else 0
            checkpoint.mark_company_completed(
                company_name,
                sources_count=result.get("total_sources", 0),
                files_generated=file_count,
            )

        except Exception as e:
            logger.error(f"Research failed for {company_name}: {e}")
            results[company_name] = {"status": "error", "error": str(e)}
            checkpoint.mark_company_error(company_name, str(e))

        # Delay between companies to avoid rate limiting
        if i < len(profiles) and delay_between > 0:
            logger.info(f"Waiting {delay_between}s before next company...")
            await asyncio.sleep(delay_between)

    # Print summary
    print(f"\n{'='*60}")
    print("BATCH RESEARCH COMPLETE")
    print(f"{'='*60}")
    for name, r in results.items():
        status = "OK" if r.get("status") == "completed" else "FAIL"
        phases = r.get("phases", 0)
        print(f"  [{status}] {name}: {phases} phases")

    # Show checkpoint summary
    final_stats = checkpoint.get_stats()
    print(f"\nCheckpoint Summary:")
    print(f"  Total companies: {final_stats.get('total_companies', 0)}")
    print(f"  Completed: {final_stats.get('completed', 0)}")
    print(f"  Errors: {final_stats.get('errors', 0)}")
    print(f"{'='*60}\n")

    return results


async def run_consolidate_market(batch_path: str, output_name: str | None) -> None:
    """
    Consolidate all company research into a single market report.

    This is Phase 2 of two-phase research - combines data from all companies.
    """
    print(f"\n{'='*60}")
    print("MARKET CONSOLIDATION")
    print(f"{'='*60}")
    print(f"Source: {batch_path}")
    print(f"Output: {output_name or 'auto-detected from _market.yaml'}")
    print(f"{'='*60}\n")

    try:
        output_dir = await consolidate_from_batch(batch_path, output_name)
        print(f"\n{'='*60}")
        print("CONSOLIDATION COMPLETE")
        print(f"Output folder: {output_dir}")
        print(f"{'='*60}\n")
    except Exception as e:
        logger.error(f"Consolidation failed: {e}")
        raise


async def run_enriched_research(
    profile: Dict[str, Any],
    related_companies: List[str],
    parallel: bool = True,
) -> Dict[str, Any]:
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
        extra_context={"cross_company_data": enrichment_context} if enrichment_context else None,
    )

    if result.get("phases"):
        output_manager = OutputManager()
        drafts = convert_phases_to_structured_output(phases=result["phases"])

        # Add enrichment note
        enrichment_note = f"""# Cross-Company Enrichment

This research was enriched with data from {len(competitor_caches)} related companies:
{chr(10).join(f'- {c.company_name} ({c.file_count} sources)' for c in competitor_caches)}

Total cross-referenced sources: {sum(c.file_count for c in competitor_caches)}
"""
        drafts["99-Sources/enrichment-context.md"] = enrichment_note

        output_manager.save_research_output(company_name, drafts)
        logger.info(f"Saved enriched research for {company_name}")

    return result


async def run_full_market_research(
    batch_path: str,
    delay_between: int = 5,
    max_gap_iterations: int = 5,
    resume: bool = False,
) -> None:
    """
    Run FULL market research workflow with all features enabled.

    This is the most comprehensive research mode:
    1. Comprehensive research for each company (200+ queries, 1000+ sources)
    2. Cross-company enrichment
    3. Gap analysis
    4. Iterative gap filling
    5. Market consolidation

    Args:
        batch_path: Path to the market folder
        delay_between: Seconds between companies
        max_gap_iterations: Maximum gap-filling iterations
        resume: If True, resume from checkpoint (skip already-completed companies)
    """
    from src.pipeline.comprehensive_research import (
        ComprehensiveResearchService,
        ContentGenerator,
    )
    from src.tools import get_shared_search_tool, get_shared_browser_tool
    from src.core.ai_client import get_ai_manager

    profiles = load_batch_profiles(batch_path)

    if not profiles:
        logger.error(f"No profiles found in {batch_path}")
        return

    # ========================================================================
    # CHECKPOINT/RESUME SETUP
    # ========================================================================
    checkpoint_mgr = get_checkpoint_manager(batch_path)
    all_profiles = profiles  # Keep original list for display

    if resume:
        # Try to load existing checkpoint
        if checkpoint_mgr.exists():
            checkpoint_mgr.load()
            stats = checkpoint_mgr.get_stats()
            print(f"\n📋 RESUME MODE: Found checkpoint")
            print(f"   Completed: {stats.get('completed', 0)}/{stats.get('total_companies', 0)}")
            print(f"   Errors: {stats.get('errors', 0)}")
        else:
            # No checkpoint file, sync from outputs (detect completed from files)
            print(f"\n📋 RESUME MODE: No checkpoint file, scanning outputs...")
            checkpoint_mgr.sync_from_outputs(profiles)
            stats = checkpoint_mgr.get_stats()
            print(f"   Detected completed: {stats.get('completed', 0)}/{stats.get('total_companies', 0)}")

        # Filter to pending companies
        profiles = checkpoint_mgr.get_pending_companies(profiles)

        if not profiles:
            print(f"\n✅ All companies already completed!")
            stats = checkpoint_mgr.get_stats()
            print(f"   Total sources: {stats.get('total_sources', 0)}")
            print(f"   Total files: {stats.get('total_files', 0)}")
            return
    else:
        # Fresh run - initialize new checkpoint
        checkpoint_mgr.initialize(profiles, config={"mode": "full_market_research"})

    print(f"\n{'='*70}")
    print("FULL MARKET RESEARCH WORKFLOW")
    print(f"{'='*70}")
    print(f"Companies: {len(profiles)}")
    print(f"Mode: Comprehensive (200+ queries per company)")
    print(f"Features: Enrichment + Gap Analysis + Gap Filling + Consolidation")
    print(f"{'='*70}")
    for i, p in enumerate(profiles, 1):
        print(f"  {i}. {p['name']} ({p.get('industry', 'N/A')})")
    print(f"{'='*70}\n")

    # Get shared tools
    search_tool = get_shared_search_tool()
    browser_tool = get_shared_browser_tool()
    ai_client = get_ai_manager()

    # ==========================================================================
    # PHASE 1: Comprehensive Research for Each Company
    # ==========================================================================
    print("\n" + "="*70)
    print("PHASE 1: COMPREHENSIVE RESEARCH (200+ queries per company)")
    print("="*70 + "\n")

    for i, profile in enumerate(profiles, 1):
        company_name = profile["name"]
        url = profile.get("website", "")
        industry = profile.get("industry")

        print(f"\n[{i}/{len(profiles)}] {company_name}")
        print(f"  Website: {url}")
        print(f"  Industry: {industry}")

        # Mark company as started in checkpoint
        checkpoint_mgr.mark_company_started(company_name)

        try:
            # Create company profile
            company = CompanyProfile(
                name=company_name,
                website=url,
                industry=industry or "General",
                country=profile.get("country", "Global"),
            )

            # Initialize comprehensive research service
            research_service = ComprehensiveResearchService(
                search_tool=search_tool,
                browser_tool=browser_tool,
                ai_client=ai_client,
            )

            # Execute comprehensive research
            result = await research_service.research_all_sections(company)

            print(f"  Sources collected: {result.total_sources}")
            print(f"  Queries executed: {result.total_queries}")
            print(f"  Duration: {result.duration_seconds:.1f}s")

            # Generate content for all files
            content_generator = ContentGenerator(ai_client=ai_client)
            drafts = await content_generator.generate_all_files(result)

            # Save output
            output_manager = OutputManager()
            output_manager.save_research_output(company_name, drafts)

            logger.info(f"Saved {len(drafts)} files for {company_name}")

            # Mark company as completed in checkpoint
            checkpoint_mgr.mark_company_completed(
                company_name,
                sources_count=result.total_sources,
                files_generated=len(drafts),
            )

        except Exception as e:
            logger.error(f"Comprehensive research failed for {company_name}: {e}")
            # Fall back to standard research
            print(f"  Falling back to standard research...")
            try:
                await run_profile_research(profile, parallel=True)
                # If fallback succeeds, still mark as completed (estimate files)
                checkpoint_mgr.mark_company_completed(company_name, sources_count=0, files_generated=40)
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                # Mark company as error in checkpoint
                checkpoint_mgr.mark_company_error(company_name, f"Comprehensive: {e}; Fallback: {e2}")

        if i < len(profiles) and delay_between > 0:
            print(f"  Waiting {delay_between}s before next company...")
            await asyncio.sleep(delay_between)

    # ==========================================================================
    # PHASE 2: Cross-Company Enrichment
    # ==========================================================================
    print("\n" + "="*70)
    print("PHASE 2: CROSS-COMPANY ENRICHMENT")
    print("="*70 + "\n")

    all_company_names = [p["name"] for p in profiles]

    for i, profile in enumerate(profiles, 1):
        print(f"\n[{i}/{len(profiles)}] Enriching: {profile['name']}")
        try:
            await run_enriched_research(
                profile,
                related_companies=all_company_names,
                parallel=True,
            )
        except Exception as e:
            logger.error(f"Enrichment failed for {profile['name']}: {e}")

        if i < len(profiles) and delay_between > 0:
            await asyncio.sleep(delay_between)

    # ==========================================================================
    # PHASE 3: Gap Analysis
    # ==========================================================================
    print("\n" + "="*70)
    print("PHASE 3: GAP ANALYSIS")
    print("="*70 + "\n")

    try:
        analyzer = GapAnalyzer()
        gap_results = analyzer.analyze_market(all_company_names)

        # Generate and save report
        report = generate_gap_report(gap_results)
        report_path = Path(batch_path) / "_gap_analysis.md"
        report_path.write_text(report, encoding="utf-8")

        total_gaps = sum(r.total_gaps for r in gap_results.values())
        print(f"Total gaps found: {total_gaps}")
        print(f"Report saved to: {report_path}")
        for company, result in gap_results.items():
            print(f"  {company}: {result.total_gaps} gaps")
    except Exception as e:
        logger.error(f"Gap analysis failed: {e}")

    # ==========================================================================
    # PHASE 4: Iterative Gap Filling
    # ==========================================================================
    print("\n" + "="*70)
    print(f"PHASE 4: ITERATIVE GAP FILLING (max {max_gap_iterations} iterations)")
    print("="*70 + "\n")

    try:
        fill_results = await fill_market_gaps(batch_path, max_iterations=max_gap_iterations)

        total_initial = sum(r.initial_gaps for r in fill_results.values())
        total_final = sum(r.final_gaps for r in fill_results.values())
        total_filled = sum(r.total_filled for r in fill_results.values())

        print(f"Gaps filled: {total_initial} -> {total_final} ({total_filled} filled)")
        for company, result in fill_results.items():
            status = "OK" if result.success else "PARTIAL"
            print(f"  [{status}] {company}: {result.initial_gaps} -> {result.final_gaps}")
    except Exception as e:
        logger.error(f"Gap filling failed: {e}")

    # ==========================================================================
    # PHASE 5: Market Consolidation
    # ==========================================================================
    print("\n" + "="*70)
    print("PHASE 5: MARKET CONSOLIDATION")
    print("="*70 + "\n")

    try:
        await run_consolidate_market(batch_path, None)
    except Exception as e:
        logger.error(f"Consolidation failed: {e}")

    # ==========================================================================
    # COMPLETE
    # ==========================================================================
    print("\n" + "="*70)
    print("FULL MARKET RESEARCH COMPLETE")
    print("="*70)
    print(f"Companies researched: {len(profiles)}")
    print(f"Output folder: outputs/")
    print("="*70 + "\n")


async def run_two_phase_batch(
    batch_path: str,
    parallel: bool = True,
    delay_between: int = 5,
) -> None:
    """
    Run full two-phase research workflow:
    1. Phase 1: Initial research for all companies (gathers data)
    2. Phase 2: Enriched research using cross-company data
    3. Market consolidation

    Args:
        batch_path: Path to the market folder
        parallel: Run phases in parallel
        delay_between: Seconds between companies
    """
    profiles = load_batch_profiles(batch_path)

    if not profiles:
        logger.error(f"No profiles found in {batch_path}")
        return

    print(f"\n{'='*60}")
    print("TWO-PHASE MARKET RESEARCH")
    print(f"{'='*60}")
    print(f"Phase 1: Initial research for {len(profiles)} companies")
    print("Phase 2: Cross-company enrichment")
    print("Phase 3: Market consolidation")
    print(f"{'='*60}\n")

    # Phase 1: Initial research
    print("\n" + "="*60)
    print("PHASE 1: INITIAL RESEARCH")
    print("="*60 + "\n")

    for i, profile in enumerate(profiles, 1):
        print(f"\n[{i}/{len(profiles)}] {profile['name']}")
        try:
            await run_profile_research(profile, parallel=parallel)
        except Exception as e:
            logger.error(f"Phase 1 failed for {profile['name']}: {e}")

        if i < len(profiles) and delay_between > 0:
            await asyncio.sleep(delay_between)

    # Phase 2: Enriched research
    print("\n" + "="*60)
    print("PHASE 2: CROSS-COMPANY ENRICHMENT")
    print("="*60 + "\n")

    # Get list of all company names for cross-reference
    all_company_names = [p["name"] for p in profiles]

    for i, profile in enumerate(profiles, 1):
        print(f"\n[{i}/{len(profiles)}] Enriching: {profile['name']}")
        try:
            await run_enriched_research(
                profile,
                related_companies=all_company_names,
                parallel=parallel,
            )
        except Exception as e:
            logger.error(f"Phase 2 failed for {profile['name']}: {e}")

        if i < len(profiles) and delay_between > 0:
            await asyncio.sleep(delay_between)

    # Phase 3: Market consolidation
    print("\n" + "="*60)
    print("PHASE 3: MARKET CONSOLIDATION")
    print("="*60 + "\n")

    await run_consolidate_market(batch_path, None)

    print("\n" + "="*60)
    print("TWO-PHASE RESEARCH COMPLETE")
    print("="*60 + "\n")


async def run_comprehensive_research(
    company_name: str,
    url: str,
    industry: str | None,
) -> None:
    """
    Run comprehensive research with 200+ queries and 1000+ sources.

    This mode generates all 52+ output files across all 10 sections.
    """
    from src.pipeline.comprehensive_research import (
        ComprehensiveResearchService,
        ContentGenerator,
    )
    from src.tools import get_shared_search_tool, get_shared_browser_tool
    from src.core.ai_client import get_ai_manager

    # Get shared tools
    search_tool = get_shared_search_tool()
    browser_tool = get_shared_browser_tool()
    ai_client = get_ai_manager()

    # Create company profile
    company = CompanyProfile(
        name=company_name,
        website=url,
        industry=industry or "General",
        country="Global",
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


async def main():
    parser = argparse.ArgumentParser(description="Company Researcher Agent")

    # Basic arguments
    parser.add_argument("--name", type=str, help="Company name to research")
    parser.add_argument("--url", type=str, help="Company website URL")
    parser.add_argument(
        "--industry",
        type=str,
        help="Company industry (e.g., 'telecommunications', 'retail'). "
             "If not provided, queries will use generic 'industry' placeholder.",
    )

    # Profile/Batch arguments
    parser.add_argument(
        "--profile",
        type=str,
        help="Path to a company YAML profile file (e.g., research_targets/paraguay_telecom/personal_paraguay.yaml)",
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="Path to a market folder to research all companies (e.g., research_targets/paraguay_telecom/)",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Seconds to wait between companies in batch mode (default: 5)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume batch research from checkpoint, skipping already-completed companies",
    )

    # Execution mode arguments
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Run research phases in parallel (default: True)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run research phases sequentially (slower but uses less resources)",
    )
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive research with 200+ queries, 1000+ sources, and 52+ output files",
    )

    # Two-phase research arguments
    parser.add_argument(
        "--two-phase",
        action="store_true",
        help="Run full two-phase research: initial + cross-company enrichment + market consolidation",
    )
    parser.add_argument(
        "--consolidate",
        action="store_true",
        help="Only run market consolidation (requires prior batch research)",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Only run Phase 2 enrichment (requires prior batch research)",
    )
    parser.add_argument(
        "--market-name",
        type=str,
        help="Name for consolidated market output (default: from _market.yaml)",
    )

    # Gap filling arguments
    parser.add_argument(
        "--fill-gaps",
        action="store_true",
        help="Iteratively research to fill all N/A values in research output",
    )
    parser.add_argument(
        "--analyze-gaps",
        action="store_true",
        help="Only analyze and report gaps without filling them",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum gap-filling iterations (default: 5)",
    )

    # Incremental research arguments (smart deduplication across runs)
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Run INCREMENTAL research: analyzes existing data, skips already-fetched URLs, "
             "and targets only missing data gaps. Best for subsequent runs on same company.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show research status for a company (completeness, gaps, sources count)",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=30,
        help="Maximum queries to run in incremental mode (default: 30)",
    )

    # CLI enhancement arguments (CLI-003)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running actual research",
    )

    # CLI-006: Verbose logging flag
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (-v for INFO, -vv for DEBUG)",
    )

    # Full workflow mode - comprehensive research with all features
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run FULL workflow: comprehensive research (200+ queries) + verbose logging + "
             "gap analysis + gap filling + enrichment + consolidation. "
             "This is the most thorough research mode available.",
    )

    args = parser.parse_args()

    # CLI-006: Handle verbose flag
    # --full mode automatically enables DEBUG logging
    if args.full or args.verbose >= 2:
        set_global_log_level(logging.DEBUG)
        logger.info("Verbose mode: DEBUG level enabled")
    elif args.verbose == 1:
        set_global_log_level(logging.INFO)
        logger.info("Verbose mode: INFO level enabled")

    # Sequential flag overrides parallel
    parallel = not args.sequential

    # Mode FULL: Complete market research with all features
    if args.full and args.batch:
        logger.info(f"Running FULL market research from: {args.batch}")
        await run_full_market_research(
            args.batch,
            delay_between=args.delay,
            max_gap_iterations=args.max_iterations,
            resume=args.resume,
        )
        return

    # Mode FULL with single profile: Comprehensive research for one company
    if args.full and args.profile:
        logger.info(f"Running FULL comprehensive research for: {args.profile}")
        profile = load_company_profile(args.profile)
        company_name = profile["name"]
        url = profile.get("website", "")
        industry = profile.get("industry")
        await run_comprehensive_research(company_name, url, industry)
        return

    # Mode FULL with CLI args: Comprehensive research
    if args.full and args.name:
        logger.info(f"Running FULL comprehensive research for: {args.name}")
        await run_comprehensive_research(args.name, args.url or "", args.industry)
        return

    # Mode 0: Two-phase research (full workflow)
    if args.two_phase and args.batch:
        logger.info(f"Running TWO-PHASE research from: {args.batch}")
        await run_two_phase_batch(args.batch, parallel=parallel, delay_between=args.delay)
        return

    # Mode 0b: Consolidate only (requires prior research)
    if args.consolidate and args.batch:
        logger.info(f"Running CONSOLIDATION for: {args.batch}")
        await run_consolidate_market(args.batch, args.market_name)
        return

    # Mode 0c: Enrich only (requires prior research)
    if args.enrich and args.batch:
        logger.info(f"Running ENRICHMENT for: {args.batch}")
        profiles = load_batch_profiles(args.batch)
        all_company_names = [p["name"] for p in profiles]
        for i, profile in enumerate(profiles, 1):
            print(f"\n[{i}/{len(profiles)}] Enriching: {profile['name']}")
            await run_enriched_research(profile, all_company_names, parallel=parallel)
            if i < len(profiles) and args.delay > 0:
                await asyncio.sleep(args.delay)
        return

    # Mode 0d: Analyze gaps only
    if args.analyze_gaps and args.batch:
        logger.info(f"Analyzing gaps for: {args.batch}")
        profiles = load_batch_profiles(args.batch)
        company_names = [p["name"] for p in profiles]

        analyzer = GapAnalyzer()
        results = analyzer.analyze_market(company_names)

        # Generate and save report
        report = generate_gap_report(results)
        report_path = Path(args.batch) / "_gap_analysis.md"
        report_path.write_text(report, encoding="utf-8")

        # Print summary
        total_gaps = sum(r.total_gaps for r in results.values())
        print(f"\n{'='*60}")
        print("GAP ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Total gaps found: {total_gaps}")
        print(f"Report saved to: {report_path}")
        for company, result in results.items():
            print(f"  {company}: {result.total_gaps} gaps ({result.fillable_from_cross_reference} cross-referenceable)")
        print(f"{'='*60}\n")
        return

    # Mode 0e: Fill gaps iteratively
    if args.fill_gaps and args.batch:
        logger.info(f"Filling gaps for: {args.batch}")
        print(f"\n{'='*60}")
        print("ITERATIVE GAP FILLING")
        print(f"Max iterations: {args.max_iterations}")
        print(f"{'='*60}\n")

        results = await fill_market_gaps(args.batch, max_iterations=args.max_iterations)

        # Print summary
        print(f"\n{'='*60}")
        print("GAP FILLING COMPLETE")
        print(f"{'='*60}")
        total_initial = sum(r.initial_gaps for r in results.values())
        total_final = sum(r.final_gaps for r in results.values())
        total_filled = sum(r.total_filled for r in results.values())
        print(f"Total gaps: {total_initial} -> {total_final} ({total_filled} filled)")
        for company, result in results.items():
            status = "OK" if result.success else "PARTIAL"
            print(f"  [{status}] {company}: {result.initial_gaps} -> {result.final_gaps}")
        print(f"{'='*60}\n")

        # Re-consolidate if consolidation exists
        market_folder = Path("outputs") / "Paraguay Telecommunications"
        if market_folder.exists():
            print("Re-running consolidation with filled data...")
            await run_consolidate_market(args.batch, args.market_name)

        return

    # ==========================================================================
    # INCREMENTAL RESEARCH MODE - Smart deduplication across runs
    # ==========================================================================

    # Mode: Show research status
    if args.status:
        if args.profile:
            profile = load_company_profile(args.profile)
            company_name = profile["name"]
        elif args.name:
            company_name = args.name
        elif args.batch:
            # Show status for all companies in batch
            profiles = load_batch_profiles(args.batch)
            print(f"\n{'='*70}")
            print("RESEARCH STATUS - ALL COMPANIES")
            print(f"{'='*70}\n")
            service = IncrementalResearchService()
            for profile in profiles:
                status = service.get_research_status(profile["name"])
                print(f"{profile['name']}:")
                print(f"  Completeness: {status['completeness']}")
                print(f"  Data gaps: {status['gaps_count']}")
                print(f"  Sources: {status['sources_count']} ({status['stale_sources']} stale)")
                if status['priority_gaps']:
                    print(f"  Priority gaps: {', '.join(status['priority_gaps'][:3])}")
                print()
            return
        else:
            print("Error: --status requires --profile, --name, or --batch")
            return

        # Show status for single company
        service = IncrementalResearchService()
        status = service.get_research_status(company_name)
        print(f"\n{'='*60}")
        print(f"RESEARCH STATUS: {company_name}")
        print(f"{'='*60}")
        print(f"Completeness: {status['completeness']}")
        print(f"Data gaps: {status['gaps_count']}")
        print(f"Sources tracked: {status['sources_count']}")
        print(f"Stale sources: {status['stale_sources']}")
        if status['last_research']:
            print(f"Last research: {status['last_research']}")
        if status['priority_gaps']:
            print(f"\nPriority gaps to fill:")
            for gap in status['priority_gaps']:
                print(f"  - {gap}")
        if status['data_types_found']:
            print(f"\nData types found: {', '.join(status['data_types_found'][:5])}")
        print(f"{'='*60}\n")
        return

    # Mode: Incremental research for batch
    if args.incremental and args.batch:
        logger.info(f"Running INCREMENTAL research for batch: {args.batch}")
        profiles = load_batch_profiles(args.batch)
        company_names = [p["name"] for p in profiles]

        # Load market config for industry
        industry = "telecommunications"
        market_yaml = Path(args.batch) / "_market.yaml"
        if market_yaml.exists():
            with open(market_yaml, "r", encoding="utf-8") as f:
                market_config = yaml.safe_load(f)
                industry = market_config.get("market", {}).get("industry", industry)
                country = market_config.get("market", {}).get("country", "Paraguay")
        else:
            country = profiles[0].get("country", "Paraguay") if profiles else "Paraguay"

        print(f"\n{'='*70}")
        print("INCREMENTAL RESEARCH MODE")
        print(f"{'='*70}")
        print(f"Companies: {len(profiles)}")
        print(f"Industry: {industry}")
        print(f"Max queries per company: {args.max_queries}")
        print(f"{'='*70}\n")

        results = await run_incremental_batch(
            company_names=company_names,
            industry=industry,
            country=country,
        )

        # Print summary
        print(f"\n{'='*70}")
        print("INCREMENTAL RESEARCH COMPLETE")
        print(f"{'='*70}")
        total_skipped_seen = sum(r.stats.urls_skipped_seen for r in results.values())
        total_skipped_similar = sum(r.stats.urls_skipped_similar for r in results.values())
        total_fetched = sum(r.stats.urls_fetched_new for r in results.values())
        total_filled = sum(r.stats.gaps_filled for r in results.values())
        print(f"URLs skipped (already seen): {total_skipped_seen}")
        print(f"URLs skipped (similar content): {total_skipped_similar}")
        print(f"New URLs fetched: {total_fetched}")
        print(f"Gaps filled: {total_filled}")
        print(f"\nPer-company results:")
        for company, result in results.items():
            efficiency = result.stats.to_dict()['efficiency_rate']
            print(f"  {company}: {result.stats.gaps_filled} gaps filled, {efficiency}")
        print(f"{'='*70}\n")
        return

    # Mode: Incremental research for single company (profile)
    if args.incremental and args.profile:
        profile = load_company_profile(args.profile)
        company_name = profile["name"]
        industry = profile.get("industry", "telecommunications")
        country = profile.get("country", "Paraguay")

        print(f"\n{'='*70}")
        print(f"INCREMENTAL RESEARCH: {company_name}")
        print(f"{'='*70}")
        print(f"Industry: {industry}")
        print(f"Country: {country}")
        print(f"Max queries: {args.max_queries}")
        print(f"{'='*70}\n")

        result = await run_incremental_research(
            company_name=company_name,
            industry=industry,
            country=country,
            max_queries=args.max_queries,
        )

        print_incremental_report(result)
        return

    # Mode: Incremental research for single company (CLI args)
    if args.incremental and args.name:
        print(f"\n{'='*70}")
        print(f"INCREMENTAL RESEARCH: {args.name}")
        print(f"{'='*70}")
        print(f"Industry: {args.industry or 'telecommunications'}")
        print(f"Max queries: {args.max_queries}")
        print(f"{'='*70}\n")

        result = await run_incremental_research(
            company_name=args.name,
            industry=args.industry or "telecommunications",
            max_queries=args.max_queries,
        )

        print_incremental_report(result)
        return

    # Mode 1: Batch research from folder
    if args.batch:
        logger.info(f"Running BATCH research from: {args.batch}")
        # Setup dry-run context if requested (CLI-003)
        dry_run = None
        if args.dry_run:
            dry_run = DryRunContext(DryRunConfig(enabled=True))
            print_header("Dry-Run Mode", "Showing planned operations without executing")
        await run_batch_research(args.batch, parallel=parallel, delay_between=args.delay, dry_run=dry_run, resume=args.resume)
        return

    # Mode 2: Single company from profile
    if args.profile:
        logger.info(f"Loading profile from: {args.profile}")
        profile = load_company_profile(args.profile)
        logger.info(f"Researching: {profile['name']} ({profile.get('industry', 'N/A')})")
        await run_profile_research(profile, parallel=parallel)
        return

    # Mode 3: Standard CLI arguments
    company_name = args.name or "Nestle"
    url = args.url or "https://www.nestle.com"
    industry = args.industry  # Optional, can be None (BUG-050)

    logger.info(f"Initializing research for {company_name} ({url})")
    if industry:
        logger.info(f"Industry: {industry}")

    # Check for comprehensive mode
    if args.comprehensive:
        logger.info("Running in COMPREHENSIVE mode (200+ queries, 1000+ sources)")
        await run_comprehensive_research(company_name, url, industry)
    else:
        logger.info(f"Running in {'PARALLEL' if parallel else 'SEQUENTIAL'} mode")
        await run_standard_research(company_name, url, industry, parallel)


if __name__ == "__main__":
    asyncio.run(main())
