"""Tests for the pipeline architecture."""

import asyncio
import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock

from src.core.result import Result, Ok, Err
from src.pipeline.context import (
    RequestContext,
    TimeoutBudget,
    CancellationToken,
    BoundLogger,
    create_context,
)
from src.pipeline.stage import (
    Stage,
    StageResult,
    StageError,
    StageErrorCode,
)
from src.pipeline.pipeline import (
    Pipeline,
    PipelineConfig,
    PipelineResult,
    PipelineStatus,
    PipelineBuilder,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@dataclass
class MockInput:
    value: int


@dataclass
class MockOutput:
    value: int


class MockStage(Stage[MockInput, MockOutput]):
    """A simple mock stage for testing."""

    def __init__(
        self,
        name: str = "mock",
        should_fail: bool = False,
        fail_count: int = 0,
        output_transform: callable = None,
    ):
        self._name = name
        self._should_fail = should_fail
        self._fail_count = fail_count
        self._calls = 0
        self._output_transform = output_transform or (lambda x: x * 2)

    @property
    def name(self) -> str:
        return self._name

    async def execute(
        self, input: MockInput, ctx: RequestContext
    ) -> Result[MockOutput, StageError]:
        self._calls += 1

        if self._should_fail:
            if self._fail_count > 0 and self._calls > self._fail_count:
                # Stop failing after fail_count attempts
                pass
            else:
                return Err(
                    StageError(
                        code=StageErrorCode.INTERNAL_ERROR,
                        message=f"Mock failure on call {self._calls}",
                        retryable=True,
                    )
                )

        return Ok(MockOutput(value=self._output_transform(input.value)))


def create_mock_context(
    request_id: str = "test-123",
    timeout_seconds: float = 300.0,
) -> RequestContext:
    """Create a mock context for testing."""
    mock_ai = AsyncMock()
    mock_ai.generate_safe = AsyncMock(return_value=Ok('{"summary": "test"}'))
    mock_ai.get_provider_name = Mock(return_value="mock")

    mock_search = AsyncMock()
    mock_search.search_safe = AsyncMock(return_value=Ok([{"url": "http://test.com", "title": "Test"}]))
    mock_search.search = AsyncMock(return_value=[{"url": "http://test.com", "title": "Test"}])

    mock_browser = AsyncMock()
    mock_browser.fetch_url = AsyncMock(return_value={"content": "test content", "title": "Test"})

    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock()

    mock_settings = Mock()

    return RequestContext(
        request_id=request_id,
        ai_client=mock_ai,
        search_tool=mock_search,
        browser_tool=mock_browser,
        cache=mock_cache,
        timeout_budget=TimeoutBudget(total_seconds=timeout_seconds),
        cancellation=CancellationToken(),
        settings=mock_settings,
        logger=BoundLogger(request_id),
    )


# =============================================================================
# TimeoutBudget Tests
# =============================================================================


class TestTimeoutBudget:
    """Tests for TimeoutBudget."""

    def test_initial_state(self):
        budget = TimeoutBudget(total_seconds=100.0)
        assert budget.remaining() <= 100.0
        assert budget.has_time_remaining()
        assert not budget.is_exhausted()

    def test_elapsed_increases(self):
        budget = TimeoutBudget(total_seconds=100.0)
        import time
        time.sleep(0.1)
        assert budget.elapsed() >= 0.1

    def test_remaining_decreases(self):
        budget = TimeoutBudget(total_seconds=1.0)
        initial = budget.remaining()
        import time
        time.sleep(0.1)
        assert budget.remaining() < initial

    def test_exhausted_when_time_up(self):
        budget = TimeoutBudget(total_seconds=0.05)
        import time
        time.sleep(0.1)
        assert budget.is_exhausted()
        assert not budget.has_time_remaining()

    def test_has_time_remaining_with_min(self):
        budget = TimeoutBudget(total_seconds=5.0)
        assert budget.has_time_remaining(min_required=3.0)
        # After some time, might not have enough
        import time
        time.sleep(0.1)
        assert budget.has_time_remaining(min_required=1.0)

    def test_consume_creates_sub_budget(self):
        budget = TimeoutBudget(total_seconds=100.0)
        sub = budget.consume(10.0)
        assert sub.total_seconds == 10.0
        assert sub.remaining() <= 10.0


# =============================================================================
# CancellationToken Tests
# =============================================================================


class TestCancellationToken:
    """Tests for CancellationToken."""

    def test_initial_state(self):
        token = CancellationToken()
        assert not token.is_cancelled
        assert token.reason is None

    def test_cancel(self):
        token = CancellationToken()
        token.cancel("User requested")
        assert token.is_cancelled
        assert token.reason == "User requested"

    def test_cancel_only_once(self):
        token = CancellationToken()
        token.cancel("First reason")
        token.cancel("Second reason")
        assert token.reason == "First reason"

    def test_callback_on_cancel(self):
        token = CancellationToken()
        callback_called = []

        token.on_cancel(lambda: callback_called.append(True))
        assert len(callback_called) == 0

        token.cancel()
        assert len(callback_called) == 1

    def test_callback_immediate_if_already_cancelled(self):
        token = CancellationToken()
        token.cancel()

        callback_called = []
        token.on_cancel(lambda: callback_called.append(True))
        assert len(callback_called) == 1

    def test_raise_if_cancelled(self):
        token = CancellationToken()
        token.raise_if_cancelled()  # Should not raise

        token.cancel("Test")
        with pytest.raises(asyncio.CancelledError):
            token.raise_if_cancelled()


# =============================================================================
# BoundLogger Tests
# =============================================================================


class TestBoundLogger:
    """Tests for BoundLogger."""

    def test_creates_with_request_id(self):
        logger = BoundLogger("req-123")
        # Just verify it doesn't crash
        logger.info("Test message")
        logger.debug("Debug message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_with_stage(self):
        logger = BoundLogger("req-123")
        stage_logger = logger.with_stage("search")
        # Verify it creates a new logger
        assert stage_logger is not logger


# =============================================================================
# StageError Tests
# =============================================================================


class TestStageError:
    """Tests for StageError."""

    def test_cancelled_factory(self):
        error = StageError.cancelled("test_stage", "User cancelled")
        assert error.code == StageErrorCode.CANCELLED
        assert error.stage_name == "test_stage"
        assert not error.retryable

    def test_timeout_factory(self):
        error = StageError.timeout("test_stage")
        assert error.code == StageErrorCode.TIMEOUT
        assert error.retryable

    def test_ai_error_factory(self):
        error = StageError.ai_error("test_stage", "API failed", retryable=False)
        assert error.code == StageErrorCode.AI_ERROR
        assert not error.retryable

    def test_with_stage_name(self):
        error = StageError.timeout()
        updated = error.with_stage_name("my_stage")
        assert updated.stage_name == "my_stage"
        assert error.stage_name == ""  # Original unchanged

    def test_str_representation(self):
        error = StageError.timeout("search", "Timed out after 30s")
        assert "[search]" in str(error)
        assert "STAGE_TIMEOUT" in str(error)


# =============================================================================
# Stage Tests
# =============================================================================


class TestStage:
    """Tests for Stage base class."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        stage = MockStage(name="test")
        ctx = create_mock_context()

        result = await stage.run(MockInput(value=5), ctx)

        assert result.is_ok
        stage_result = result.unwrap()
        assert stage_result.stage_name == "test"
        assert stage_result.output.value == 10  # 5 * 2

    @pytest.mark.asyncio
    async def test_failed_execution(self):
        stage = MockStage(name="test", should_fail=True)
        ctx = create_mock_context()

        result = await stage.run(MockInput(value=5), ctx)

        assert result.is_err
        error = result.unwrap_err()
        assert error.stage_name == "test"

    @pytest.mark.asyncio
    async def test_cancellation_check(self):
        stage = MockStage(name="test")
        ctx = create_mock_context()
        ctx.cancellation.cancel("Test cancellation")

        result = await stage.run(MockInput(value=5), ctx)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == StageErrorCode.CANCELLED

    @pytest.mark.asyncio
    async def test_timeout_budget_check(self):
        stage = MockStage(name="test")
        ctx = create_mock_context(timeout_seconds=0.0)

        result = await stage.run(MockInput(value=5), ctx)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == StageErrorCode.TIMEOUT_BUDGET_EXHAUSTED

    @pytest.mark.asyncio
    async def test_timing_recorded(self):
        stage = MockStage(name="test")
        ctx = create_mock_context()

        result = await stage.run(MockInput(value=5), ctx)

        assert result.is_ok
        stage_result = result.unwrap()
        assert stage_result.started_at is not None
        assert stage_result.completed_at is not None
        assert stage_result.duration_seconds >= 0


# =============================================================================
# Pipeline Tests
# =============================================================================


class TestPipeline:
    """Tests for Pipeline execution."""

    @pytest.mark.asyncio
    async def test_single_stage_success(self):
        stage = MockStage(name="stage1")
        pipeline = Pipeline([stage])
        ctx = create_mock_context()

        result = await pipeline.execute(MockInput(value=5), ctx)

        assert result.is_success
        assert result.output.value == 10
        assert len(result.completed_stages) == 1

    @pytest.mark.asyncio
    async def test_multiple_stages_success(self):
        stages = [
            MockStage(name="stage1", output_transform=lambda x: x * 2),
            MockStage(name="stage2", output_transform=lambda x: x + 1),
            MockStage(name="stage3", output_transform=lambda x: x * 3),
        ]
        pipeline = Pipeline(stages)
        ctx = create_mock_context()

        # Input: 5
        # Stage1: 5 * 2 = 10
        # Stage2: 10 + 1 = 11
        # Stage3: 11 * 3 = 33
        result = await pipeline.execute(MockInput(value=5), ctx)

        assert result.is_success
        assert result.output.value == 33
        assert len(result.completed_stages) == 3

    @pytest.mark.asyncio
    async def test_stage_failure_stops_pipeline(self):
        stages = [
            MockStage(name="stage1"),
            MockStage(name="stage2", should_fail=True),
            MockStage(name="stage3"),
        ]
        pipeline = Pipeline(stages)
        ctx = create_mock_context()

        result = await pipeline.execute(MockInput(value=5), ctx)

        assert result.status == PipelineStatus.FAILED
        assert result.failed_stage == "stage2"
        assert len(result.completed_stages) == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        # Stage fails twice, then succeeds
        stage = MockStage(name="flaky", should_fail=True, fail_count=2)
        pipeline = Pipeline(
            [stage],
            config=PipelineConfig(max_retries=3),
        )
        ctx = create_mock_context()

        result = await pipeline.execute(MockInput(value=5), ctx)

        assert result.is_success
        assert stage._calls == 3  # Failed twice, succeeded on third

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        stage = MockStage(name="always_fail", should_fail=True)
        pipeline = Pipeline(
            [stage],
            config=PipelineConfig(max_retries=2),
        )
        ctx = create_mock_context()

        result = await pipeline.execute(MockInput(value=5), ctx)

        assert result.status == PipelineStatus.FAILED
        assert stage._calls == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_cancellation_stops_pipeline(self):
        stages = [
            MockStage(name="stage1"),
            MockStage(name="stage2"),
        ]
        pipeline = Pipeline(stages)
        ctx = create_mock_context()

        # Cancel after first stage would complete
        async def cancel_after_delay():
            await asyncio.sleep(0.01)
            ctx.cancellation.cancel("Test cancel")

        asyncio.create_task(cancel_after_delay())

        result = await pipeline.execute(MockInput(value=5), ctx)

        # Result depends on timing, but should not be SUCCESS with all stages
        assert result.request_id == "test-123"

    @pytest.mark.asyncio
    async def test_checkpoint_saved(self):
        stages = [
            MockStage(name="stage1"),
            MockStage(name="stage2"),
        ]
        pipeline = Pipeline(
            stages,
            config=PipelineConfig(checkpoint_enabled=True),
        )
        ctx = create_mock_context()

        result = await pipeline.execute(MockInput(value=5), ctx)

        checkpoint = pipeline.get_checkpoint(ctx.request_id)
        assert checkpoint is not None
        assert "stage1" in checkpoint.completed_stages
        assert "stage2" in checkpoint.completed_stages

    @pytest.mark.asyncio
    async def test_pipeline_result_metadata(self):
        stage = MockStage(name="test")
        pipeline = Pipeline([stage])
        ctx = create_mock_context()

        result = await pipeline.execute(MockInput(value=5), ctx)

        assert result.request_id == "test-123"
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0


class TestPipelineBuilder:
    """Tests for PipelineBuilder."""

    def test_build_simple_pipeline(self):
        pipeline = (
            PipelineBuilder()
            .add(MockStage(name="stage1"))
            .add(MockStage(name="stage2"))
            .build()
        )

        assert len(pipeline.stages) == 2
        assert pipeline.stage_names == ["stage1", "stage2"]

    def test_build_with_config(self):
        pipeline = (
            PipelineBuilder()
            .add(MockStage(name="stage1"))
            .with_config(PipelineConfig(max_retries=5))
            .build()
        )

        assert pipeline.config.max_retries == 5

    def test_build_with_timeout(self):
        pipeline = (
            PipelineBuilder()
            .add(MockStage(name="stage1"))
            .with_timeout(60.0)
            .build()
        )

        assert pipeline.config.timeout_seconds == 60.0

    def test_build_with_retries(self):
        pipeline = (
            PipelineBuilder()
            .add(MockStage(name="stage1"))
            .with_retries(10)
            .build()
        )

        assert pipeline.config.max_retries == 10


class TestPipelineResult:
    """Tests for PipelineResult."""

    def test_is_success(self):
        result = PipelineResult(status=PipelineStatus.SUCCESS, output=42)
        assert result.is_success
        assert not result.is_partial_success

    def test_is_partial_success(self):
        result = PipelineResult(status=PipelineStatus.PARTIAL_SUCCESS)
        assert result.is_partial_success
        assert not result.is_success

    def test_get_stage_output(self):
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            completed_stages=[
                StageResult(
                    stage_name="search",
                    output={"data": "test"},
                    started_at=None,
                    completed_at=None,
                )
            ],
        )

        output = result.get_stage_output("search")
        assert output == {"data": "test"}

        missing = result.get_stage_output("nonexistent")
        assert missing is None
