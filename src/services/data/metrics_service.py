"""
Metrics Service for Research Operations.

Provides unified tracking and reporting for:
- MON-001: Research Duration Metrics
- MON-002: Source Success Rate Tracking
- MON-003: AI Token Usage (future)
- MON-004: Error Rate (future)

Usage:
    from src.services.metrics_service import get_metrics_service

    metrics = get_metrics_service()

    with metrics.track_operation("market_research"):
        # do research
        pass

    print(metrics.get_summary())
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...core.logging import setup_logger
from .source_tracker import get_source_tracker

logger = setup_logger("metrics")


@dataclass
class OperationMetric:
    """Metrics for a single operation."""

    name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Get operation duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def is_complete(self) -> bool:
        """Check if operation has completed."""
        return self.end_time is not None


@dataclass
class PhaseMetrics:
    """Aggregated metrics for a research phase."""

    phase_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    queries_executed: int = 0
    sources_found: int = 0
    sources_successful: int = 0
    sources_failed: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Get phase duration in seconds."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def source_success_rate(self) -> float:
        """Get source fetch success rate for this phase."""
        total = self.sources_successful + self.sources_failed
        if total == 0:
            return 1.0
        return self.sources_successful / total


class MetricsService:
    """
    Central service for tracking research metrics.

    Tracks:
    - Operation durations (MON-001)
    - Source success rates (MON-002)
    - Per-phase statistics
    - Overall research statistics
    """

    def __init__(self):
        self._operations: List[OperationMetric] = []
        self._phases: Dict[str, PhaseMetrics] = {}
        self._research_start: Optional[float] = None
        self._research_end: Optional[float] = None
        self._company_name: Optional[str] = None

    def start_research(self, company_name: str) -> None:
        """Mark the start of a research session."""
        self._research_start = time.time()
        self._company_name = company_name
        self._operations = []
        self._phases = {}
        logger.info(f"Research started for: {company_name}")

    def end_research(self) -> None:
        """Mark the end of a research session."""
        self._research_end = time.time()
        duration = self._research_end - (self._research_start or self._research_end)
        logger.info(f"Research completed in {duration:.1f}s")

    @contextmanager
    def track_operation(self, name: str, metadata: Dict[str, Any] = None):
        """
        Context manager to track an operation's duration.

        Usage:
            with metrics.track_operation("fetch_sources"):
                # do work
                pass
        """
        metric = OperationMetric(
            name=name,
            start_time=time.time(),
            metadata=metadata or {},
        )
        self._operations.append(metric)

        try:
            yield metric
            metric.success = True
        except Exception as e:
            metric.success = False
            metric.error = str(e)
            raise
        finally:
            metric.end_time = time.time()

    def start_phase(self, phase_name: str) -> PhaseMetrics:
        """Start tracking a research phase."""
        metrics = PhaseMetrics(
            phase_name=phase_name,
            start_time=datetime.now(),
        )
        self._phases[phase_name] = metrics
        return metrics

    def end_phase(self, phase_name: str) -> None:
        """End tracking a research phase."""
        if phase_name in self._phases:
            self._phases[phase_name].end_time = datetime.now()

    def record_queries(self, phase_name: str, count: int) -> None:
        """Record number of queries executed in a phase."""
        if phase_name in self._phases:
            self._phases[phase_name].queries_executed += count

    def record_sources(
        self,
        phase_name: str,
        found: int,
        successful: int = 0,
        failed: int = 0,
    ) -> None:
        """Record source statistics for a phase."""
        if phase_name in self._phases:
            self._phases[phase_name].sources_found += found
            self._phases[phase_name].sources_successful += successful
            self._phases[phase_name].sources_failed += failed

    def record_error(self, phase_name: str, error: str) -> None:
        """Record an error in a phase."""
        if phase_name in self._phases:
            self._phases[phase_name].errors.append(error)

    def get_total_duration(self) -> float:
        """Get total research duration in seconds."""
        if not self._research_start:
            return 0.0
        end = self._research_end or time.time()
        return end - self._research_start

    def get_phase_durations(self) -> Dict[str, float]:
        """Get duration for each phase."""
        return {
            name: phase.duration_seconds
            for name, phase in self._phases.items()
        }

    def get_source_success_rates(self) -> Dict[str, float]:
        """Get source success rate for each phase."""
        return {
            name: phase.source_success_rate
            for name, phase in self._phases.items()
        }

    def get_overall_source_success_rate(self) -> float:
        """Get overall source success rate across all phases."""
        total_successful = sum(p.sources_successful for p in self._phases.values())
        total_failed = sum(p.sources_failed for p in self._phases.values())
        total = total_successful + total_failed
        if total == 0:
            # Fall back to source tracker stats
            tracker = get_source_tracker()
            return tracker.get_success_rate()
        return total_successful / total

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of all metrics.

        Returns:
            Dictionary with all metrics data
        """
        # Get source tracker stats
        tracker = get_source_tracker()
        fetch_summary = tracker.get_fetch_summary()

        return {
            "company": self._company_name,
            "duration": {
                "total_seconds": self.get_total_duration(),
                "by_phase": self.get_phase_durations(),
            },
            "sources": {
                "total_tracked": len(tracker.get_all_sources()),
                "fetch_attempts": fetch_summary["total_attempts"],
                "fetch_successful": fetch_summary["successful"],
                "fetch_failed": fetch_summary["failed"],
                "overall_success_rate": self.get_overall_source_success_rate(),
                "by_phase": {
                    name: {
                        "found": p.sources_found,
                        "successful": p.sources_successful,
                        "failed": p.sources_failed,
                        "success_rate": p.source_success_rate,
                    }
                    for name, p in self._phases.items()
                },
                "by_domain": fetch_summary.get("by_domain", {}),
            },
            "queries": {
                "total": sum(p.queries_executed for p in self._phases.values()),
                "by_phase": {
                    name: p.queries_executed
                    for name, p in self._phases.items()
                },
            },
            "operations": {
                "total": len(self._operations),
                "successful": sum(1 for o in self._operations if o.success),
                "failed": sum(1 for o in self._operations if not o.success),
                "by_name": self._aggregate_operations(),
            },
            "errors": {
                name: p.errors
                for name, p in self._phases.items()
                if p.errors
            },
        }

    def _aggregate_operations(self) -> Dict[str, Dict[str, Any]]:
        """Aggregate operation metrics by name."""
        aggregated: Dict[str, Dict[str, Any]] = {}

        for op in self._operations:
            if op.name not in aggregated:
                aggregated[op.name] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "successful": 0,
                    "failed": 0,
                }

            aggregated[op.name]["count"] += 1
            aggregated[op.name]["total_duration"] += op.duration_seconds
            if op.success:
                aggregated[op.name]["successful"] += 1
            else:
                aggregated[op.name]["failed"] += 1

        # Add average duration
        for stats in aggregated.values():
            stats["avg_duration"] = (
                stats["total_duration"] / stats["count"]
                if stats["count"] > 0
                else 0.0
            )

        return aggregated

    def print_summary(self) -> None:
        """Print a formatted summary to console (uses rich if available)."""
        summary = self.get_summary()

        try:
            from ...utils.cli import console, print_research_metrics, ResearchMetrics

            # Convert to ResearchMetrics for rich display
            metrics = ResearchMetrics(
                start_time=self._research_start or 0,
                end_time=self._research_end or time.time(),
                phase_durations=summary["duration"]["by_phase"],
                source_counts={
                    name: data["found"]
                    for name, data in summary["sources"]["by_phase"].items()
                },
                query_counts=summary["queries"]["by_phase"],
            )
            print_research_metrics(metrics)

        except ImportError:
            # Fallback to basic print
            print("\n" + "=" * 60)
            print("RESEARCH METRICS")
            print("=" * 60)
            print(f"Company: {summary['company']}")
            print(f"Total Duration: {summary['duration']['total_seconds']:.1f}s")
            print(f"Total Sources: {summary['sources']['total_tracked']}")
            print(f"Source Success Rate: {summary['sources']['overall_success_rate']:.1%}")
            print(f"Total Queries: {summary['queries']['total']}")
            print("=" * 60 + "\n")


# =============================================================================
# Singleton Instance
# =============================================================================

_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service


def reset_metrics_service() -> None:
    """Reset the metrics service (for new research sessions)."""
    global _metrics_service
    _metrics_service = MetricsService()


__all__ = [
    "MetricsService",
    "OperationMetric",
    "PhaseMetrics",
    "get_metrics_service",
    "reset_metrics_service",
]
