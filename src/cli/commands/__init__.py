"""
CLI command implementations for various research modes.
"""

from src.cli.commands.research import (
    run_standard_research,
    run_profile_research,
    run_comprehensive_research,
)
from src.cli.commands.batch import (
    run_batch_research,
    run_two_phase_batch,
    run_full_market_research,
    run_enriched_research,
)
from src.cli.commands.gaps import (
    run_analyze_gaps,
    run_fill_gaps,
)
from src.cli.commands.consolidate import run_consolidate_market
from src.cli.commands.incremental import (
    run_incremental_research,
    run_incremental_batch,
    run_status_check,
)

__all__ = [
    # Research commands
    "run_standard_research",
    "run_profile_research",
    "run_comprehensive_research",
    # Batch commands
    "run_batch_research",
    "run_two_phase_batch",
    "run_full_market_research",
    "run_enriched_research",
    # Gap commands
    "run_analyze_gaps",
    "run_fill_gaps",
    # Consolidation
    "run_consolidate_market",
    # Incremental
    "run_incremental_research",
    "run_incremental_batch",
    "run_status_check",
]
