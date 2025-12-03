"""
Research progress tracking system.

Provides real-time visibility into agent state and research progress.
"""

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .logger import setup_logger

logger = setup_logger("progress")


class ResearchStage(str, Enum):
    """Stages of the research process."""
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
class ProgressEvent:
    """A single progress event."""
    timestamp: datetime
    stage: ResearchStage
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "stage": self.stage.value,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class ResearchProgress:
    """
    Tracks the progress of a research task.

    Provides information about:
    - Current stage and activity
    - Depth/breadth progress for recursive research
    - Query completion status
    - Time tracking
    """
    # Task identification
    task_id: str = ""
    company_name: str = ""

    # Depth tracking (for recursive research)
    total_depth: int = 1
    current_depth: int = 0

    # Breadth tracking (queries at current depth)
    total_breadth: int = 1
    current_breadth: int = 0

    # Query tracking
    total_queries: int = 0
    completed_queries: int = 0
    current_query: str = ""

    # Source tracking
    total_sources: int = 0
    processed_sources: int = 0

    # Stage tracking
    current_stage: ResearchStage = ResearchStage.INITIALIZING
    current_activity: str = ""

    # Time tracking
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Event history
    events: List[ProgressEvent] = field(default_factory=list)

    # Error tracking
    errors: List[str] = field(default_factory=list)

    def start(self):
        """Mark the research as started."""
        self.started_at = datetime.now()
        self.updated_at = self.started_at
        self._add_event(ResearchStage.INITIALIZING, "Research started")

    def set_stage(self, stage: ResearchStage, activity: str = ""):
        """Update the current stage."""
        self.current_stage = stage
        self.current_activity = activity
        self.updated_at = datetime.now()
        self._add_event(stage, activity or f"Entered {stage.value} stage")

    def set_activity(self, activity: str):
        """Update the current activity without changing stage."""
        self.current_activity = activity
        self.updated_at = datetime.now()

    def set_query(self, query: str, index: Optional[int] = None, total: Optional[int] = None):
        """Update the current query being processed."""
        self.current_query = query
        if index is not None:
            self.current_breadth = index
        if total is not None:
            self.total_breadth = total
        self.updated_at = datetime.now()

    def complete_query(self):
        """Mark the current query as completed."""
        self.completed_queries += 1
        self.current_breadth += 1
        self.updated_at = datetime.now()

    def increment_depth(self):
        """Move to the next depth level."""
        self.current_depth += 1
        self.current_breadth = 0
        self.updated_at = datetime.now()
        self._add_event(
            self.current_stage,
            f"Moving to depth {self.current_depth}/{self.total_depth}"
        )

    def add_sources(self, count: int):
        """Add discovered sources."""
        self.total_sources += count
        self.updated_at = datetime.now()

    def process_source(self):
        """Mark a source as processed."""
        self.processed_sources += 1
        self.updated_at = datetime.now()

    def add_error(self, error: str):
        """Record an error."""
        self.errors.append(error)
        self._add_event(ResearchStage.ERROR, error)

    def complete(self):
        """Mark the research as complete."""
        self.current_stage = ResearchStage.COMPLETE
        self.current_activity = "Research complete"
        self.updated_at = datetime.now()
        self._add_event(ResearchStage.COMPLETE, "Research completed successfully")

    def _add_event(self, stage: ResearchStage, message: str, details: Optional[Dict] = None):
        """Add an event to the history."""
        event = ProgressEvent(
            timestamp=datetime.now(),
            stage=stage,
            message=message,
            details=details,
        )
        self.events.append(event)
        # Keep events bounded
        if len(self.events) > 100:
            self.events = self.events[-100:]

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.started_at is None:
            return 0.0
        end_time = self.updated_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def query_progress(self) -> float:
        """Get query completion progress (0.0 to 1.0)."""
        if self.total_queries == 0:
            return 0.0
        return self.completed_queries / self.total_queries

    @property
    def source_progress(self) -> float:
        """Get source processing progress (0.0 to 1.0)."""
        if self.total_sources == 0:
            return 0.0
        return self.processed_sources / self.total_sources

    @property
    def depth_progress(self) -> float:
        """Get depth progress (0.0 to 1.0)."""
        if self.total_depth == 0:
            return 0.0
        return self.current_depth / self.total_depth

    @property
    def overall_progress(self) -> float:
        """Get overall progress estimate (0.0 to 1.0)."""
        if self.current_stage == ResearchStage.COMPLETE:
            return 1.0
        if self.current_stage == ResearchStage.INITIALIZING:
            return 0.0

        # Weight different aspects
        query_weight = 0.4
        source_weight = 0.3
        depth_weight = 0.3

        return (
            self.query_progress * query_weight +
            self.source_progress * source_weight +
            self.depth_progress * depth_weight
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "company_name": self.company_name,
            "current_stage": self.current_stage.value,
            "current_activity": self.current_activity,
            "current_query": self.current_query,
            "progress": {
                "depth": f"{self.current_depth}/{self.total_depth}",
                "breadth": f"{self.current_breadth}/{self.total_breadth}",
                "queries": f"{self.completed_queries}/{self.total_queries}",
                "sources": f"{self.processed_sources}/{self.total_sources}",
                "overall": f"{self.overall_progress:.1%}",
            },
            "elapsed_seconds": self.elapsed_time,
            "errors": self.errors,
        }

    def format_status(self) -> str:
        """Format a human-readable status string."""
        status_parts = [
            f"[{self.current_stage.value.upper()}]",
            f"{self.overall_progress:.0%}",
        ]

        if self.current_activity:
            status_parts.append(self.current_activity)
        elif self.current_query:
            status_parts.append(f"Query: {self.current_query[:50]}...")

        if self.total_queries > 0:
            status_parts.append(f"({self.completed_queries}/{self.total_queries} queries)")

        return " ".join(status_parts)


