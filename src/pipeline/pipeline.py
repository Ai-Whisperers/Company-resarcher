"""
Pipeline - Executes stages in sequence with error handling and recovery.

The Pipeline is the orchestrator that:
1. Runs stages in sequence
2. Handles retries with exponential backoff
3. Checkpoints progress for recovery
4. Tracks metrics and timing
5. Supports cancellation and timeout budgets
"""

from __future__ import annotations

import asyncio
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

from src.core.result import Result, Err

from .context import RequestContext, create_context
from .stage import Stage, StageResult, StageError

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


# =============================================================================
# Pipeline Configuration
# =============================================================================


@dataclass
class PipelineConfig:
    """
    Configuration for pipeline execution.

    Attributes:
        max_retries: Maximum retry attempts per stage (default 3)
        retry_base_delay: Base delay for exponential backoff in seconds (default 1.0)
        retry_max_delay: Maximum delay between retries in seconds (default 30.0)
        timeout_seconds: Total timeout for the pipeline (default 300.0)
        fail_fast: Stop on first stage failure (default True)
        checkpoint_enabled: Enable checkpointing for recovery (default True)
    """

    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    timeout_seconds: float = 300.0
    fail_fast: bool = True
    checkpoint_enabled: bool = True


# =============================================================================
# Pipeline Result
# =============================================================================


class PipelineStatus(str, Enum):
    """Status of pipeline execution."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class PipelineResult(Generic[TOutput]):
    """
    Result of pipeline execution.

    Contains the final output (if successful), all completed stage results,
    and information about any failures.

    Attributes:
        status: Overall pipeline status
        output: Final output (if successful)
        completed_stages: Results from all completed stages
        failed_stage: Name of the stage that failed (if any)
        error: Error from the failed stage (if any)
        started_at: When pipeline execution started
        completed_at: When pipeline execution completed
        request_id: Request ID for tracing
        can_resume: Whether execution can be resumed from checkpoint
    """

    status: PipelineStatus
    output: Optional[TOutput] = None
    completed_stages: List[StageResult] = field(default_factory=list)
    failed_stage: Optional[str] = None
    error: Optional[StageError] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request_id: str = ""
    can_resume: bool = False

    @property
    def is_success(self) -> bool:
        """Check if pipeline completed successfully."""
        return self.status == PipelineStatus.SUCCESS

    @property
    def is_partial_success(self) -> bool:
        """Check if pipeline had partial success."""
        return self.status == PipelineStatus.PARTIAL_SUCCESS

    @property
    def duration_seconds(self) -> Optional[float]:
        """Total execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def get_stage_output(self, stage_name: str) -> Optional[Any]:
        """Get output from a specific stage."""
        for stage_result in self.completed_stages:
            if stage_result.stage_name == stage_name:
                return stage_result.output
        return None


# =============================================================================
# Checkpoint
# =============================================================================


@dataclass
class Checkpoint:
    """
    Checkpoint for resuming pipeline execution.

    Stores the state after each successful stage so execution
    can be resumed from the last good state.
    """

    request_id: str
    completed_stages: List[str]
    stage_outputs: Dict[str, Any]
    last_input: Any
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_resume_stage_index(self, stage_names: List[str]) -> int:
        """Get the index of the next stage to execute."""
        for i, name in enumerate(stage_names):
            if name not in self.completed_stages:
                return i
        return len(stage_names)  # All done


# =============================================================================
# Pipeline
# =============================================================================


