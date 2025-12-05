"""
Research workflow state management.

This module implements the state model for the LangGraph research workflow,
with validation, bounds checking, and thread-safe operations.

Addresses:
- GR-001: State validation between transitions
- GR-002: Race conditions in state updates
- GR-003: Unbounded state accumulation
- GR-004: State rollback on failure
- GR-005: Memory leak prevention
- GR-014: State schema validation
- GR-015: Standardized error handling
- GR-017: Lifecycle hooks
- GR-019: Configurable configuration
"""

from typing import List, Dict, Optional, Any, Set, Callable
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from langchain_core.messages import BaseMessage
import copy
import asyncio
from functools import wraps
from dataclasses import dataclass, field

# Import typed models for enhanced type safety
# Import typed models for enhanced type safety
from src.domain.models.base import (
    FinancialData,
    MarketData,
    CompetitorData,
    BrandData,
    SalesData,
    TypedResearchContext,
)
from src.core.types import ResearchSource


# =============================================================================
# Configurable State Configuration (GR-019)
# =============================================================================


@dataclass
class StateConfig:
    """
    Centralized configuration for state management.

    Addresses GR-019: Hardcoded configuration by providing a single
    place to configure all state-related settings.
    """

    # Bounds (GR-003)
    max_raw_data_items: int = 100
    max_source_log_items: int = 100
    max_messages: int = 50
    max_errors: int = 50
    max_draft_size_chars: int = 500_000  # 500KB per draft
    max_feedback_loops: int = 10

    # Checkpointing (GR-004)
    max_checkpoints: int = 5

    # Validation (GR-014)
    strict_validation: bool = True
    allow_extra_fields: bool = False

    def __repr__(self) -> str:
        """Return string representation (GR-026)."""
        return (
            f"StateConfig(max_raw_data={self.max_raw_data_items}, "
            f"max_checkpoints={self.max_checkpoints}, "
            f"strict={self.strict_validation})"
        )


# Global state configuration
_state_config: Optional[StateConfig] = None


def get_state_config() -> StateConfig:
    """Get the global state configuration with environment variable overrides."""
    global _state_config
    if _state_config is None:
        import os

        _state_config = StateConfig(
            max_raw_data_items=int(os.getenv("STATE_MAX_RAW_DATA_ITEMS", "100")),
            max_source_log_items=int(os.getenv("STATE_MAX_SOURCE_LOG_ITEMS", "100")),
            max_messages=int(os.getenv("STATE_MAX_MESSAGES", "50")),
            max_errors=int(os.getenv("STATE_MAX_ERRORS", "50")),
            max_draft_size_chars=int(os.getenv("STATE_MAX_DRAFT_SIZE_CHARS", "500000")),
            max_feedback_loops=int(os.getenv("STATE_MAX_FEEDBACK_LOOPS", "10")),
            max_checkpoints=int(os.getenv("STATE_MAX_CHECKPOINTS", "5")),
        )
    return _state_config


def set_state_config(config: StateConfig) -> None:
    """Set a custom state configuration."""
    global _state_config
    _state_config = config


def reset_state_config() -> None:
    """Reset to default state configuration."""
    global _state_config
    _state_config = None


# Legacy constants for backward compatibility (GR-003)
# Now configurable via environment variables
import os as _os

MAX_RAW_DATA_ITEMS = int(_os.getenv("STATE_MAX_RAW_DATA_ITEMS", "100"))
MAX_SOURCE_LOG_ITEMS = int(_os.getenv("STATE_MAX_SOURCE_LOG_ITEMS", "100"))
MAX_MESSAGES = int(_os.getenv("STATE_MAX_MESSAGES", "50"))
MAX_ERRORS = int(_os.getenv("STATE_MAX_ERRORS", "50"))
MAX_DRAFT_SIZE_CHARS = int(_os.getenv("STATE_MAX_DRAFT_SIZE_CHARS", "500000"))
MAX_FEEDBACK_LOOPS = int(_os.getenv("STATE_MAX_FEEDBACK_LOOPS", "10"))


# =============================================================================
# Error Types (GR-015: Standardized Error Handling)
# =============================================================================


