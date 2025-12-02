# [RESOLVED] UX-001: Progress Bars for CLI

**Status**: RESOLVED
**Original File**: backlog/11-ux.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** CLI progress bars are essential for long-running tasks.

**Acceptance Criteria:**
- [x] Use `tqdm` or `rich.progress`
- [x] Show progress for: Search queries, Page scraping, Report generation

## Resolution

Comprehensive CLI progress tracking implemented using `rich` library.

### Implementation Details

**Files:**
- `src/utils/cli.py` - Rich-based CLI utilities (474 lines)
- `src/core/progress.py` - Progress tracking system (436 lines)

#### 1. Rich Progress Bars (`src/utils/cli.py`)

```python
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
    )

def create_phase_progress() -> Progress:
    """Create a progress bar for research phases."""
    return Progress(
        SpinnerColumn("dots"),
        TextColumn("[phase]{task.description}[/phase]"),
        BarColumn(bar_width=30, complete_style="magenta", finished_style="green"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    )

@contextmanager
def research_progress_context(total_companies: int, description: str = "Researching"):
    """Context manager for batch research progress tracking."""
    with create_research_progress() as progress:
        task = progress.add_task(f"[info]{description}[/info]", total=total_companies)
        yield progress, task
```

#### 2. Progress Tracking System (`src/core/progress.py`)

```python
class ResearchStage(str, Enum):
    INITIALIZING = "initializing"
    GENERATING_QUERIES = "generating_queries"
    SEARCHING = "searching"
    FETCHING_CONTENT = "fetching_content"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    WRITING = "writing"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class ResearchProgress:
    # Depth/breadth tracking for recursive research
    total_depth: int
    current_depth: int
    total_breadth: int
    current_breadth: int

    # Query/source tracking
    total_queries: int
    completed_queries: int
    total_sources: int
    processed_sources: int

    # Progress properties
    @property
    def overall_progress(self) -> float: ...
    @property
    def query_progress(self) -> float: ...
    @property
    def source_progress(self) -> float: ...
```

#### 3. Console Styling

Custom theme with consistent styling:
```python
THEME = Theme({
    "info": "cyan",
    "success": "green bold",
    "warning": "yellow",
    "error": "red bold",
    "company": "blue bold",
    "phase": "magenta",
    "metric": "cyan italic",
})
```

#### 4. Additional Features

- **Batch Results Summary** (CLI-005): Rich tables for batch results
- **Dry-Run Mode** (CLI-003): Preview operations without executing
- **Research Metrics** (MON-001): Timing and metrics tracking

### Usage Example

```python
from src.utils.cli import research_progress_context, print_company_header

# Batch research with progress
with research_progress_context(len(companies), "Researching companies") as (progress, task):
    for i, company in enumerate(companies, 1):
        print_company_header(company.name, i, len(companies))
        await research(company)
        progress.update(task, advance=1)
```

## Files

- `src/utils/cli.py` - CLI utilities with rich progress bars
- `src/core/progress.py` - Progress tracking system with callbacks
