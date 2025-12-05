import logging
from src.services.data import consolidate_from_batch

logger = logging.getLogger("cli.commands.consolidate")


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