class StateErrorCode(str, Enum):
    """Standardized error codes for state operations."""

    VALIDATION_ERROR = "STATE_VALIDATION_ERROR"
    TRANSITION_ERROR = "STATE_TRANSITION_ERROR"
    BOUNDS_EXCEEDED = "STATE_BOUNDS_EXCEEDED"
    SCHEMA_MISMATCH = "STATE_SCHEMA_MISMATCH"
    CHECKPOINT_ERROR = "STATE_CHECKPOINT_ERROR"
    ROLLBACK_ERROR = "STATE_ROLLBACK_ERROR"
    HOOK_ERROR = "STATE_HOOK_ERROR"


@dataclass
class StateError:
    """
    Structured error information for state operations.

    Addresses GR-015: Inconsistent error handling by providing
    a standardized error structure.
    """

    code: StateErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    phase: Optional[str] = None
    recoverable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "phase": self.phase,
            "recoverable": self.recoverable,
        }

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"


class StateValidationError(Exception):
    """Exception for state validation failures."""

    def __init__(self, error: StateError):
        self.error = error
        super().__init__(str(error))


class StateTransitionError(Exception):
    """Exception for invalid state transitions."""

    def __init__(self, error: StateError):
        self.error = error
        super().__init__(str(error))


# =============================================================================
# Lifecycle Hooks (GR-017)
# =============================================================================


LifecycleHook = Callable[["ResearchState", Optional["ResearchState"]], None]


@dataclass
class LifecycleHooks:
    """
    Lifecycle hooks for state transitions.

    Addresses GR-017: Missing lifecycle hooks by providing
    callbacks for state transition events.
    """

    on_before_transition: List[LifecycleHook] = field(default_factory=list)
    on_after_transition: List[LifecycleHook] = field(default_factory=list)
    on_validation_error: List[Callable[[StateError], None]] = field(
        default_factory=list
    )
    on_checkpoint: List[Callable[[Dict[str, Any]], None]] = field(default_factory=list)
    on_rollback: List[Callable[[Dict[str, Any]], None]] = field(default_factory=list)

    def __repr__(self) -> str:
        """Return string representation (GR-026)."""
        return (
            f"LifecycleHooks(before={len(self.on_before_transition)}, "
            f"after={len(self.on_after_transition)}, "
            f"errors={len(self.on_validation_error)})"
        )


# Global lifecycle hooks
_lifecycle_hooks: Optional[LifecycleHooks] = None


def get_lifecycle_hooks() -> LifecycleHooks:
    """Get the global lifecycle hooks."""
    global _lifecycle_hooks
    if _lifecycle_hooks is None:
        _lifecycle_hooks = LifecycleHooks()
    return _lifecycle_hooks


def register_hook(
    hook_type: str,
    callback: Callable[..., Any],
) -> None:
    """
    Register a lifecycle hook.

    Args:
        hook_type: One of 'before_transition', 'after_transition',
                   'validation_error', 'checkpoint', 'rollback'
        callback: Function to call when the event occurs
    """
    hooks = get_lifecycle_hooks()
    hook_map: Dict[str, List[Callable[..., Any]]] = {
        "before_transition": hooks.on_before_transition,
        "after_transition": hooks.on_after_transition,
        "validation_error": hooks.on_validation_error,
        "checkpoint": hooks.on_checkpoint,
        "rollback": hooks.on_rollback,
    }
    if hook_type not in hook_map:
        raise ValueError(f"Unknown hook type: {hook_type}")
    hook_map[hook_type].append(callback)


def reset_lifecycle_hooks() -> None:
    """Reset all lifecycle hooks."""
    global _lifecycle_hooks
    _lifecycle_hooks = None


# =============================================================================
# Schema Validation (GR-014)
# =============================================================================


@dataclass
class SchemaField:
    """Definition of a field in the state schema."""

    name: str
    field_type: type
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None