class Pipeline(Generic[TInput, TOutput]):
    """
    Executes a sequence of stages with error handling and recovery.

    The Pipeline orchestrates stage execution, handling:
    - Sequential execution with typed data flow
    - Retry logic with exponential backoff
    - Checkpointing for recovery
    - Timeout budget enforcement
    - Cancellation support
    - Comprehensive logging and metrics

    Example:
        pipeline = Pipeline([
            SearchStage(),
            AnalyzeStage(),
            WriteStage(),
        ])

        ctx = create_context(request_id="req-123")
        result = await pipeline.execute(search_input, ctx)

        if result.is_success:
            report = result.output
        else:
            print(f"Failed: {result.error}")

        # Resume from checkpoint
        if result.can_resume:
            result = await pipeline.resume(checkpoint, ctx)
    """

    def __init__(
        self,
        stages: List[Stage],
        config: Optional[PipelineConfig] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            stages: List of stages to execute in order
            config: Pipeline configuration (uses defaults if not provided)
        """
        self.stages = stages
        self.config = config or PipelineConfig()
        self._checkpoints: Dict[str, Checkpoint] = {}

    @property
    def stage_names(self) -> List[str]:
        """Get list of stage names in order."""
        return [stage.name for stage in self.stages]

    async def execute(
        self,
        input: TInput,
        ctx: Optional[RequestContext] = None,
    ) -> PipelineResult[TOutput]:
        """
        Execute the pipeline from the beginning.

        Args:
            input: Initial input for the first stage
            ctx: Request context (created if not provided)

        Returns:
            PipelineResult with status, output, and metadata
        """
        # Create context if not provided
        if ctx is None:
            ctx = create_context(timeout_seconds=self.config.timeout_seconds)

        started_at = datetime.utcnow()
        ctx.logger.info(
            f"Starting pipeline",
            stages=len(self.stages),
            timeout=f"{self.config.timeout_seconds}s",
        )

        # Run stages
        result = await self._run_stages(input, ctx, start_index=0)

        result.started_at = started_at
        result.completed_at = datetime.utcnow()
        result.request_id = ctx.request_id

        ctx.logger.info(
            f"Pipeline completed",
            status=result.status.value,
            duration=f"{result.duration_seconds:.2f}s",
            completed_stages=len(result.completed_stages),
        )

        return result

    async def resume(
        self,
        checkpoint: Checkpoint,
        ctx: Optional[RequestContext] = None,
    ) -> PipelineResult[TOutput]:
        """
        Resume pipeline execution from a checkpoint.

        Args:
            checkpoint: Checkpoint to resume from
            ctx: Request context (created if not provided)

        Returns:
            PipelineResult with status, output, and metadata
        """
        if ctx is None:
            ctx = create_context(
                request_id=checkpoint.request_id,
                timeout_seconds=self.config.timeout_seconds,
            )

        started_at = datetime.utcnow()
        start_index = checkpoint.get_resume_stage_index(self.stage_names)

        ctx.logger.info(
            f"Resuming pipeline from stage {start_index}",
            checkpoint_stages=len(checkpoint.completed_stages),
        )

        # Restore completed stages
        completed_stages = []
        for stage_name in checkpoint.completed_stages:
            if stage_name in checkpoint.stage_outputs:
                completed_stages.append(
                    StageResult(
                        stage_name=stage_name,
                        output=checkpoint.stage_outputs[stage_name],
                        started_at=checkpoint.created_at,
                        completed_at=checkpoint.created_at,
                        metadata={"restored_from_checkpoint": True},
                    )
                )

        # Run remaining stages
        result = await self._run_stages(
            checkpoint.last_input,
            ctx,
            start_index=start_index,
            completed_stages=completed_stages,
        )

        result.started_at = started_at
        result.completed_at = datetime.utcnow()
        result.request_id = ctx.request_id

        return result

    async def _run_stages(
        self,
        initial_input: Any,
        ctx: RequestContext,
        start_index: int = 0,
        completed_stages: Optional[List[StageResult]] = None,
    ) -> PipelineResult[TOutput]:
        """
        Run stages starting from a given index.

        Args:
            initial_input: Input for the first stage to run
            ctx: Request context
            start_index: Index of first stage to run
            completed_stages: Already completed stages (for resume)

        Returns:
            PipelineResult
        """
        completed = completed_stages or []
        current_input = initial_input

        for i in range(start_index, len(self.stages)):
            stage = self.stages[i]

            # Check cancellation
            if ctx.cancellation.is_cancelled:
                return PipelineResult(
                    status=PipelineStatus.CANCELLED,
                    completed_stages=completed,
                    failed_stage=stage.name,
                    error=StageError.cancelled(stage.name, ctx.cancellation.reason),
                    can_resume=self.config.checkpoint_enabled,
                )

            # Check timeout budget
            if ctx.timeout_budget.is_exhausted():
                return PipelineResult(
                    status=PipelineStatus.TIMEOUT,
                    completed_stages=completed,
                    failed_stage=stage.name,
                    error=StageError.timeout_budget_exhausted(stage.name),
                    can_resume=self.config.checkpoint_enabled,
                )

            # Execute stage with retry
            result = await self._execute_with_retry(stage, current_input, ctx)

            if result.is_ok:
                stage_result = result.unwrap()
                completed.append(stage_result)
                current_input = stage_result.output

                # Save checkpoint
                if self.config.checkpoint_enabled:
                    self._save_checkpoint(ctx.request_id, completed, current_input)
            else:
                error = result.unwrap_err()

                # Determine if we have partial success
                if completed and not self.config.fail_fast:
                    return PipelineResult(
                        status=PipelineStatus.PARTIAL_SUCCESS,
                        output=completed[-1].output if completed else None,
                        completed_stages=completed,
                        failed_stage=stage.name,
                        error=error,
                        can_resume=self.config.checkpoint_enabled and error.retryable,
                    )

                return PipelineResult(
                    status=PipelineStatus.FAILED,
                    completed_stages=completed,
                    failed_stage=stage.name,
                    error=error,
                    can_resume=self.config.checkpoint_enabled and error.retryable,
                )

        # All stages completed successfully
        return PipelineResult(
            status=PipelineStatus.SUCCESS,
            output=current_input,
            completed_stages=completed,
        )

    async def _execute_with_retry(
        self,
        stage: Stage,
        input: Any,
        ctx: RequestContext,
    ) -> Result[StageResult, StageError]:
        """
        Execute a stage with retry logic.

        Args:
            stage: Stage to execute
            input: Input for the stage
            ctx: Request context

        Returns:
            Result with StageResult or StageError
        """
        last_error: Optional[StageError] = None

        for attempt in range(self.config.max_retries + 1):
            if attempt > 0:
                ctx.logger.info(
                    f"Retrying stage",
                    stage=stage.name,
                    attempt=attempt + 1,
                    max_attempts=self.config.max_retries + 1,
                )

            result = await stage.run(input, ctx)

            if result.is_ok:
                return result

            last_error = result.unwrap_err()

            # Check if we should retry
            if not stage.can_retry(last_error):
                ctx.logger.warning(
                    f"Stage error is not retryable",
                    stage=stage.name,
                    error_code=last_error.code.value,
                )
                return Err(last_error)

            # Check if we have retries left
            if attempt >= self.config.max_retries:
                ctx.logger.warning(
                    f"Stage exhausted all retries",
                    stage=stage.name,
                    attempts=attempt + 1,
                )
                return Err(last_error)

            # Check cancellation before retry delay
            if ctx.cancellation.is_cancelled:
                return Err(
                    StageError.cancelled(stage.name, ctx.cancellation.reason)
                )

            # Exponential backoff
            delay = min(
                self.config.retry_base_delay * (2 ** attempt),
                self.config.retry_max_delay,
            )

            # Don't wait longer than remaining budget
            delay = min(delay, ctx.timeout_budget.remaining() - 1)
            if delay <= 0:
                return Err(StageError.timeout_budget_exhausted(stage.name))

            ctx.logger.info(f"Waiting before retry", delay=f"{delay:.1f}s")
            await asyncio.sleep(delay)

        # Should not reach here, but just in case
        return Err(last_error or StageError.internal(stage.name, "Unknown error"))

    def _save_checkpoint(
        self,
        request_id: str,
        completed: List[StageResult],
        last_input: Any,
    ) -> None:
        """Save a checkpoint for potential resume."""
        self._checkpoints[request_id] = Checkpoint(
            request_id=request_id,
            completed_stages=[s.stage_name for s in completed],
            stage_outputs={s.stage_name: s.output for s in completed},
            last_input=last_input,
        )

    def get_checkpoint(self, request_id: str) -> Optional[Checkpoint]:
        """Get a saved checkpoint by request ID."""
        return self._checkpoints.get(request_id)

    def clear_checkpoint(self, request_id: str) -> None:
        """Clear a saved checkpoint."""
        self._checkpoints.pop(request_id, None)


# =============================================================================
# Pipeline Builder
# =============================================================================


class PipelineBuilder(Generic[TInput, TOutput]):
    """
    Fluent builder for creating pipelines.

    Example:
        pipeline = (
            PipelineBuilder()
            .add(SearchStage())
            .add(AnalyzeStage())
            .add(WriteStage())
            .with_config(PipelineConfig(max_retries=5))
            .build()
        )
    """

    def __init__(self):
        self._stages: List[Stage] = []
        self._config: Optional[PipelineConfig] = None

    def add(self, stage: Stage) -> "PipelineBuilder[TInput, TOutput]":
        """Add a stage to the pipeline."""
        self._stages.append(stage)
        return self

    def with_config(self, config: PipelineConfig) -> "PipelineBuilder[TInput, TOutput]":
        """Set the pipeline configuration."""
        self._config = config
        return self

    def with_retries(self, max_retries: int) -> "PipelineBuilder[TInput, TOutput]":
        """Set the maximum retry count."""
        if self._config is None:
            self._config = PipelineConfig()
        self._config.max_retries = max_retries
        return self

    def with_timeout(self, seconds: float) -> "PipelineBuilder[TInput, TOutput]":
        """Set the timeout in seconds."""
        if self._config is None:
            self._config = PipelineConfig()
        self._config.timeout_seconds = seconds
        return self

    def build(self) -> Pipeline[TInput, TOutput]:
        """Build the pipeline."""
        return Pipeline(self._stages, self._config)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PipelineConfig",
    "PipelineStatus",
    "PipelineResult",
    "Checkpoint",
    "Pipeline",
    "PipelineBuilder",
]
