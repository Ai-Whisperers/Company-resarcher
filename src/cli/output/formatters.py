"""
CLI output formatters and utilities.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom theme for consistent styling
THEME = Theme(
    {
        "info": "cyan",
        "success": "green bold",
        "warning": "yellow",
        "error": "red bold",
        "company": "blue bold",
        "phase": "magenta",
        "metric": "cyan italic",
    }
)

# Global console instance with custom theme
console = Console(theme=THEME)

T = TypeVar("T")


# =============================================================================
# Data Classes for Results
# =============================================================================


@dataclass
class PhaseResult:
    """Result of a single research phase."""

    name: str
    status: str  # "completed", "failed", "skipped"
    duration_seconds: float = 0.0
    sources_found: int = 0
    error_message: str | None = None


@dataclass
class CompanyResult:
    """Result of research for a single company."""

    name: str
    status: str  # "completed", "failed", "partial"
    duration_seconds: float = 0.0
    phases: list[PhaseResult] = field(default_factory=list)
    total_sources: int = 0
    error_message: str | None = None

    @property
    def phases_completed(self) -> int:
        return sum(1 for p in self.phases if p.status == "completed")

    @property
    def phases_failed(self) -> int:
        return sum(1 for p in self.phases if p.status == "failed")


@dataclass
class BatchResult:
    """Aggregated results for a batch research run."""

    companies: list[CompanyResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0

    @property
    def total_companies(self) -> int:
        return len(self.companies)

    @property
    def successful(self) -> int:
        return sum(1 for c in self.companies if c.status == "completed")

    @property
    def failed(self) -> int:
        return sum(1 for c in self.companies if c.status == "failed")

    @property
    def total_sources(self) -> int:
        return sum(c.total_sources for c in self.companies)


# =============================================================================
# Progress Bar Utilities
# =============================================================================


def create_research_progress() -> Progress:
    """Create a styled progress bar for research operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=False,
    )


def create_phase_progress() -> Progress:
    """Create a progress bar for research phases."""
    return Progress(
        SpinnerColumn("dots"),
        TextColumn("[phase]{task.description}[/phase]"),
        BarColumn(bar_width=30, complete_style="magenta", finished_style="green"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        expand=False,
    )


@contextmanager
def research_progress_context(total_companies: int, description: str = "Researching"):
    """Context manager for batch research progress tracking."""
    with create_research_progress() as progress:
        task = progress.add_task(f"[info]{description}[/info]", total=total_companies)
        yield progress, task


# =============================================================================
# Console Output Utilities
# =============================================================================


def print_header(title: str, subtitle: str | None = None) -> None:
    """Print a styled header panel."""
    content = Text(title, style="bold white")
    if subtitle:
        content.append(f"\n{subtitle}", style="dim")
    console.print(Panel(content, border_style="blue", padding=(1, 2)))


def print_company_header(company_name: str, index: int, total: int) -> None:
    """Print header for a company research section."""
    console.print()
    console.rule(f"[company]{company_name}[/company] [{index}/{total}]", style="blue")
    console.print()


def print_phase_status(
    phase_name: str, status: str, duration: float | None = None
) -> None:
    """Print the status of a research phase."""
    status_icons = {
        "completed": "[success]OK[/success]",
        "failed": "[error]FAIL[/error]",
        "skipped": "[warning]SKIP[/warning]",
        "running": "[info]...[/info]",
    }
    icon = status_icons.get(status, "[dim]?[/dim]")

    msg = f"  {icon} [phase]{phase_name}[/phase]"
    if duration is not None:
        msg += f" [metric]({duration:.1f}s)[/metric]"

    console.print(msg)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success]{message}[/success]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]{message}[/warning]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[error]{message}[/error]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[info]{message}[/info]")


# =============================================================================
# Batch Results Summary (CLI-005)
# =============================================================================