class StateSchema:
    """
    Schema definition for state validation.

    Addresses GR-014: No state schema validation by providing
    explicit schema definitions and validation.
    """

    def __init__(self, fields: Optional[List[SchemaField]] = None):
        self._fields: Dict[str, SchemaField] = {}
        if fields:
            for f in fields:
                self._fields[f.name] = f

    def add_field(self, field_def: SchemaField) -> None:
        """Add a field to the schema."""
        self._fields[field_def.name] = field_def

    def validate(self, state_dict: Dict[str, Any]) -> List[StateError]:
        """
        Validate a state dictionary against the schema.

        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[StateError] = []

        for name, field_def in self._fields.items():
            # Check required fields
            if field_def.required and name not in state_dict:
                errors.append(
                    StateError(
                        code=StateErrorCode.SCHEMA_MISMATCH,
                        message=f"Required field '{name}' is missing",
                        details={"field": name},
                    )
                )
                continue

            if name not in state_dict:
                continue

            value = state_dict[name]

            # Type check
            if not isinstance(value, field_def.field_type):
                errors.append(
                    StateError(
                        code=StateErrorCode.SCHEMA_MISMATCH,
                        message=f"Field '{name}' has wrong type",
                        details={
                            "field": name,
                            "expected": field_def.field_type.__name__,
                            "actual": type(value).__name__,
                        },
                    )
                )
                continue

            # Numeric bounds
            if field_def.min_value is not None and isinstance(value, (int, float)):
                if value < field_def.min_value:
                    errors.append(
                        StateError(
                            code=StateErrorCode.BOUNDS_EXCEEDED,
                            message=f"Field '{name}' below minimum",
                            details={
                                "field": name,
                                "min": field_def.min_value,
                                "value": value,
                            },
                        )
                    )

            if field_def.max_value is not None and isinstance(value, (int, float)):
                if value > field_def.max_value:
                    errors.append(
                        StateError(
                            code=StateErrorCode.BOUNDS_EXCEEDED,
                            message=f"Field '{name}' exceeds maximum",
                            details={
                                "field": name,
                                "max": field_def.max_value,
                                "value": value,
                            },
                        )
                    )

            # Length bounds for sequences
            if hasattr(value, "__len__"):
                if (
                    field_def.min_length is not None
                    and len(value) < field_def.min_length
                ):
                    errors.append(
                        StateError(
                            code=StateErrorCode.BOUNDS_EXCEEDED,
                            message=f"Field '{name}' too short",
                            details={
                                "field": name,
                                "min_length": field_def.min_length,
                                "length": len(value),
                            },
                        )
                    )

                if (
                    field_def.max_length is not None
                    and len(value) > field_def.max_length
                ):
                    errors.append(
                        StateError(
                            code=StateErrorCode.BOUNDS_EXCEEDED,
                            message=f"Field '{name}' too long",
                            details={
                                "field": name,
                                "max_length": field_def.max_length,
                                "length": len(value),
                            },
                        )
                    )

            # Allowed values
            if field_def.allowed_values is not None:
                if value not in field_def.allowed_values:
                    errors.append(
                        StateError(
                            code=StateErrorCode.VALIDATION_ERROR,
                            message=f"Field '{name}' has invalid value",
                            details={
                                "field": name,
                                "allowed": field_def.allowed_values,
                                "value": value,
                            },
                        )
                    )

        return errors

    @classmethod
    def default_schema(cls) -> "StateSchema":
        """Create the default schema for ResearchState."""
        return cls(
            [
                SchemaField(
                    "company_name", str, required=True, min_length=1, max_length=500
                ),
                SchemaField("website", str, required=False, max_length=2000),
                SchemaField(
                    "current_wave",
                    str,
                    required=True,
                    allowed_values=[
                        "init",
                        "gathering",
                        "thinking",
                        "writing",
                        "review",
                        "complete",
                        "error",
                    ],
                ),
                SchemaField(
                    "feedback_loop_count",
                    int,
                    required=False,
                    min_value=0,
                    max_value=MAX_FEEDBACK_LOOPS,
                ),
                SchemaField(
                    "raw_data", list, required=False, max_length=MAX_RAW_DATA_ITEMS
                ),
                SchemaField(
                    "source_log", list, required=False, max_length=MAX_SOURCE_LOG_ITEMS
                ),
                SchemaField("errors", list, required=False, max_length=MAX_ERRORS),
            ]
        )


# Global schema instance
_state_schema: Optional[StateSchema] = None


def get_state_schema() -> StateSchema:
    """Get the global state schema."""
    global _state_schema
    if _state_schema is None:
        _state_schema = StateSchema.default_schema()
    return _state_schema


def set_state_schema(schema: StateSchema) -> None:
    """Set a custom state schema."""
    global _state_schema
    _state_schema = schema


def reset_state_schema() -> None:
    """Reset to default state schema."""
    global _state_schema
    _state_schema = None


# =============================================================================
# Research Phase Enum (GR-001: State Validation)
# =============================================================================


class ResearchPhase(str, Enum):
    """Valid research workflow phases."""

    INIT = "init"
    GATHERING = "gathering"
    THINKING = "thinking"
    WRITING = "writing"
    REVIEW = "review"
    COMPLETE = "complete"
    ERROR = "error"


# =============================================================================
# Configurable Phase Transitions (GR-009: Remove hardcoded transitions)
# =============================================================================


class TransitionConfig:
    """
    Configurable phase transition rules.

    Addresses GR-009: Hardcoded state transitions by allowing
    custom transition rules to be defined.
    """

    # Default transitions - can be overridden
    DEFAULT_TRANSITIONS: Dict[ResearchPhase, Set[ResearchPhase]] = {
        ResearchPhase.INIT: {ResearchPhase.GATHERING, ResearchPhase.ERROR},
        ResearchPhase.GATHERING: {ResearchPhase.THINKING, ResearchPhase.ERROR},
        ResearchPhase.THINKING: {ResearchPhase.WRITING, ResearchPhase.ERROR},
        ResearchPhase.WRITING: {ResearchPhase.REVIEW, ResearchPhase.ERROR},
        ResearchPhase.REVIEW: {
            ResearchPhase.WRITING,
            ResearchPhase.COMPLETE,
            ResearchPhase.ERROR,
        },
        ResearchPhase.COMPLETE: set(),  # Terminal state
        ResearchPhase.ERROR: {ResearchPhase.INIT},  # Can restart from error
    }

    def __init__(
        self,
        transitions: Optional[Dict[ResearchPhase, Set[ResearchPhase]]] = None,
        allow_skip_phases: bool = False,
        terminal_phases: Optional[Set[ResearchPhase]] = None,
    ):
        """
        Initialize transition configuration.

        Args:
            transitions: Custom transition map (uses defaults if None)
            allow_skip_phases: If True, allows skipping intermediate phases
            terminal_phases: Set of terminal phases (defaults to {COMPLETE})
        """
        self._transitions = transitions or self.DEFAULT_TRANSITIONS.copy()
        self._allow_skip_phases = allow_skip_phases
        self._terminal_phases = terminal_phases or {ResearchPhase.COMPLETE}

    def get_valid_transitions(self, from_phase: ResearchPhase) -> Set[ResearchPhase]:
        """Get valid transitions from a phase."""
        return self._transitions.get(from_phase, set())

    def can_transition(
        self, from_phase: ResearchPhase, to_phase: ResearchPhase
    ) -> bool:
        """Check if a transition is valid."""
        if self._allow_skip_phases:
            # Allow any non-backward transition except from terminal
            if from_phase in self._terminal_phases:
                return False
            return True
        return to_phase in self.get_valid_transitions(from_phase)

    def add_transition(
        self, from_phase: ResearchPhase, to_phase: ResearchPhase
    ) -> None:
        """Add a new valid transition."""
        if from_phase not in self._transitions:
            self._transitions[from_phase] = set()
        self._transitions[from_phase].add(to_phase)

    def remove_transition(
        self, from_phase: ResearchPhase, to_phase: ResearchPhase
    ) -> None:
        """Remove a transition."""
        if from_phase in self._transitions:
            self._transitions[from_phase].discard(to_phase)

    def is_terminal(self, phase: ResearchPhase) -> bool:
        """Check if a phase is terminal."""
        return phase in self._terminal_phases

    def set_terminal(self, phase: ResearchPhase, is_terminal: bool = True) -> None:
        """Set whether a phase is terminal."""
        if is_terminal:
            self._terminal_phases.add(phase)
        else:
            self._terminal_phases.discard(phase)

    def __repr__(self) -> str:
        """Return string representation (GR-026)."""
        return (
            f"TransitionConfig(phases={len(self._transitions)}, "
            f"terminals={len(self._terminal_phases)}, "
            f"skip_phases={self._allow_skip_phases})"
        )


# Global transition config (can be replaced for custom workflows)
_transition_config: Optional[TransitionConfig] = None


def get_transition_config() -> TransitionConfig:
    """Get the global transition configuration."""
    global _transition_config
    if _transition_config is None:
        _transition_config = TransitionConfig()
    return _transition_config


def set_transition_config(config: TransitionConfig) -> None:
    """Set a custom transition configuration."""
    global _transition_config
    _transition_config = config


def reset_transition_config() -> None:
    """Reset to default transition configuration."""
    global _transition_config
    _transition_config = None


# Legacy constant for backward compatibility
VALID_PHASE_TRANSITIONS: Dict[ResearchPhase, Set[ResearchPhase]] = (
    TransitionConfig.DEFAULT_TRANSITIONS
)


# =============================================================================
# Source Metadata Model
# =============================================================================


class SourceMetadata(BaseModel):
    """Metadata for a research source."""

    url: str
    title: str
    date_accessed: str
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str = ""


# =============================================================================
# State Manager (GR-002: Race Conditions, GR-004: Rollback, GR-005: Memory)
# =============================================================================


class StateManager:
    """
    Thread-safe state manager for concurrent state updates.

    Addresses:
    - GR-002: Race conditions in state updates
    - GR-004: State rollback on failure
    - GR-005: Memory leak in graph execution
    """

    def __init__(self, max_checkpoints: int = 5):
        self._lock = asyncio.Lock()
        self._checkpoints: List[Dict[str, Any]] = []
        self._max_checkpoints = max_checkpoints

    async def update_state(
        self, state: Dict[str, Any], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Thread-safe state update with locking.

        Args:
            state: Current state dictionary
            updates: Updates to apply

        Returns:
            Updated state dictionary
        """
        async with self._lock:
            new_state = {**state, **updates}
            return new_state

    def checkpoint(self, state: Dict[str, Any]) -> None:
        """
        Create a checkpoint of the current state (GR-004: State Rollback).

        Args:
            state: State to checkpoint
        """
        checkpoint = copy.deepcopy(state)
        self._checkpoints.append(checkpoint)

        # Limit checkpoint history to prevent memory issues
        if len(self._checkpoints) > self._max_checkpoints:
            self._checkpoints.pop(0)

    def rollback(self) -> Optional[Dict[str, Any]]:
        """
        Rollback to the last checkpoint (GR-004: State Rollback).

        Returns:
            Previous state or None if no checkpoints
        """
        if self._checkpoints:
            return self._checkpoints.pop()
        return None

    def clear_checkpoints(self) -> None:
        """Clear all checkpoints to free memory (GR-005: Memory Leak)."""
        self._checkpoints.clear()

    def get_checkpoint_count(self) -> int:
        """Get the number of stored checkpoints."""
        return len(self._checkpoints)


