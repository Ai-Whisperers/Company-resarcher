"""
Stage - The unit of work in a pipeline.

A Stage is a single step that:
1. Takes typed input
2. Produces typed output (wrapped in Result)
3. Reports whether errors are retryable
4. Has no global dependencies (uses RequestContext)

This replaces the ad-hoc agent pattern with explicit contracts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

from ..core.result import Result, Ok, Err

from .context import RequestContext

# Type variables for stage generics
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


# =============================================================================
# Stage Error Types
# =============================================================================


class StageErrorCode(str, Enum):
    """Standard error codes for stage failures."""

    # Control flow errors
    CANCELLED = "STAGE_CANCELLED"
    TIMEOUT = "STAGE_TIMEOUT"
    TIMEOUT_BUDGET_EXHAUSTED = "STAGE_TIMEOUT_BUDGET_EXHAUSTED"

    # Input/validation errors
    INVALID_INPUT = "STAGE_INVALID_INPUT"
    MISSING_DATA = "STAGE_MISSING_DATA"

    # External service errors
    AI_ERROR = "STAGE_AI_ERROR"
    SEARCH_ERROR = "STAGE_SEARCH_ERROR"
    BROWSER_ERROR = "STAGE_BROWSER_ERROR"
    NETWORK_ERROR = "STAGE_NETWORK_ERROR"

    # Processing errors
    PARSE_ERROR = "STAGE_PARSE_ERROR"
    TRANSFORM_ERROR = "STAGE_TRANSFORM_ERROR"

    # Generic
    INTERNAL_ERROR = "STAGE_INTERNAL_ERROR"
    PARTIAL_FAILURE = "STAGE_PARTIAL_FAILURE"


@dataclass(frozen=True)
class StageError:
    """
    Structured error from a stage execution.

    Attributes:
        code: Error code from StageErrorCode enum
        message: Human-readable error message
        stage_name: Name of the stage that failed
        details: Additional error context
        retryable: Whether the error is transient (retry may succeed)
        partial_result: Any partial data recovered before failure
    """

    code: StageErrorCode
    message: str
    stage_name: str = ""
    details: Optional[Dict[str, Any]] = None
    retryable: bool = False
    partial_result: Optional[Any] = None

    # Factory methods for common errors

    @classmethod
    def cancelled(
        cls, stage_name: str = "", reason: str = "Operation cancelled"
    ) -> "StageError":
        return cls(
            code=StageErrorCode.CANCELLED,
            message=reason,
            stage_name=stage_name,
            retryable=False,
        )

    @classmethod
    def timeout(
        cls, stage_name: str = "", message: str = "Operation timed out"
    ) -> "StageError":
        return cls(
            code=StageErrorCode.TIMEOUT,
            message=message,
            stage_name=stage_name,
            retryable=True,  # Timeouts are often transient
        )

    @classmethod
    def timeout_budget_exhausted(cls, stage_name: str = "") -> "StageError":
        return cls(
            code=StageErrorCode.TIMEOUT_BUDGET_EXHAUSTED,
            message="Request timeout budget exhausted",
            stage_name=stage_name,
            retryable=False,  # No point retrying if no time left
        )

    @classmethod
    def invalid_input(
        cls,
        stage_name: str = "",
        message: str = "Invalid input",
        details: Optional[Dict[str, Any]] = None,
    ) -> "StageError":
        return cls(
            code=StageErrorCode.INVALID_INPUT,
            message=message,
            stage_name=stage_name,
            details=details,
            retryable=False,
        )

    @classmethod
    def ai_error(
        cls,
        stage_name: str = "",
        message: str = "AI service error",
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> "StageError":
        return cls(
            code=StageErrorCode.AI_ERROR,
            message=message,
            stage_name=stage_name,
            details=details,
            retryable=retryable,
        )

    @classmethod
    def search_error(
        cls,
        stage_name: str = "",
        message: str = "Search failed",
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> "StageError":
        return cls(
            code=StageErrorCode.SEARCH_ERROR,
            message=message,
            stage_name=stage_name,
            details=details,
            retryable=retryable,
        )

    @classmethod
    def parse_error(
        cls,
        stage_name: str = "",
        message: str = "Failed to parse response",
        raw_output: Optional[str] = None,
    ) -> "StageError":
        return cls(
            code=StageErrorCode.PARSE_ERROR,
            message=message,
            stage_name=stage_name,
            details={"raw_output": raw_output} if raw_output else None,
            retryable=False,
        )

    @classmethod
    def partial_failure(
        cls,
        stage_name: str = "",
        message: str = "Partial failure",
        partial_result: Any = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> "StageError":
        return cls(
            code=StageErrorCode.PARTIAL_FAILURE,
            message=message,
            stage_name=stage_name,
            details=details,
            retryable=False,
            partial_result=partial_result,
        )

    @classmethod
    def internal(
        cls,
        stage_name: str = "",
        message: str = "Internal error",
        exception: Optional[Exception] = None,
    ) -> "StageError":
        details = None
        if exception:
            details = {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
            }
        return cls(
            code=StageErrorCode.INTERNAL_ERROR,
            message=message,
            stage_name=stage_name,
            details=details,
            retryable=False,
        )

    def with_stage_name(self, stage_name: str) -> "StageError":
        """Return a copy with the stage name set."""
        return StageError(
            code=self.code,
            message=self.message,
            stage_name=stage_name,
            details=self.details,
            retryable=self.retryable,
            partial_result=self.partial_result,
        )

    def __str__(self) -> str:
        prefix = f"[{self.stage_name}] " if self.stage_name else ""
        return f"{prefix}[{self.code.value}] {self.message}"


# =============================================================================
# Stage Result
# =============================================================================


@dataclass
class StageResult(Generic[TOutput]):
    """
    Result of a successful stage execution.

    Includes metadata for observability and debugging.
    """

    stage_name: str
    output: TOutput
    started_at: datetime
    completed_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Time taken to execute the stage."""
        return (self.completed_at - self.started_at).total_seconds()


