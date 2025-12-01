import asyncio
import argparse
import sys
import io
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from src.pipeline.orchestrator import PipelineOrchestrator
from src.core.logger import setup_logger
from src.core.output_manager import OutputManager
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
from src.core.types import CompanyProfile

# Fix Windows Unicode encoding issues (TECH-031)
if sys.platform == 'win32':
    # Force UTF-8 encoding for stdout/stderr to handle non-ASCII characters
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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
) -> Dict[str, Any]:
    """
    Run research for all companies in a market folder.

    Args:
        batch_path: Path to the market folder
        parallel: Whether to run phases in parallel (within each company)
        delay_between: Seconds to wait between companies

    Returns:
        Summary of all research results
    """
    profiles = load_batch_profiles(batch_path)

    if not profiles:
        logger.error(f"No profiles found in {batch_path}")
        return {"error": "No profiles found"}

    print(f"\n{'='*60}")
    print(f"BATCH RESEARCH: {len(profiles)} companies")
    print(f"{'='*60}")
    for i, p in enumerate(profiles, 1):
        print(f"  {i}. {p['name']} ({p.get('industry', 'N/A')})")
    print(f"{'='*60}\n")

    results = {}
    for i, profile in enumerate(profiles, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(profiles)}] Researching: {profile['name']}")
        print(f"{'='*60}\n")

        try:
            result = await run_profile_research(profile, parallel=parallel)
            results[profile["name"]] = {
                "status": result.get("status", "unknown"),
                "phases": len(result.get("phases", [])),
            }
        except Exception as e:
            logger.error(f"Research failed for {profile['name']}: {e}")
            results[profile["name"]] = {"status": "error", "error": str(e)}

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

    args = parser.parse_args()

    # Sequential flag overrides parallel
    parallel = not args.sequential

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

    # Mode 1: Batch research from folder
    if args.batch:
        logger.info(f"Running BATCH research from: {args.batch}")
        await run_batch_research(args.batch, parallel=parallel, delay_between=args.delay)
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