def print_batch_summary(result: BatchResult) -> None:
    """Print a rich summary table for batch research results."""
    console.print()
    console.rule("[bold]Batch Research Summary[/bold]", style="green")
    console.print()

    # Summary metrics
    metrics_table = Table(show_header=False, box=None, padding=(0, 2))
    metrics_table.add_column("Metric", style="dim")
    metrics_table.add_column("Value", style="bold")

    metrics_table.add_row("Total Companies", str(result.total_companies))
    metrics_table.add_row("Successful", f"[green]{result.successful}[/green]")
    metrics_table.add_row(
        "Failed", f"[red]{result.failed}[/red]" if result.failed > 0 else "0"
    )
    metrics_table.add_row("Total Sources", str(result.total_sources))
    metrics_table.add_row("Total Duration", f"{result.total_duration_seconds:.1f}s")

    console.print(Panel(metrics_table, title="Overview", border_style="blue"))
    console.print()

    # Detailed company results table
    table = Table(title="Company Results", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Company", style="company")
    table.add_column("Status", justify="center")
    table.add_column("Phases", justify="center")
    table.add_column("Sources", justify="right")
    table.add_column("Duration", justify="right", style="metric")

    for i, company in enumerate(result.companies, 1):
        status_style = {
            "completed": "[green]OK[/green]",
            "failed": "[red]FAIL[/red]",
            "partial": "[yellow]PARTIAL[/yellow]",
        }.get(company.status, company.status)

        phases_str = f"{company.phases_completed}/{len(company.phases)}"
        if company.phases_failed > 0:
            phases_str += f" [red]({company.phases_failed} failed)[/red]"

        table.add_row(
            str(i),
            company.name,
            status_style,
            phases_str,
            str(company.total_sources),
            f"{company.duration_seconds:.1f}s",
        )

    console.print(table)
    console.print()


def print_simple_batch_summary(results: dict[str, dict[str, Any]]) -> None:
    """Print a simple batch summary from dict results (legacy format)."""
    console.print()
    console.rule("[bold]Batch Research Complete[/bold]", style="green")
    console.print()

    table = Table(show_lines=False)
    table.add_column("Status", justify="center", width=8)
    table.add_column("Company", style="company")
    table.add_column("Phases", justify="right")

    for name, r in results.items():
        status = r.get("status", "unknown")
        status_str = "[green]OK[/green]" if status == "completed" else "[red]FAIL[/red]"
        phases = r.get("phases", 0)

        table.add_row(status_str, name, str(phases))

    console.print(table)
    console.print()


# =============================================================================
# Dry-Run Mode (CLI-003)
# =============================================================================


@dataclass
class DryRunConfig:
    """Configuration for dry-run mode."""

    enabled: bool = False
    verbose: bool = True


class DryRunContext:
    """Context for dry-run operations."""

    def __init__(self, config: DryRunConfig | None = None):
        self.config = config or DryRunConfig()
        self.operations: list[dict[str, Any]] = []

    def would_execute(
        self, operation: str, details: dict[str, Any] | None = None
    ) -> None:
        """Record an operation that would be executed."""
        op = {"operation": operation, "details": details or {}}
        self.operations.append(op)

        if self.config.verbose:
            console.print(
                f"[dim][DRY-RUN][/dim] Would execute: [info]{operation}[/info]"
            )
            if details:
                for k, v in details.items():
                    console.print(f"  [dim]{k}:[/dim] {v}")

    def print_summary(self) -> None:
        """Print summary of operations that would have been executed."""
        console.print()
        console.rule("[bold]Dry-Run Summary[/bold]", style="yellow")
        console.print()

        if not self.operations:
            console.print("[dim]No operations would be executed.[/dim]")
            return

        table = Table(title="Planned Operations", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Operation", style="info")
        table.add_column("Details")

        for i, op in enumerate(self.operations, 1):
            details_str = ", ".join(f"{k}={v}" for k, v in op["details"].items())
            table.add_row(str(i), op["operation"], details_str or "-")

        console.print(table)
        console.print()
        console.print(f"[warning]Total operations: {len(self.operations)}[/warning]")
        console.print("[dim]Run without --dry-run to execute these operations.[/dim]")


def dry_run_decorator(
    operation_name: str,
    get_details: Callable[..., dict[str, Any]] | None = None,
):
    """Decorator to make a function respect dry-run mode."""

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        def wrapper(*args, dry_run: DryRunContext | None = None, **kwargs) -> T | None:
            if dry_run and dry_run.config.enabled:
                details = get_details(*args, **kwargs) if get_details else {}
                dry_run.would_execute(operation_name, details)
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Research Timing Utilities (MON-001)
# =============================================================================


@dataclass
class ResearchMetrics:
    """Metrics collected during research."""

    start_time: float = 0.0
    end_time: float = 0.0
    phase_durations: dict[str, float] = field(default_factory=dict)
    source_counts: dict[str, int] = field(default_factory=dict)
    query_counts: dict[str, int] = field(default_factory=dict)

    @property
    def total_duration(self) -> float:
        return self.end_time - self.start_time if self.end_time else 0.0

    @property
    def total_sources(self) -> int:
        return sum(self.source_counts.values())

    @property
    def total_queries(self) -> int:
        return sum(self.query_counts.values())


@contextmanager
def timed_operation(name: str, metrics: ResearchMetrics | None = None):
    """Context manager for timing operations."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        if metrics:
            metrics.phase_durations[name] = duration
        console.print(f"  [metric]{name}: {duration:.2f}s[/metric]")


def print_research_metrics(metrics: ResearchMetrics) -> None:
    """Print research metrics summary."""
    console.print()
    console.rule("[bold]Research Metrics[/bold]", style="cyan")
    console.print()

    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Total Duration", f"{metrics.total_duration:.1f}s")
    table.add_row("Total Sources", str(metrics.total_sources))
    table.add_row("Total Queries", str(metrics.total_queries))

    console.print(Panel(table, title="Summary", border_style="cyan"))

    if metrics.phase_durations:
        console.print()
        phase_table = Table(title="Phase Durations")
        phase_table.add_column("Phase", style="phase")
        phase_table.add_column("Duration", justify="right", style="metric")
        phase_table.add_column("Sources", justify="right")
        phase_table.add_column("Queries", justify="right")

        for phase, duration in metrics.phase_durations.items():
            sources = metrics.source_counts.get(phase, 0)
            queries = metrics.query_counts.get(phase, 0)
            phase_table.add_row(phase, f"{duration:.2f}s", str(sources), str(queries))

        console.print(phase_table)

    console.print()
