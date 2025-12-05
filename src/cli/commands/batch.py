import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.logging import setup_logger
from src.lib.concurrency.checkpoint_manager import get_checkpoint_manager
from src.cli.handlers.profiles import load_batch_profiles
from src.cli.commands.research import run_profile_research, run_enriched_research
from src.cli.commands.consolidate import run_consolidate_market
from src.utils.cli import DryRunContext

logger = setup_logger("cli.commands.batch")


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
            logger.info(
                "No checkpoint found, detecting completed companies from outputs..."
            )
            checkpoint.initialize(
                all_profiles,
                config={"delay_between": delay_between, "parallel": parallel},
            )
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
        checkpoint.initialize(
            all_profiles, config={"delay_between": delay_between, "parallel": parallel}
        )

    print(f"\n{'='*60}")
    print(
        f"BATCH RESEARCH: {len(profiles)} companies"
        + (f" ({skipped_count} skipped)" if skipped_count else "")
    )
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
            print(
                f"     Focus: {', '.join(profile.get('research_focus', ['market', 'financial', 'competitor', 'brand', 'sales']))}"
            )
        print(f"\nTotal: {len(profiles)} companies")
        print(f"Delay between: {delay_between}s")
        print(f"Mode: {'parallel' if parallel else 'sequential'}")
        return {"dry_run": True, "companies": len(profiles)}

    # Generate batch ID for grouping in dashboard
    batch_id = str(uuid.uuid4())

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
            result = await run_profile_research(
                profile,
                parallel=parallel,
                batch_id=batch_id,
                batch_index=total_index,
                batch_total=len(all_profiles),
            )
            results[company_name] = {
                "status": result.get("status", "unknown"),
                "phases": len(result.get("phases", [])),
            }

            # Mark company as completed in checkpoint
            # Count output files for stats
            company_dir = Path("outputs") / company_name
            file_count = (
                len(list(company_dir.rglob("*.md"))) if company_dir.exists() else 0
            )
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
    print("\n" + "=" * 60)
    print("PHASE 1: INITIAL RESEARCH")
    print("=" * 60 + "\n")

    for i, profile in enumerate(profiles, 1):
        print(f"\n[{i}/{len(profiles)}] {profile['name']}")
        try:
            await run_profile_research(profile, parallel=parallel)
        except Exception as e:
            logger.error(f"Phase 1 failed for {profile['name']}: {e}")

        if i < len(profiles) and delay_between > 0:
            await asyncio.sleep(delay_between)

    # Phase 2: Enriched research
    print("\n" + "=" * 60)
    print("PHASE 2: CROSS-COMPANY ENRICHMENT")
    print("=" * 60 + "\n")

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
    print("\n" + "=" * 60)
    print("PHASE 3: MARKET CONSOLIDATION")
    print("=" * 60 + "\n")

    await run_consolidate_market(batch_path, None)

    print("\n" + "=" * 60)
    print("TWO-PHASE RESEARCH COMPLETE")
    print("=" * 60 + "\n")
