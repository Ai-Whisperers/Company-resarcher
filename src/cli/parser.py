import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
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
        "-v",
        "--verbose",
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

    # Checkpoint management arguments
    parser.add_argument(
        "--resume-checkpoint",
        type=str,
        metavar="THREAD_ID",
        help="Resume interrupted research from checkpoint thread ID",
    )
    parser.add_argument(
        "--list-checkpoints",
        action="store_true",
        help="List all available research checkpoints",
    )
    parser.add_argument(
        "--checkpoint-stats",
        action="store_true",
        help="Display checkpoint database statistics",
    )
    parser.add_argument(
        "--cleanup-checkpoints",
        type=int,
        metavar="DAYS",
        help="Clean up checkpoints older than specified days",
    )
    parser.add_argument(
        "--delete-checkpoint",
        type=str,
        metavar="THREAD_ID",
        help="Delete all checkpoints for a specific thread ID",
    )
    parser.add_argument(
        "--human-feedback",
        type=str,
        help="Provide human feedback when resuming from checkpoint (use with --resume-checkpoint)",
    )

    return parser