# =============================================================================
# Stage Protocol
# =============================================================================


class Stage(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for pipeline stages.

    A stage is a single unit of work that transforms typed input to typed output.
    Stages use RequestContext for all dependencies (no global imports).

    Type Parameters:
        TInput: The input type for this stage
        TOutput: The output type for this stage

    Example:
        class SearchStage(Stage[SearchInput, SearchOutput]):
            name = "search"

            async def execute(
                self, input: SearchInput, ctx: RequestContext
            ) -> Result[SearchOutput, StageError]:
                # Use ctx for all dependencies
                results = await ctx.search_tool.search_safe(input.query)
                ...
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this stage (used in logging and checkpoints)."""
        ...

    @abstractmethod
    async def execute(
        self,
        input: TInput,
        ctx: RequestContext,
    ) -> Result[TOutput, StageError]:
        """
        Execute the stage logic.

        Args:
            input: Typed input for this stage
            ctx: Request context with all dependencies

        Returns:
            Ok(output) on success, Err(StageError) on failure

        Important:
            - Check ctx.cancellation.is_cancelled periodically
            - Check ctx.timeout_budget.has_time_remaining() before long ops
            - Use ctx.logger for all logging
            - Never import global singletons - use ctx services
        """
        ...

    def can_retry(self, error: StageError) -> bool:
        """
        Determine if this error should be retried.

        Override to customize retry behavior for specific error types.

        Args:
            error: The error that occurred

        Returns:
            True if the operation should be retried
        """
        return error.retryable

    def validate_input(self, input: TInput) -> Optional[StageError]:
        """
        Validate input before execution.

        Override to add input validation. Return StageError if invalid.

        Args:
            input: The input to validate

        Returns:
            None if valid, StageError if invalid
        """
        return None

    async def run(
        self,
        input: TInput,
        ctx: RequestContext,
    ) -> Result[StageResult[TOutput], StageError]:
        """
        Run the stage with timing and error handling.

        This is the main entry point called by the Pipeline.
        It wraps execute() with validation, timing, and error handling.

        Args:
            input: Typed input for this stage
            ctx: Request context

        Returns:
            Ok(StageResult) on success, Err(StageError) on failure
        """
        stage_ctx = ctx.with_stage(self.name)

        # Check if we can continue
        stop_reason = stage_ctx.check_can_continue()
        if stop_reason:
            return Err(
                StageError.cancelled(self.name, stop_reason)
                if "Cancel" in stop_reason
                else StageError.timeout_budget_exhausted(self.name)
            )

        # Validate input
        validation_error = self.validate_input(input)
        if validation_error:
            return Err(validation_error.with_stage_name(self.name))

        # Execute with timing
        started_at = datetime.utcnow()
        stage_ctx.logger.info("Starting stage")

        try:
            result = await self.execute(input, stage_ctx)
        except Exception as e:
            stage_ctx.logger.exception(f"Stage raised exception: {e}")
            return Err(StageError.internal(self.name, str(e), e))

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        if result.is_ok:
            stage_ctx.logger.info(f"Stage completed", duration=f"{duration:.2f}s")
            return Ok(
                StageResult(
                    stage_name=self.name,
                    output=result.unwrap(),
                    started_at=started_at,
                    completed_at=completed_at,
                )
            )
        else:
            error = result.unwrap_err().with_stage_name(self.name)
            stage_ctx.logger.warning(
                f"Stage failed: {error.message}",
                error_code=error.code.value,
                duration=f"{duration:.2f}s",
            )
            return Err(error)


# =============================================================================
# Composite Stage
# =============================================================================


class CompositeStage(Stage[TInput, TOutput]):
    """
    A stage that runs multiple sub-stages in sequence.

    Useful for grouping related stages into a logical unit.
    """

    def __init__(
        self,
        name: str,
        stages: List[Stage],
    ):
        self._name = name
        self._stages = stages

    @property
    def name(self) -> str:
        return self._name

    async def execute(
        self,
        input: TInput,
        ctx: RequestContext,
    ) -> Result[TOutput, StageError]:
        current = input

        for stage in self._stages:
            result = await stage.run(current, ctx)

            if result.is_err:
                return Err(result.unwrap_err())

            current = result.unwrap().output

        return Ok(current)


# =============================================================================
# Parallel Stage
# =============================================================================


class ParallelStage(Stage[TInput, List[Any]]):
    """
    A stage that runs multiple sub-stages in parallel.

    Collects results from all stages, with configurable failure behavior.
    """

    def __init__(
        self,
        name: str,
        stages: List[Stage[TInput, Any]],
        fail_fast: bool = False,
    ):
        self._name = name
        self._stages = stages
        self._fail_fast = fail_fast

    @property
    def name(self) -> str:
        return self._name

    async def execute(
        self,
        input: TInput,
        ctx: RequestContext,
    ) -> Result[List[Any], StageError]:
        import asyncio

        tasks = [stage.run(input, ctx) for stage in self._stages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs = []
        errors = []

        for i, result in enumerate(results):
            stage_name = self._stages[i].name

            if isinstance(result, Exception):
                errors.append(
                    StageError.internal(stage_name, str(result), result)
                )
            elif result.is_ok:
                outputs.append(result.unwrap().output)
            else:
                errors.append(result.unwrap_err())

        if errors and (self._fail_fast or len(errors) == len(self._stages)):
            return Err(
                StageError.partial_failure(
                    self.name,
                    f"{len(errors)} of {len(self._stages)} parallel stages failed",
                    partial_result=outputs if outputs else None,
                    details={"errors": [str(e) for e in errors]},
                )
            )

        return Ok(outputs)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "StageErrorCode",
    "StageError",
    "StageResult",
    "Stage",
    "CompositeStage",
    "ParallelStage",
]
