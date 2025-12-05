"""
Shared project state for MCP server.

This module implements a thread-safe shared state model that allows MCP tools
to share data without explicit argument passing, reducing token usage
and improving efficiency.

Addresses ARCH-001: Stateful MCP Server Architecture
- Tools can share data without explicit argument passing
- State is preserved across tool calls within a session
- Thread-safe for concurrent requests
- Reduced token usage for context passing

Usage:
    from src.mcp.state import get_project_state, update_project_state

    # Read from state
    state = get_project_state()
    company = state.company_name

    # Update state
    update_project_state(company_analysis=result)
"""

from __future__ import annotations

import threading
import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging import setup_logger

logger = setup_logger("mcp_state")


class ResearchPhase(str, Enum):
    """Valid research workflow phases for MCP server."""

    IDLE = "idle"
    GATHERING = "gathering"
    ANALYZING = "analyzing"
    WRITING = "writing"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    ERROR = "error"


class SourceInfo(TypedDict, total=False):
    """Type definition for source information."""

    url: str
    title: str
    content: str
    source_type: str
    reliability_score: float


@dataclass
class ProjectState:
    """
    Shared state for the research project.

    This class maintains all research data that can be shared between
    MCP tool calls without explicit argument passing.

    Thread-safe: All read/write operations are protected by a lock.

    Attributes:
        session_id: Unique identifier for this research session
        company_name: Name of the company being researched
        company_website: Company website URL
        company_industry: Industry classification
        current_phase: Current research phase
        raw_data: Raw data gathered from sources
        company_analysis: Analyzed company data
        market_analysis: Market research results
        competitive_analysis: Competitor research results
        financial_analysis: Financial data analysis
        draft_report: Current draft of the research report
        final_report: Final completed report
        sources: List of sources used
        errors: List of errors encountered
        metadata: Additional metadata about the research
        created_at: Timestamp when session was created
        updated_at: Timestamp when session was last updated
    """

    # Session info
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Company info
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    company_description: Optional[str] = None

    # Research phase
    current_phase: ResearchPhase = ResearchPhase.IDLE

    # Raw data (Wave 1)
    raw_data: List[Dict[str, Any]] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)

    # Analysis results (Wave 2)
    company_analysis: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    competitive_analysis: Optional[Dict[str, Any]] = None
    financial_analysis: Optional[Dict[str, Any]] = None
    sales_analysis: Optional[Dict[str, Any]] = None
    brand_analysis: Optional[Dict[str, Any]] = None
    technology_analysis: Optional[Dict[str, Any]] = None

    # Reports (Wave 3)
    draft_report: Optional[str] = None
    final_report: Optional[str] = None
    report_sections: Dict[str, str] = field(default_factory=dict)

    # Sources and errors
    sources: List[SourceInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Evaluation metrics
    evaluation_metrics: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "company_name": self.company_name,
            "company_website": self.company_website,
            "company_industry": self.company_industry,
            "company_description": self.company_description,
            "current_phase": self.current_phase.value,
            "raw_data": self.raw_data,
            "search_queries": self.search_queries,
            "company_analysis": self.company_analysis,
            "market_analysis": self.market_analysis,
            "competitive_analysis": self.competitive_analysis,
            "financial_analysis": self.financial_analysis,
            "sales_analysis": self.sales_analysis,
            "brand_analysis": self.brand_analysis,
            "technology_analysis": self.technology_analysis,
            "draft_report": self.draft_report,
            "final_report": self.final_report,
            "report_sections": self.report_sections,
            "sources": self.sources,
            "errors": self.errors,
            "evaluation_metrics": self.evaluation_metrics,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectState":
        """Create state from dictionary."""
        phase = data.get("current_phase", "idle")
        if isinstance(phase, str):
            phase = ResearchPhase(phase)

        return cls(
            session_id=data.get("session_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            company_name=data.get("company_name"),
            company_website=data.get("company_website"),
            company_industry=data.get("company_industry"),
            company_description=data.get("company_description"),
            current_phase=phase,
            raw_data=data.get("raw_data", []),
            search_queries=data.get("search_queries", []),
            company_analysis=data.get("company_analysis"),
            market_analysis=data.get("market_analysis"),
            competitive_analysis=data.get("competitive_analysis"),
            financial_analysis=data.get("financial_analysis"),
            sales_analysis=data.get("sales_analysis"),
            brand_analysis=data.get("brand_analysis"),
            technology_analysis=data.get("technology_analysis"),
            draft_report=data.get("draft_report"),
            final_report=data.get("final_report"),
            report_sections=data.get("report_sections", {}),
            sources=data.get("sources", []),
            errors=data.get("errors", []),
            evaluation_metrics=data.get("evaluation_metrics"),
            quality_score=data.get("quality_score"),
            metadata=data.get("metadata", {}),
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state (for logging/debugging)."""
        return {
            "session_id": self.session_id,
            "company_name": self.company_name,
            "current_phase": self.current_phase.value,
            "has_company_analysis": self.company_analysis is not None,
            "has_market_analysis": self.market_analysis is not None,
            "has_competitive_analysis": self.competitive_analysis is not None,
            "has_financial_analysis": self.financial_analysis is not None,
            "has_draft_report": self.draft_report is not None,
            "has_final_report": self.final_report is not None,
            "num_sources": len(self.sources),
            "num_errors": len(self.errors),
        }


# =============================================================================
# Thread-Safe State Management
# =============================================================================


class StateManager:
    """
    Thread-safe manager for project state.

    Implements the singleton pattern with thread-safe access to shared state.
    All state modifications are atomic and protected by a reentrant lock.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._state: Optional[ProjectState] = None
        self._checkpoints: List[ProjectState] = []
        self._max_checkpoints: int = 5

    def get_state(self) -> ProjectState:
        """
        Get the current project state.

        Returns a copy to prevent external mutation.
        Creates a new state if none exists.

        Returns:
            Copy of the current project state
        """
        with self._lock:
            if self._state is None:
                self._state = self._create_new_state()
            # Return a deep copy to prevent external mutation
            return copy.deepcopy(self._state)

    def set_state(self, state: ProjectState) -> None:
        """
        Replace the entire project state.

        Args:
            state: New state to set
        """
        with self._lock:
            self._state = copy.deepcopy(state)
            self._state.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"State replaced: {self._state.get_summary()}")

    def update_state(self, **kwargs: Any) -> ProjectState:
        """
        Update specific fields in the project state.

        Thread-safe atomic update of state fields.

        Args:
            **kwargs: Fields to update

        Returns:
            Updated state
        """
        with self._lock:
            if self._state is None:
                self._state = self._create_new_state()

            for key, value in kwargs.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
                else:
                    logger.warning(f"Unknown state field: {key}")

            self._state.updated_at = datetime.now(timezone.utc).isoformat()
            logger.debug(f"State updated: {list(kwargs.keys())}")

            return copy.deepcopy(self._state)

    def reset_state(self) -> ProjectState:
        """
        Reset the project state to initial values.

        Returns:
            New empty state
        """
        with self._lock:
            self._state = self._create_new_state()
            self._checkpoints.clear()
            logger.info("State reset to initial values")
            return copy.deepcopy(self._state)

    def checkpoint(self) -> None:
        """
        Create a checkpoint of the current state.

        Checkpoints can be used to rollback to a previous state.
        """
        with self._lock:
            if self._state is not None:
                checkpoint = copy.deepcopy(self._state)
                self._checkpoints.append(checkpoint)

                # Limit checkpoint history
                if len(self._checkpoints) > self._max_checkpoints:
                    self._checkpoints.pop(0)

                logger.debug(f"Checkpoint created: {len(self._checkpoints)} total")

    def rollback(self) -> Optional[ProjectState]:
        """
        Rollback to the last checkpoint.

        Returns:
            Previous state or None if no checkpoints
        """
        with self._lock:
            if self._checkpoints:
                self._state = self._checkpoints.pop()
                self._state.updated_at = datetime.now(timezone.utc).isoformat()
                logger.info("State rolled back to checkpoint")
                return copy.deepcopy(self._state)
            logger.warning("No checkpoints available for rollback")
            return None

    def add_source(self, source: SourceInfo) -> None:
        """Add a source to the state (thread-safe)."""
        with self._lock:
            if self._state is None:
                self._state = self._create_new_state()
            self._state.sources.append(source)
            self._state.updated_at = datetime.now(timezone.utc).isoformat()

    def add_error(self, error: str) -> None:
        """Add an error to the state (thread-safe)."""
        with self._lock:
            if self._state is None:
                self._state = self._create_new_state()
            self._state.errors.append(error)
            self._state.updated_at = datetime.now(timezone.utc).isoformat()
            logger.error(f"Error added to state: {error}")

    def add_raw_data(self, data: Dict[str, Any]) -> None:
        """Add raw data to the state (thread-safe)."""
        with self._lock:
            if self._state is None:
                self._state = self._create_new_state()
            self._state.raw_data.append(data)
            self._state.updated_at = datetime.now(timezone.utc).isoformat()

    def set_phase(self, phase: ResearchPhase) -> None:
        """Set the current research phase (thread-safe)."""
        with self._lock:
            if self._state is None:
                self._state = self._create_new_state()
            old_phase = self._state.current_phase
            self._state.current_phase = phase
            self._state.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Phase changed: {old_phase.value} -> {phase.value}")

    def _create_new_state(self) -> ProjectState:
        """Create a new project state with default values."""
        import uuid

        now = datetime.now(timezone.utc).isoformat()
        return ProjectState(
            session_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
        )


# =============================================================================
# Global State Manager Instance
# =============================================================================

_state_manager: Optional[StateManager] = None
_state_manager_lock = threading.Lock()


def _get_state_manager() -> StateManager:
    """Get the global state manager instance (thread-safe singleton)."""
    global _state_manager
    if _state_manager is None:
        with _state_manager_lock:
            if _state_manager is None:
                _state_manager = StateManager()
    return _state_manager


def get_project_state() -> ProjectState:
    """
    Get the current project state.

    This is the main entry point for reading shared state.
    Returns a copy to prevent external mutation.

    Returns:
        Copy of the current project state

    Example:
        state = get_project_state()
        company = state.company_name
        if state.market_analysis:
            market_size = state.market_analysis.get("market_size")
    """
    return _get_state_manager().get_state()


def set_project_state(state: ProjectState) -> None:
    """
    Replace the entire project state.

    Use this to restore a saved state or set initial values.

    Args:
        state: New state to set

    Example:
        new_state = ProjectState(
            company_name="Acme Corp",
            company_website="https://acme.com"
        )
        set_project_state(new_state)
    """
    _get_state_manager().set_state(state)


def update_project_state(**kwargs: Any) -> ProjectState:
    """
    Update specific fields in the project state.

    This is the main entry point for modifying shared state.
    Thread-safe atomic update of state fields.

    Args:
        **kwargs: Fields to update

    Returns:
        Updated state

    Example:
        # Update company info
        update_project_state(
            company_name="Acme Corp",
            company_website="https://acme.com"
        )

        # Update analysis results
        update_project_state(
            market_analysis={"market_size": "$10B", "growth_rate": "5%"}
        )
    """
    return _get_state_manager().update_state(**kwargs)


def reset_project_state() -> ProjectState:
    """
    Reset the project state to initial values.

    Call this when starting a new research session.

    Returns:
        New empty state

    Example:
        reset_project_state()
        update_project_state(company_name="New Company")
    """
    return _get_state_manager().reset_state()


def checkpoint_state() -> None:
    """
    Create a checkpoint of the current state.

    Checkpoints can be used to rollback to a previous state
    if something goes wrong during research.

    Example:
        # Before risky operation
        checkpoint_state()
        try:
            perform_analysis()
        except Exception:
            rollback_state()
    """
    _get_state_manager().checkpoint()


def rollback_state() -> Optional[ProjectState]:
    """
    Rollback to the last checkpoint.

    Returns:
        Previous state or None if no checkpoints available
    """
    return _get_state_manager().rollback()


def add_source(source: SourceInfo) -> None:
    """Add a source to the shared state."""
    _get_state_manager().add_source(source)


def add_error(error: str) -> None:
    """Add an error to the shared state."""
    _get_state_manager().add_error(error)


def add_raw_data(data: Dict[str, Any]) -> None:
    """Add raw data to the shared state."""
    _get_state_manager().add_raw_data(data)


def set_phase(phase: ResearchPhase) -> None:
    """Set the current research phase."""
    _get_state_manager().set_phase(phase)


# =============================================================================
# Testing Utilities
# =============================================================================


def reset_state_manager() -> None:
    """
    Reset the global state manager (for testing).

    This clears the singleton instance, allowing tests to start fresh.
    """
    global _state_manager
    with _state_manager_lock:
        _state_manager = None