# Global state manager instance
_state_manager: Optional[StateManager] = None
_state_manager_lock = asyncio.Lock()


async def get_state_manager() -> StateManager:
    """Get or create the global state manager instance (thread-safe)."""
    global _state_manager
    if _state_manager is None:
        async with _state_manager_lock:
            if _state_manager is None:
                _state_manager = StateManager()
    return _state_manager


def get_state_manager_sync() -> StateManager:
    """Get the global state manager instance (sync version for non-async contexts)."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def reset_state_manager() -> None:
    """Reset the global state manager (for testing)."""
    global _state_manager
    if _state_manager:
        _state_manager.clear_checkpoints()
    _state_manager = None


# =============================================================================
# Research State Model (Enhanced with validation)
# =============================================================================


class ResearchState(BaseModel):
    """
    The global state (Blackboard) for the research process.
    Passed between all agents in the LangGraph.

    Implements:
    - GR-001: State validation between transitions
    - GR-003: Bounded state accumulation
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,  # Validate on every update
    )

    # Input
    company_name: str = Field(..., min_length=1, max_length=500)
    website: str = Field(default="", max_length=2000)

    # Wave 1: Raw Data Gathering
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)
    source_log: List[SourceMetadata] = Field(default_factory=list)

    # Wave 2: Inferred Data (Analysis)
    financial_data: Dict[str, Any] = Field(default_factory=dict)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    sales_data: Dict[str, Any] = Field(default_factory=dict)
    competitor_data: Dict[str, Any] = Field(default_factory=dict)
    brand_data: Dict[str, Any] = Field(default_factory=dict)

    # Wave 3: Drafting
    drafts: Dict[str, str] = Field(default_factory=dict)

    # Meta / Control Flow
    current_wave: str = Field(default="init")
    messages: List[BaseMessage] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Feedback Loop
    critique_feedback: Optional[str] = None
    feedback_loop_count: int = Field(default=0, ge=0)

    # Evaluation Metrics
    evaluation_metrics: Optional[Dict[str, Any]] = None

    # =============================================================================
    # Validators (GR-001: State Validation, GR-003: Bounds)
    # =============================================================================

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        """Validate and sanitize company name."""
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty")
        return v

    @field_validator("current_wave")
    @classmethod
    def validate_current_wave(cls, v: str) -> str:
        """Validate current wave is a valid phase."""
        valid_waves = {phase.value for phase in ResearchPhase}
        if v not in valid_waves:
            raise ValueError(f"Invalid wave: {v}. Must be one of: {valid_waves}")
        return v

    @field_validator("raw_data")
    @classmethod
    def validate_raw_data_bounds(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enforce bounds on raw_data (GR-003)."""
        if len(v) > MAX_RAW_DATA_ITEMS:
            return v[-MAX_RAW_DATA_ITEMS:]
        return v

    @field_validator("source_log")
    @classmethod
    def validate_source_log_bounds(
        cls, v: List[SourceMetadata]
    ) -> List[SourceMetadata]:
        """Enforce bounds on source_log (GR-003)."""
        if len(v) > MAX_SOURCE_LOG_ITEMS:
            return v[-MAX_SOURCE_LOG_ITEMS:]
        return v

    @field_validator("messages")
    @classmethod
    def validate_messages_bounds(cls, v: List[BaseMessage]) -> List[BaseMessage]:
        """Enforce bounds on messages (GR-003)."""
        if len(v) > MAX_MESSAGES:
            return v[-MAX_MESSAGES:]
        return v

    @field_validator("errors")
    @classmethod
    def validate_errors_bounds(cls, v: List[str]) -> List[str]:
        """Enforce bounds on errors (GR-003)."""
        if len(v) > MAX_ERRORS:
            return v[-MAX_ERRORS:]
        return v

    @field_validator("drafts")
    @classmethod
    def validate_drafts_size(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Enforce size limits on drafts (GR-003)."""
        for key, content in v.items():
            if len(content) > MAX_DRAFT_SIZE_CHARS:
                v[key] = (
                    content[:MAX_DRAFT_SIZE_CHARS]
                    + "\n\n[Content truncated due to size limits]"
                )
        return v

    @field_validator("feedback_loop_count")
    @classmethod
    def validate_feedback_loop_count(cls, v: int) -> int:
        """Enforce max feedback loops (GR-003)."""
        return min(v, MAX_FEEDBACK_LOOPS)

    # =============================================================================
    # Phase Transition Methods (GR-001)
    # =============================================================================

    def can_transition_to(self, new_phase: ResearchPhase) -> bool:
        """
        Check if transition to new phase is valid.

        Uses the global TransitionConfig to determine valid transitions.

        Args:
            new_phase: Target phase

        Returns:
            True if transition is valid
        """
        try:
            current = ResearchPhase(self.current_wave)
        except ValueError:
            return False
        config = get_transition_config()
        return config.can_transition(current, new_phase)

    def transition_to(self, new_phase: ResearchPhase) -> "ResearchState":
        """
        Transition to a new phase with validation.

        Args:
            new_phase: Target phase

        Returns:
            New state with updated phase

        Raises:
            ValueError: If transition is invalid
        """
        if not self.can_transition_to(new_phase):
            config = get_transition_config()
            try:
                current = ResearchPhase(self.current_wave)
                valid = config.get_valid_transitions(current)
                valid_str = [p.value for p in valid]
            except ValueError:
                valid_str = []

            raise ValueError(
                f"Invalid phase transition: {self.current_wave} -> {new_phase.value}. "
                f"Valid transitions: {valid_str}"
            )

        return self.model_copy(update={"current_wave": new_phase.value})

    # =============================================================================
    # State Management Methods
    # =============================================================================

    def add_error(self, error: str) -> "ResearchState":
        """Add an error message to the state."""
        new_errors = self.errors + [error]
        return self.model_copy(update={"errors": new_errors})

    def add_source(self, source: SourceMetadata) -> "ResearchState":
        """Add a source to the log."""
        new_sources = self.source_log + [source]
        return self.model_copy(update={"source_log": new_sources})

    def increment_feedback_loop(self) -> "ResearchState":
        """Increment the feedback loop counter."""
        new_count = min(self.feedback_loop_count + 1, MAX_FEEDBACK_LOOPS)
        return self.model_copy(update={"feedback_loop_count": new_count})

    def is_max_feedback_reached(self) -> bool:
        """Check if maximum feedback loops reached."""
        return self.feedback_loop_count >= MAX_FEEDBACK_LOOPS

    def get_state_size_bytes(self) -> int:
        """
        Estimate the memory size of the state (GR-005: Memory monitoring).

        Returns:
            Approximate size in bytes
        """
        import sys

        return sys.getsizeof(self.model_dump_json())

    def cleanup_transient_data(self) -> "ResearchState":
        """
        Clean up transient data to reduce memory usage (GR-005).

        Returns:
            State with cleaned up transient data
        """
        trimmed_messages = (
            self.messages[-10:] if len(self.messages) > 10 else self.messages
        )

        return self.model_copy(
            update={
                "messages": trimmed_messages,
                "raw_data": [],  # Clear raw data after processing
            }
        )

    # =============================================================================
    # Typed Model Accessors (Issue #053 - Replace Dict[str, Any])
    # =============================================================================

    def get_typed_financial_data(self) -> FinancialData:
        """
        Get financial_data as a typed FinancialData model.

        Provides type safety and IDE autocompletion for financial data access.
        """
        return FinancialData.from_dict(self.financial_data)

    def get_typed_market_data(self) -> MarketData:
        """
        Get market_data as a typed MarketData model.

        Provides type safety and IDE autocompletion for market data access.
        """
        return MarketData.from_dict(self.market_data)

    def get_typed_competitor_data(self) -> CompetitorData:
        """
        Get competitor_data as a typed CompetitorData model.

        Provides type safety and IDE autocompletion for competitor data access.
        """
        return CompetitorData.from_dict(self.competitor_data)

    def get_typed_brand_data(self) -> BrandData:
        """
        Get brand_data as a typed BrandData model.

        Provides type safety and IDE autocompletion for brand data access.
        """
        return BrandData.from_dict(self.brand_data)

    def get_typed_sales_data(self) -> SalesData:
        """
        Get sales_data as a typed SalesData model.

        Provides type safety and IDE autocompletion for sales data access.
        """
        return SalesData.from_dict(self.sales_data)

    def get_typed_research_context(self) -> TypedResearchContext:
        """
        Get all research data as a TypedResearchContext.

        This is the recommended way to access research data for type safety.
        Replaces accessing individual Dict[str, Any] fields.

        Example:
            ctx = state.get_typed_research_context()
            revenue = ctx.financial_data.revenue  # IDE autocomplete works!
        """
        # Convert raw_data to ResearchSource objects
        sources = []
        for item in self.raw_data:
            url = item.get("url")
            content = item.get("content")
            if url and content:
                sources.append(
                    ResearchSource(
                        url=url,
                        title=item.get("source", "Unknown Source"),
                        content=content,
                        source_type="web",
                        metadata=item.get("metadata", {}),
                    )
                )

        return TypedResearchContext.from_state_dicts(
            financial=self.financial_data,
            market=self.market_data,
            competitor=self.competitor_data,
            brand=self.brand_data,
            sales=self.sales_data,
            sources=sources,
        )

    def set_typed_financial_data(self, data: FinancialData) -> "ResearchState":
        """Update financial_data from a typed model."""
        return self.model_copy(update={"financial_data": data.to_legacy_dict()})

    def set_typed_market_data(self, data: MarketData) -> "ResearchState":
        """Update market_data from a typed model."""
        return self.model_copy(update={"market_data": data.to_legacy_dict()})

    def set_typed_competitor_data(self, data: CompetitorData) -> "ResearchState":
        """Update competitor_data from a typed model."""
        return self.model_copy(update={"competitor_data": data.to_legacy_dict()})

    def set_typed_brand_data(self, data: BrandData) -> "ResearchState":
        """Update brand_data from a typed model."""
        return self.model_copy(update={"brand_data": data.to_legacy_dict()})

    def set_typed_sales_data(self, data: SalesData) -> "ResearchState":
        """Update sales_data from a typed model."""
        return self.model_copy(update={"sales_data": data.to_legacy_dict()})

    # =============================================================================
    # Schema Validation (GR-014)
    # =============================================================================

    def validate_schema(self, schema: Optional[StateSchema] = None) -> List[StateError]:
        """
        Validate this state against a schema (GR-014).

        Args:
            schema: Schema to validate against (uses global if None)

        Returns:
            List of validation errors (empty if valid)
        """
        if schema is None:
            schema = get_state_schema()
        return schema.validate(self.model_dump())

    def is_valid(self, schema: Optional[StateSchema] = None) -> bool:
        """Check if state is valid against schema."""
        return len(self.validate_schema(schema)) == 0

    # =============================================================================
    # Lifecycle Hooks Integration (GR-017)
    # =============================================================================

    def _call_hooks_safely(
        self,
        hook_list: List[Callable],
        hooks: LifecycleHooks,
        phase: str,
        *args,
    ) -> None:
        """Call hooks with error handling."""
        for hook in hook_list:
            try:
                hook(*args)
            except Exception as e:
                error = StateError(
                    code=StateErrorCode.HOOK_ERROR,
                    message=f"Hook failed: {e}",
                    phase=phase,
                )
                for error_hook in hooks.on_validation_error:
                    error_hook(error)

    def _get_valid_transitions_str(self) -> List[str]:
        """Get valid transitions as strings."""
        config = get_transition_config()
        try:
            current = ResearchPhase(self.current_wave)
            valid = config.get_valid_transitions(current)
            return [p.value for p in valid]
        except ValueError:
            return []

    def transition_to_with_hooks(self, new_phase: ResearchPhase) -> "ResearchState":
        """
        Transition to a new phase with lifecycle hooks (GR-017).

        Calls before/after hooks and handles errors via hooks.

        Args:
            new_phase: Target phase

        Returns:
            New state with updated phase

        Raises:
            StateTransitionError: If transition is invalid
        """
        hooks = get_lifecycle_hooks()

        # Call before hooks
        self._call_hooks_safely(
            hooks.on_before_transition, hooks, self.current_wave, self, None
        )

        # Perform transition
        if not self.can_transition_to(new_phase):
            error = StateError(
                code=StateErrorCode.TRANSITION_ERROR,
                message=f"Invalid phase transition: {self.current_wave} -> {new_phase.value}",
                details={"valid_transitions": self._get_valid_transitions_str()},
                phase=self.current_wave,
                recoverable=False,
            )
            for error_hook in hooks.on_validation_error:
                error_hook(error)
            raise StateTransitionError(error)

        new_state = self.model_copy(update={"current_wave": new_phase.value})

        # Call after hooks
        self._call_hooks_safely(
            hooks.on_after_transition, hooks, new_phase.value, self, new_state
        )

        return new_state


# =============================================================================
# State Validation Decorator (GR-001)
# =============================================================================


def validate_state_transition(func):
    """
    Decorator to validate state before and after node execution.

    Ensures state consistency and catches validation errors.
    """

    @wraps(func)
    async def wrapper(state_dict: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        # Validate input state
        try:
            ResearchState(**state_dict)
        except Exception as e:
            return {
                **state_dict,
                "errors": state_dict.get("errors", [])
                + [f"Input state validation failed: {e}"],
                "current_wave": ResearchPhase.ERROR.value,
            }

        # Execute the node
        try:
            result = await func(state_dict, *args, **kwargs)
        except Exception as e:
            return {
                **state_dict,
                "errors": state_dict.get("errors", [])
                + [f"Node execution failed: {e}"],
            }

        # Merge and validate output state
        try:
            merged = {**state_dict, **result}
            output_state = ResearchState(**merged)
            return output_state.model_dump()
        except Exception as e:
            return {
                **state_dict,
                **result,
                "errors": state_dict.get("errors", [])
                + [f"Output state validation failed: {e}"],
            }

    return wrapper
