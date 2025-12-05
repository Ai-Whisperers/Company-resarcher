# FE-011: Structured Logging and Diagnostics

## Priority: MEDIUM
## Category: Feature Enhancement/DevOps
## Status: Backlog
## Created: 2025-11-28

## Summary

Implement structured logging with JSON format and research run diagnostics to make debugging, monitoring, and analysis easier.

## Problem Statement

Current logging challenges:
1. Logs are unstructured text, hard to parse/search
2. No aggregate metrics per research run
3. Difficult to identify root causes of failures
4. No way to compare runs over time
5. Hard to measure improvement after fixes

## Proposed Solution

### 1. Structured JSON Logging

```python
# src/core/logger.py

import json
import logging
from datetime import datetime
from typing import Any, Dict

class StructuredFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, 'research_id'):
            log_data['research_id'] = record.research_id
        if hasattr(record, 'phase'):
            log_data['phase'] = record.phase
        if hasattr(record, 'company'):
            log_data['company'] = record.company
        if hasattr(record, 'metrics'):
            log_data['metrics'] = record.metrics

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_structured_logger(name: str, research_id: str = None) -> logging.Logger:
    """Get a logger with structured output."""
    logger = logging.getLogger(name)

    if research_id:
        logger = logging.LoggerAdapter(logger, {'research_id': research_id})

    return logger
```

### 2. Research Run Diagnostics

```python
# src/core/diagnostics.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

@dataclass
class PhaseMetrics:
    """Metrics for a single research phase."""
    phase_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    queries_executed: int = 0
    results_found: int = 0
    sources_fetched: int = 0
    sources_usable: int = 0
    sources_filtered: int = 0
    ai_calls: int = 0
    ai_tokens_used: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        if self.sources_fetched == 0:
            return 0.0
        return self.sources_usable / self.sources_fetched


@dataclass
class ResearchDiagnostics:
    """Complete diagnostics for a research run."""
    research_id: str
    company_name: str
    company_url: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, success, failed, partial

    # Aggregate metrics
    total_queries: int = 0
    total_results: int = 0
    total_sources_fetched: int = 0
    total_sources_usable: int = 0
    total_ai_calls: int = 0
    total_ai_tokens: int = 0

    # Per-phase metrics
    phases: Dict[str, PhaseMetrics] = field(default_factory=dict)

    # Error tracking
    errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)

    # Search provider stats
    search_provider_used: str = ""
    search_fallbacks: int = 0

    def add_phase(self, phase: PhaseMetrics):
        self.phases[phase.phase_name] = phase
        self.total_queries += phase.queries_executed
        self.total_results += phase.results_found
        self.total_sources_fetched += phase.sources_fetched
        self.total_sources_usable += phase.sources_usable
        self.total_ai_calls += phase.ai_calls
        self.total_ai_tokens += phase.ai_tokens_used

    def add_error(self, phase: str, error_type: str, message: str, details: dict = None):
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase,
            "type": error_type,
            "message": message,
            "details": details or {}
        })

    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def overall_success_rate(self) -> float:
        if self.total_sources_fetched == 0:
            return 0.0
        return self.total_sources_usable / self.total_sources_fetched

    def to_summary(self) -> Dict:
        """Generate a summary for logging/display."""
        return {
            "research_id": self.research_id,
            "company": self.company_name,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "phases_completed": len([p for p in self.phases.values() if p.end_time]),
            "total_queries": self.total_queries,
            "total_sources": self.total_sources_fetched,
            "usable_sources": self.total_sources_usable,
            "success_rate": f"{self.overall_success_rate:.1%}",
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "ai_tokens": self.total_ai_tokens,
        }

    def to_json(self) -> str:
        """Export full diagnostics as JSON."""
        return json.dumps({
            **self.to_summary(),
            "phases": {
                name: {
                    "duration": p.duration_seconds,
                    "queries": p.queries_executed,
                    "sources_fetched": p.sources_fetched,
                    "sources_usable": p.sources_usable,
                    "success_rate": f"{p.success_rate:.1%}",
                    "errors": p.errors,
                }
                for name, p in self.phases.items()
            },
            "errors": self.errors,
            "warnings": self.warnings,
        }, indent=2)

    def save(self, output_dir: str):
        """Save diagnostics to file."""
        filepath = f"{output_dir}/diagnostics.json"
        with open(filepath, 'w') as f:
            f.write(self.to_json())
```