# Type for progress callbacks
ProgressCallback = Callable[[ResearchProgress], None]
AsyncProgressCallback = Callable[[ResearchProgress], "asyncio.Future[None]"]


class ProgressTracker:
    """
    Manages progress tracking with callback support.

    Allows registering callbacks that are invoked on progress updates.
    """

    def __init__(self):
        self._progress: Optional[ResearchProgress] = None
        self._callbacks: List[ProgressCallback] = []
        self._async_callbacks: List[AsyncProgressCallback] = []
        self._lock = threading.Lock()

    def create_progress(
        self,
        task_id: str = "",
        company_name: str = "",
        total_depth: int = 1,
        total_queries: int = 0,
    ) -> ResearchProgress:
        """
        Create a new progress tracker for a research task.

        Args:
            task_id: Unique identifier for the task.
            company_name: Name of the company being researched.
            total_depth: Total depth for recursive research.
            total_queries: Expected number of queries.

        Returns:
            New ResearchProgress instance.
        """
        progress = ResearchProgress(
            task_id=task_id,
            company_name=company_name,
            total_depth=total_depth,
            total_queries=total_queries,
        )
        progress.start()

        with self._lock:
            self._progress = progress

        self._notify(progress)
        return progress

    def get_progress(self) -> Optional[ResearchProgress]:
        """Get the current progress."""
        with self._lock:
            return self._progress

    def update(self, **kwargs):
        """
        Update progress and notify callbacks.

        Args:
            **kwargs: Fields to update on the progress object.
        """
        with self._lock:
            if self._progress is None:
                return

            for key, value in kwargs.items():
                if hasattr(self._progress, key):
                    setattr(self._progress, key, value)

            self._progress.updated_at = datetime.now()
            progress = self._progress

        self._notify(progress)

    def set_stage(self, stage: ResearchStage, activity: str = ""):
        """Update stage and notify."""
        with self._lock:
            if self._progress:
                self._progress.set_stage(stage, activity)
                progress = self._progress
            else:
                return

        self._notify(progress)

    def set_activity(self, activity: str):
        """Update activity and notify."""
        with self._lock:
            if self._progress:
                self._progress.set_activity(activity)
                progress = self._progress
            else:
                return

        self._notify(progress)

    def register_callback(self, callback: ProgressCallback):
        """Register a synchronous callback."""
        with self._lock:
            self._callbacks.append(callback)

    def register_async_callback(self, callback: AsyncProgressCallback):
        """Register an async callback."""
        with self._lock:
            self._async_callbacks.append(callback)

    def unregister_callback(self, callback: ProgressCallback):
        """Unregister a callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def _notify(self, progress: ResearchProgress):
        """Notify all registered callbacks."""
        with self._lock:
            callbacks = list(self._callbacks)
            async_callbacks = list(self._async_callbacks)

        # Call sync callbacks
        for callback in callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

        # Schedule async callbacks if there's a running loop
        for callback in async_callbacks:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(callback(progress))
            except RuntimeError:
                # No running loop, skip async callbacks
                pass
            except Exception as e:
                logger.error(f"Async progress callback error: {e}")

    def reset(self):
        """Reset the tracker."""
        with self._lock:
            self._progress = None


# Global progress tracker
_progress_tracker: Optional[ProgressTracker] = None
_progress_tracker_lock = threading.Lock()


def get_progress_tracker() -> ProgressTracker:
    """Get or create the global progress tracker."""
    global _progress_tracker
    if _progress_tracker is None:
        with _progress_tracker_lock:
            if _progress_tracker is None:
                _progress_tracker = ProgressTracker()
    return _progress_tracker


def reset_progress_tracker():
    """Reset the global progress tracker."""
    global _progress_tracker
    with _progress_tracker_lock:
        if _progress_tracker:
            _progress_tracker.reset()
        _progress_tracker = None


# Convenience functions for common progress updates
def log_progress(message: str, stage: Optional[ResearchStage] = None):
    """Log a progress message."""
    tracker = get_progress_tracker()
    if stage:
        tracker.set_stage(stage, message)
    else:
        tracker.set_activity(message)
    logger.info(f"Progress: {message}")
