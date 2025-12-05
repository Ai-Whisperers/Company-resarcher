import asyncio
import logging
from pathlib import Path

# CRITICAL: Load .env with override=True BEFORE any pydantic settings imports
from dotenv import load_dotenv

_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)


async def main():
    from src.cli.parser import create_parser

    parser = create_parser()
    args = parser.parse_args()

    # Imports moved here to speed up CLI startup (especially for --help)
    from src.core.logging import setup_logger, set_global_log_level
    from src.cli.handlers.profiles import load_company_profile, load_batch_profiles
    from src.cli.output.formatters import print_header, DryRunContext, DryRunConfig

    logger = setup_logger("cli.app")

    # Lazy imports to speed up CLI startup
    from src.cli.commands.research import (
        run_comprehensive_research,
        run_profile_research,
        run_enriched_research,
        run_full_market_research,
    )
    from src.cli.commands.batch import run_batch_research, run_two_phase_batch
    from src.cli.commands.consolidate import run_consolidate_market
    from src.cli.commands.gaps import run_gap_analysis, run_gap_filling
    from src.cli.commands.incremental import (
        run_incremental_batch_mode,
        run_incremental_profile_mode,
        run_incremental_name_mode,
    )
    from src.cli.commands.status import run_status_command
    from src.cli.commands.checkpoint import (
        resume_research_command,
        list_checkpoints_command,
        checkpoint_stats_command,
        cleanup_checkpoints_command,
        delete_thread_command,
    )

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

    # ==========================================================================
    # CHECKPOINT MANAGEMENT COMMANDS
    # ==========================================================================

    # Resume from checkpoint
    if args.resume_checkpoint:
        await resume_research_command(
            thread_id=args.resume_checkpoint,
            human_feedback=args.human_feedback,
        )
        return

    # List checkpoints
    if args.list_checkpoints:
        list_checkpoints_command(limit=50)
        return

    # Checkpoint statistics
    if args.checkpoint_stats:
        checkpoint_stats_command()
        return

    # Cleanup old checkpoints
    if args.cleanup_checkpoints:
        cleanup_checkpoints_command(max_age_days=args.cleanup_checkpoints)
        return

    # Delete specific checkpoint thread
    if args.delete_checkpoint:
        delete_thread_command(thread_id=args.delete_checkpoint)
        return

    # ==========================================================================
    # RESEARCH COMMANDS
    # ==========================================================================

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
        await run_comprehensive_research(
            company_name,
            url,
            industry,
            ticker=profile.get("ticker"),
            exchange=profile.get("exchange"),
            parent_ticker=profile.get("parent_ticker"),
            parent_company=profile.get("parent_company"),
        )
        return

    # Mode FULL with CLI args: Comprehensive research
    if args.full and args.name:
        logger.info(f"Running FULL comprehensive research for: {args.name}")
        await run_comprehensive_research(args.name, args.url or "", args.industry)
        return

    # Mode 0: Two-phase research (full workflow)
    if args.two_phase and args.batch:
        logger.info(f"Running TWO-PHASE research from: {args.batch}")
        await run_two_phase_batch(
            args.batch, parallel=parallel, delay_between=args.delay
        )
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
        await run_gap_analysis(args.batch)
        return

    # Mode 0e: Fill gaps iteratively
    if args.fill_gaps and args.batch:
        await run_gap_filling(
            args.batch, max_iterations=args.max_iterations, market_name=args.market_name
        )
        return

    # ==========================================================================
    # INCREMENTAL RESEARCH MODE - Smart deduplication across runs
    # ==========================================================================

    # Mode: Show research status
    if args.status:
        run_status_command(
            batch_path=args.batch,
            profile_path=args.profile,
            company_name=args.name,
        )
        return

    # Mode: Incremental research for batch
    if args.incremental and args.batch:
        await run_incremental_batch_mode(args.batch, max_queries=args.max_queries)
        return

    # Mode: Incremental research for single company (profile)
    if args.incremental and args.profile:
        await run_incremental_profile_mode(args.profile, max_queries=args.max_queries)
        return

    # Mode: Incremental research for single company (CLI args)
    if args.incremental and args.name:
        await run_incremental_name_mode(
            args.name, args.industry, max_queries=args.max_queries
        )
        return

    # Mode 1: Batch research from folder
    if args.batch:
        logger.info(f"Running BATCH research from: {args.batch}")
        # Setup dry-run context if requested (CLI-003)
        dry_run = None
        if args.dry_run:
            dry_run = DryRunContext(DryRunConfig(enabled=True))
            print_header("Dry-Run Mode", "Showing planned operations without executing")
        await run_batch_research(
            args.batch,
            parallel=parallel,
            delay_between=args.delay,
            dry_run=dry_run,
            resume=args.resume,
        )
        return

    # Mode 2: Single company from profile
    if args.profile:
        logger.info(f"Running research from profile: {args.profile}")
        profile = load_company_profile(args.profile)
        await run_profile_research(profile, parallel=parallel)
        return

    # Mode 3: Single company from CLI args
    if args.name:
        logger.info(f"Running research for: {args.name}")
        # Create temporary profile
        profile = {
            "name": args.name,
            "website": args.url or "",
            "industry": args.industry,
            "country": "Global",
            "research_focus": ["market", "financial", "competitor", "brand", "sales"],
        }
        await run_profile_research(profile, parallel=parallel)
        return

    # No arguments provided
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
