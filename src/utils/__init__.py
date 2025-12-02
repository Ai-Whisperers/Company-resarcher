"""
Utility modules for the Company Researcher.
"""

from .url_utils import (
    extract_country_from_url,
    extract_country_tld,
    normalize_url,
    get_domain,
    is_same_site,
    add_country_context_to_query,
    COUNTRY_TLD_MAP,
)

from .cli import (
    console,
    print_header,
    print_company_header,
    print_phase_status,
    print_success,
    print_warning,
    print_error,
    print_info,
    create_research_progress,
    create_phase_progress,
    research_progress_context,
    PhaseResult,
    CompanyResult,
    BatchResult,
    print_batch_summary,
    print_simple_batch_summary,
    DryRunConfig,
    DryRunContext,
    dry_run_decorator,
    ResearchMetrics,
    timed_operation,
    print_research_metrics,
)

__all__ = [
    # URL utilities
    "extract_country_from_url",
    "extract_country_tld",
    "normalize_url",
    "get_domain",
    "is_same_site",
    "add_country_context_to_query",
    "COUNTRY_TLD_MAP",
    # CLI utilities
    "console",
    "print_header",
    "print_company_header",
    "print_phase_status",
    "print_success",
    "print_warning",
    "print_error",
    "print_info",
    "create_research_progress",
    "create_phase_progress",
    "research_progress_context",
    "PhaseResult",
    "CompanyResult",
    "BatchResult",
    "print_batch_summary",
    "print_simple_batch_summary",
    "DryRunConfig",
    "DryRunContext",
    "dry_run_decorator",
    "ResearchMetrics",
    "timed_operation",
    "print_research_metrics",
]
