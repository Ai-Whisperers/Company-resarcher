#!/usr/bin/env python3
"""
Fix Existing Research - Reprocess sources and regenerate market consolidation.

This script:
1. Reprocesses raw sources to populate empty sections
2. Regenerates the market consolidation

Usage:
    python scripts/fix_existing_research.py --company COPACO --dry-run
    python scripts/fix_existing_research.py --all
    python scripts/fix_existing_research.py --consolidate-only
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.data import (
    SourceReprocessor,
    MarketConsolidator,
)
from src.services.data.reprocessor import format_reprocess_results
from src.core.logging.logger import setup_logger

logger = setup_logger("fix_research")


async def reprocess_companies(
    companies: list[str] | None = None,
    dry_run: bool = False,
    base_dir: str = "outputs",
) -> dict:
    """Reprocess sources for specified companies."""
    reprocessor = SourceReprocessor(base_dir)

    if companies:
        results = {}
        for company in companies:
            logger.info(f"Processing: {company}")
            results[company] = await reprocessor.reprocess_company(company, dry_run)
    else:
        logger.info("Processing all companies...")
        results = await reprocessor.reprocess_all_companies(dry_run=dry_run)

    # Print results
    report = format_reprocess_results(results)
    print("\n" + report)

    # Save report
    report_path = Path(base_dir) / "_reprocess_report.md"
    report_path.write_text(report, encoding="utf-8")
    logger.info(f"Report saved to: {report_path}")

    return results


async def regenerate_consolidation(
    market_name: str = "Paraguay Telecommunications",
    companies: list[str] | None = None,
    base_dir: str = "outputs",
):
    """Regenerate market consolidation."""
    if companies is None:
        # Default Paraguay telecom companies
        companies = [
            "Claro_Paraguay",
            "COPACO",
            "Personal_Paraguay",
            "Telecom_Argentina",
            "Tigo_Paraguay",
            "Vox_Paraguay",
        ]

    logger.info(f"Regenerating market consolidation: {market_name}")
    logger.info(f"Companies: {companies}")

    consolidator = MarketConsolidator(base_dir)

    try:
        output_dir = await consolidator.consolidate_market(
            market_name=market_name,
            company_folders=companies,
        )
        logger.info(f"Market consolidation complete: {output_dir}")
        return output_dir
    except Exception as e:
        logger.error(f"Market consolidation failed: {e}")
        raise


async def main():
    parser = argparse.ArgumentParser(description="Fix existing research data")
    parser.add_argument(
        "--company", "-c",
        action="append",
        help="Company to process (can be repeated)",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Process all companies",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Don't actually write files",
    )
    parser.add_argument(
        "--consolidate-only",
        action="store_true",
        help="Only regenerate market consolidation",
    )
    parser.add_argument(
        "--skip-consolidation",
        action="store_true",
        help="Skip market consolidation step",
    )
    parser.add_argument(
        "--base-dir",
        default="outputs",
        help="Base output directory",
    )

    args = parser.parse_args()

    # Determine companies to process
    if args.all:
        companies = None  # Will process all
    elif args.company:
        companies = args.company
    else:
        # Default to Paraguay telecom companies
        companies = [
            "Claro_Paraguay",
            "COPACO",
            "Personal_Paraguay",
            "Tigo_Paraguay",
        ]

    # Step 1: Reprocess sources (unless consolidate-only)
    if not args.consolidate_only:
        logger.info("=" * 60)
        logger.info("STEP 1: Reprocessing sources")
        logger.info("=" * 60)
        await reprocess_companies(companies, args.dry_run, args.base_dir)

    # Step 2: Regenerate consolidation (unless skip or dry-run)
    if not args.skip_consolidation and not args.dry_run:
        logger.info("=" * 60)
        logger.info("STEP 2: Regenerating market consolidation")
        logger.info("=" * 60)
        await regenerate_consolidation(base_dir=args.base_dir)

    logger.info("=" * 60)
    logger.info("COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
