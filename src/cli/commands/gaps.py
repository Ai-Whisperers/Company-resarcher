import logging
from pathlib import Path
from src.services.research import (
    GapAnalyzer,
    generate_gap_report,
    fill_market_gaps,
)
from src.cli.handlers.profiles import load_batch_profiles
from src.cli.commands.consolidate import run_consolidate_market

logger = logging.getLogger("cli.commands.gaps")


async def run_gap_analysis(batch_path: str) -> None:
    """Run gap analysis for a batch of companies."""
    logger.info(f"Analyzing gaps for: {batch_path}")
    profiles = load_batch_profiles(batch_path)
    company_names = [p["name"] for p in profiles]

    analyzer = GapAnalyzer()
    results = analyzer.analyze_market(company_names)

    # Generate and save report
    report = generate_gap_report(results)
    report_path = Path(batch_path) / "_gap_analysis.md"
    report_path.write_text(report, encoding="utf-8")

    # Print summary
    total_gaps = sum(r.total_gaps for r in results.values())
    print(f"\n{'='*60}")
    print("GAP ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Total gaps found: {total_gaps}")
    print(f"Report saved to: {report_path}")
    for company, result in results.items():
        print(
            f"  {company}: {result.total_gaps} gaps ({result.fillable_from_cross_reference} cross-referenceable)"
        )
    print(f"{'='*60}\n")


async def run_gap_filling(
    batch_path: str, max_iterations: int = 5, market_name: str | None = None
) -> None:
    """Iteratively fill gaps in research data."""
    logger.info(f"Filling gaps for: {batch_path}")
    print(f"\n{'='*60}")
    print("ITERATIVE GAP FILLING")
    print(f"Max iterations: {max_iterations}")
    print(f"{'='*60}\n")

    results = await fill_market_gaps(batch_path, max_iterations=max_iterations)

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
    # Note: This path check is a bit specific, might want to make it more generic or remove it
    # For now keeping it to match original logic but making it safer
    market_folder = Path("outputs") / "Paraguay Telecommunications"
    if market_folder.exists():
        print("Re-running consolidation with filled data...")
        await run_consolidate_market(batch_path, market_name)