### 3. Integration with Pipeline

```python
# src/pipeline/orchestrator.py

class ResearchOrchestrator:
    async def conduct_research(self, company_name: str, url: str):
        research_id = generate_research_id()

        # Initialize diagnostics
        diagnostics = ResearchDiagnostics(
            research_id=research_id,
            company_name=company_name,
            company_url=url,
            start_time=datetime.utcnow()
        )

        logger = get_structured_logger("orchestrator", research_id)

        try:
            for phase_name in self.phases:
                phase_metrics = PhaseMetrics(
                    phase_name=phase_name,
                    start_time=datetime.utcnow()
                )

                try:
                    result = await self._run_phase(phase_name, diagnostics, phase_metrics)
                except Exception as e:
                    diagnostics.add_error(phase_name, type(e).__name__, str(e))
                    phase_metrics.errors.append(str(e))

                phase_metrics.end_time = datetime.utcnow()
                diagnostics.add_phase(phase_metrics)

            diagnostics.status = "success"

        except Exception as e:
            diagnostics.status = "failed"
            diagnostics.add_error("orchestrator", type(e).__name__, str(e))

        finally:
            diagnostics.end_time = datetime.utcnow()

            # Log summary
            logger.info("Research completed", extra={"metrics": diagnostics.to_summary()})

            # Save diagnostics
            diagnostics.save(self.output_dir)

        return diagnostics
```

### 4. CLI Summary Output

```python
# At end of research run:

def print_diagnostics_summary(diagnostics: ResearchDiagnostics):
    """Print human-readable summary to console."""
    print("\n" + "="*60)
    print("RESEARCH RUN SUMMARY")
    print("="*60)
    print(f"Company: {diagnostics.company_name}")
    print(f"Status: {diagnostics.status.upper()}")
    print(f"Duration: {diagnostics.duration_seconds:.1f}s")
    print()
    print("METRICS:")
    print(f"  Total Queries: {diagnostics.total_queries}")
    print(f"  Sources Fetched: {diagnostics.total_sources_fetched}")
    print(f"  Sources Usable: {diagnostics.total_sources_usable}")
    print(f"  Success Rate: {diagnostics.overall_success_rate:.1%}")
    print(f"  AI Tokens Used: {diagnostics.total_ai_tokens:,}")
    print()
    print("PHASES:")
    for name, phase in diagnostics.phases.items():
        status = "OK" if not phase.errors else f"ERRORS({len(phase.errors)})"
        print(f"  {name}: {phase.duration_seconds:.1f}s - {phase.sources_usable}/{phase.sources_fetched} sources - {status}")

    if diagnostics.errors:
        print()
        print(f"ERRORS ({len(diagnostics.errors)}):")
        for err in diagnostics.errors[:5]:  # Show first 5
            print(f"  [{err['phase']}] {err['type']}: {err['message'][:50]}")

    print("="*60)
```

## Expected Output

```
============================================================
RESEARCH RUN SUMMARY
============================================================
Company: Personal Paraguay
Status: SUCCESS
Duration: 92.3s

METRICS:
  Total Queries: 20
  Sources Fetched: 45
  Sources Usable: 12
  Success Rate: 26.7%
  AI Tokens Used: 15,432

PHASES:
  market: 27.4s - 2/12 sources - OK
  financial: 8.3s - 3/9 sources - ERRORS(1)
  competitor: 18.2s - 3/8 sources - OK
  brand: 22.1s - 2/10 sources - OK
  sales: 16.3s - 2/6 sources - ERRORS(1)

ERRORS (2):
  [financial] ValidationError: source_type must be one of...
  [sales] TemplateError: 'company' is undefined
============================================================
```

## Acceptance Criteria

- [ ] Logs are structured JSON when LOG_FORMAT=json
- [ ] diagnostics.json saved with each research run
- [ ] Summary printed at end of research
- [ ] Per-phase metrics tracked
- [ ] Error aggregation and reporting
- [ ] Easy to compare runs over time

## Files to Create/Modify

- New: `src/core/diagnostics.py`
- Modify: `src/core/logger.py` - Add structured formatter
- Modify: `src/pipeline/orchestrator.py` - Track diagnostics
- Modify: `main.py` - Print summary

## Related Issues

- All bugs - easier to debug with better logging
- Performance tracking for optimization
