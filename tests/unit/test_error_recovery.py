"""
Unit tests for Error Recovery.

Tests error recovery paths and graceful degradation:
- Retry mechanisms
- Fallback strategies
- Graceful degradation
- Recovery from transient errors
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from typing import List, Any, Optional

from src.core.exceptions.base import (
    CompanyResearcherError,
    AIError,
    AIRateLimitError,
    AITimeoutError,
    NetworkError,
    NetworkTimeoutError,
    SearchError,
    NoResultsError,
    PipelineError,
    StageError,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_operation():
    """Create a mock async operation."""
    return AsyncMock()


@pytest.fixture
def flaky_operation():
    """Create an operation that fails intermittently."""
    call_count = 0

    async def operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise NetworkTimeoutError(url="https://api.example.com", timeout_seconds=30)
        return {"success": True, "attempts": call_count}

    return operation


@pytest.fixture
def always_failing_operation():
    """Create an operation that always fails."""
    async def operation():
        raise AIError("Always fails", provider="test")

    return operation


# =============================================================================
# Retry Mechanism Tests
# =============================================================================


class TestRetryMechanism:
    """Tests for retry mechanisms."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_transient_error(self, flaky_operation):
        """Verify retry succeeds after transient errors."""
        async def retry_with_attempts(operation, max_attempts: int = 3):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await operation()
                except (NetworkTimeoutError, AITimeoutError) as e:
                    last_error = e
                    await asyncio.sleep(0.01)  # Brief delay
            raise last_error

        result = await retry_with_attempts(flaky_operation, max_attempts=5)

        assert result["success"] is True
        assert result["attempts"] == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self, always_failing_operation):
        """Verify retry raises after exhausting attempts."""
        async def retry_with_attempts(operation, max_attempts: int = 3):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await operation()
                except AIError as e:
                    last_error = e
                    await asyncio.sleep(0.01)
            raise last_error

        with pytest.raises(AIError):
            await retry_with_attempts(always_failing_operation, max_attempts=3)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self, mock_operation):
        """Verify exponential backoff between retries."""
        delays = []
        attempt = 0

        async def operation_with_backoff():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise NetworkTimeoutError(url="test", timeout_seconds=10)
            return "success"

        async def retry_with_backoff(operation, max_attempts: int = 3, base_delay: float = 0.01):
            for i in range(max_attempts):
                try:
                    return await operation()
                except NetworkError:
                    if i < max_attempts - 1:
                        delay = base_delay * (2 ** i)
                        delays.append(delay)
                        await asyncio.sleep(delay)
            raise NetworkError("Max retries exceeded")

        result = await retry_with_backoff(operation_with_backoff)

        assert result == "success"
        assert len(delays) == 2
        # Second delay should be larger than first (exponential)
        assert delays[1] > delays[0]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_retry_respects_retry_after(self):
        """Verify retry respects rate limit retry-after headers."""
        retry_after_respected = False

        async def rate_limited_operation():
            nonlocal retry_after_respected
            if not retry_after_respected:
                retry_after_respected = True
                raise AIRateLimitError(provider="openai", retry_after=1)
            return "success"

        async def retry_with_rate_limit(operation):
            try:
                return await operation()
            except AIRateLimitError as e:
                if e.retry_after:
                    await asyncio.sleep(min(e.retry_after, 0.1))  # Cap for test
                return await operation()

        result = await retry_with_rate_limit(rate_limited_operation)
        assert result == "success"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self):
        """Verify non-retryable errors are not retried."""
        attempt_count = 0

        async def validation_failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Invalid input")  # Non-retryable

        async def retry_only_transient(operation, max_attempts: int = 3):
            retryable_errors = (NetworkError, AITimeoutError)
            for attempt in range(max_attempts):
                try:
                    return await operation()
                except retryable_errors:
                    await asyncio.sleep(0.01)
                except Exception:
                    raise  # Don't retry non-transient errors

        with pytest.raises(ValueError):
            await retry_only_transient(validation_failing_operation)

        assert attempt_count == 1  # Only one attempt


# =============================================================================
# Fallback Strategy Tests
# =============================================================================


class TestFallbackStrategies:
    """Tests for fallback strategies."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Verify fallback is used when primary fails."""
        primary_called = False
        fallback_called = False

        async def primary():
            nonlocal primary_called
            primary_called = True
            raise AIError("Primary failed", provider="openai")

        async def fallback():
            nonlocal fallback_called
            fallback_called = True
            return "fallback_result"

        async def with_fallback(primary_fn, fallback_fn):
            try:
                return await primary_fn()
            except AIError:
                return await fallback_fn()

        result = await with_fallback(primary, fallback)

        assert primary_called is True
        assert fallback_called is True
        assert result == "fallback_result"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiple_fallbacks_chain(self):
        """Verify multiple fallbacks are tried in order."""
        calls = []

        async def provider1():
            calls.append("provider1")
            raise SearchError("Provider 1 failed")

        async def provider2():
            calls.append("provider2")
            raise SearchError("Provider 2 failed")

        async def provider3():
            calls.append("provider3")
            return "success"

        async def with_fallback_chain(providers: List):
            for provider in providers:
                try:
                    return await provider()
                except SearchError:
                    continue
            raise SearchError("All providers failed")

        result = await with_fallback_chain([provider1, provider2, provider3])

        assert result == "success"
        assert calls == ["provider1", "provider2", "provider3"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fallback_preserves_original_error(self):
        """Verify original error is preserved when all fallbacks fail."""
        original_error = AIError("Original error", provider="primary")

        async def primary():
            raise original_error

        async def fallback():
            raise AIError("Fallback error", provider="fallback")

        async def with_fallback_preserve_original(primary_fn, fallback_fn):
            try:
                return await primary_fn()
            except AIError as original:
                try:
                    return await fallback_fn()
                except AIError:
                    raise original  # Re-raise original

        with pytest.raises(AIError) as exc_info:
            await with_fallback_preserve_original(primary, fallback)

        # Should be the original error
        assert "Original error" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cached_fallback(self):
        """Verify cached results are used as fallback."""
        cache = {"query": "cached_result"}
        api_called = False

        async def api_call(query: str):
            nonlocal api_called
            api_called = True
            raise NetworkError("API unavailable")

        async def with_cache_fallback(query: str):
            try:
                return await api_call(query)
            except NetworkError:
                if query in cache:
                    return cache[query]
                raise

        result = await with_cache_fallback("query")

        assert api_called is True
        assert result == "cached_result"


# =============================================================================
# Graceful Degradation Tests
# =============================================================================


class TestGracefulDegradation:
    """Tests for graceful degradation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_partial_result_on_failure(self):
        """Verify partial results are returned on partial failure."""
        async def fetch_data(source: str):
            if source == "failing_source":
                raise NetworkError("Source unavailable")
            return f"data_from_{source}"

        async def fetch_all_with_degradation(sources: List[str]):
            results = {}
            errors = []

            for source in sources:
                try:
                    results[source] = await fetch_data(source)
                except NetworkError as e:
                    errors.append((source, str(e)))

            return {"results": results, "errors": errors}

        sources = ["source1", "failing_source", "source2"]
        output = await fetch_all_with_degradation(sources)

        assert len(output["results"]) == 2
        assert len(output["errors"]) == 1
        assert "source1" in output["results"]
        assert "source2" in output["results"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_default_value_on_failure(self):
        """Verify default values are used on failure."""
        async def fetch_optional_data():
            raise NetworkError("Service unavailable")

        async def get_data_with_default(default: Any = None):
            try:
                return await fetch_optional_data()
            except NetworkError:
                return default

        result = await get_data_with_default(default="default_value")
        assert result == "default_value"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduced_functionality_mode(self):
        """Verify system operates in reduced mode on failure."""
        class ServiceWithDegradation:
            def __init__(self):
                self.full_mode = True
                self.features_available = ["search", "analysis", "export"]

            async def enable_degraded_mode(self, failed_feature: str):
                self.full_mode = False
                self.features_available.remove(failed_feature)

            async def process(self, feature: str):
                if feature not in self.features_available:
                    raise RuntimeError(f"Feature {feature} unavailable")
                return f"processed_{feature}"

        service = ServiceWithDegradation()
        await service.enable_degraded_mode("analysis")

        # Search still works
        assert await service.process("search") == "processed_search"

        # Analysis is unavailable
        with pytest.raises(RuntimeError):
            await service.process("analysis")


# =============================================================================
# Recovery Path Tests
# =============================================================================


class TestRecoveryPaths:
    """Tests for error recovery paths."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_recovery_from_timeout(self):
        """Verify recovery from timeout errors."""
        attempt = 0

        async def operation_with_timeout():
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise AITimeoutError(provider="openai", timeout_seconds=30)
            return "recovered"

        async def recover_from_timeout(operation):
            try:
                return await operation()
            except AITimeoutError:
                # Retry with potentially different parameters
                return await operation()

        result = await recover_from_timeout(operation_with_timeout)
        assert result == "recovered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_recovery_from_rate_limit(self):
        """Verify recovery from rate limit errors."""
        async def operation():
            raise AIRateLimitError(provider="openai", retry_after=60)

        async def recover_from_rate_limit(operation, alternative):
            try:
                return await operation()
            except AIRateLimitError:
                # Switch to alternative provider
                return await alternative()

        async def alternative():
            return "alternative_result"

        result = await recover_from_rate_limit(operation, alternative)
        assert result == "alternative_result"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_recovery_state_cleanup(self):
        """Verify state is cleaned up on recovery."""
        class StatefulOperation:
            def __init__(self):
                self.state = "initial"
                self.resources = []

            async def acquire_resource(self):
                self.resources.append("resource")
                self.state = "acquired"

            async def release_resource(self):
                if self.resources:
                    self.resources.pop()
                self.state = "released"

            async def process(self):
                await self.acquire_resource()
                raise PipelineError("Processing failed")

        op = StatefulOperation()

        try:
            await op.process()
        except PipelineError:
            await op.release_resource()

        assert op.state == "released"
        assert len(op.resources) == 0


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self):
        """Verify circuit opens after threshold failures."""
        class CircuitBreaker:
            def __init__(self, failure_threshold: int = 3):
                self.failures = 0
                self.failure_threshold = failure_threshold
                self.state = "closed"

            async def execute(self, operation):
                if self.state == "open":
                    raise RuntimeError("Circuit is open")

                try:
                    result = await operation()
                    self.failures = 0
                    return result
                except Exception as e:
                    self.failures += 1
                    if self.failures >= self.failure_threshold:
                        self.state = "open"
                    raise

        breaker = CircuitBreaker(failure_threshold=3)

        async def failing_operation():
            raise NetworkError("Failed")

        # Three failures should open the circuit
        for _ in range(3):
            with pytest.raises(NetworkError):
                await breaker.execute(failing_operation)

        assert breaker.state == "open"

        # Further calls should fail fast
        with pytest.raises(RuntimeError, match="Circuit is open"):
            await breaker.execute(failing_operation)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_circuit_half_open_recovery(self):
        """Verify circuit can recover through half-open state."""
        class CircuitBreaker:
            def __init__(self):
                self.state = "open"

            async def try_recovery(self, operation):
                self.state = "half-open"
                try:
                    result = await operation()
                    self.state = "closed"
                    return result
                except Exception:
                    self.state = "open"
                    raise

        breaker = CircuitBreaker()

        async def recovered_operation():
            return "success"

        result = await breaker.try_recovery(recovered_operation)

        assert result == "success"
        assert breaker.state == "closed"


# =============================================================================
# Error Aggregation Tests
# =============================================================================


class TestErrorAggregation:
    """Tests for aggregating multiple errors."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_collect_all_errors(self):
        """Verify all errors are collected, not just first."""
        async def validate_item(item: dict) -> List[str]:
            errors = []
            if not item.get("name"):
                errors.append("name is required")
            if not item.get("value"):
                errors.append("value is required")
            if item.get("value", 0) < 0:
                errors.append("value must be positive")
            return errors

        item = {"name": "", "value": -5}
        errors = await validate_item(item)

        assert len(errors) == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_aggregate_pipeline_errors(self):
        """Verify pipeline errors are aggregated from all stages."""
        async def run_pipeline(stages: List):
            errors = []
            results = {}

            for stage_name, stage_fn in stages:
                try:
                    results[stage_name] = await stage_fn()
                except Exception as e:
                    errors.append(StageError(stage_name, str(e)))

            if errors:
                raise PipelineError(
                    f"{len(errors)} stages failed",
                    stage=None
                )

            return results

        async def stage1():
            raise ValueError("Stage 1 failed")

        async def stage2():
            return "success"

        async def stage3():
            raise ValueError("Stage 3 failed")

        stages = [("stage1", stage1), ("stage2", stage2), ("stage3", stage3)]

        with pytest.raises(PipelineError) as exc_info:
            await run_pipeline(stages)

        assert "2 stages failed" in str(exc_info.value)


# =============================================================================
# Logging and Monitoring Tests
# =============================================================================


class TestErrorLogging:
    """Tests for error logging during recovery."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_errors_are_logged(self):
        """Verify errors are logged for monitoring."""
        logged_errors = []

        def log_error(error: Exception, context: dict):
            logged_errors.append({
                "error_type": type(error).__name__,
                "message": str(error),
                "context": context
            })

        async def operation_with_logging():
            try:
                raise AIError("Test error", provider="test")
            except AIError as e:
                log_error(e, {"operation": "test", "attempt": 1})
                raise

        with pytest.raises(AIError):
            await operation_with_logging()

        assert len(logged_errors) == 1
        assert logged_errors[0]["error_type"] == "AIError"
        assert logged_errors[0]["context"]["operation"] == "test"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_recovery_events_logged(self):
        """Verify recovery events are logged."""
        events = []

        def log_event(event: str, details: dict):
            events.append({"event": event, "details": details})

        async def operation_with_recovery_logging():
            try:
                raise NetworkTimeoutError(url="test", timeout_seconds=30)
            except NetworkTimeoutError as e:
                log_event("error_occurred", {"error": str(e)})

                # Recovery
                log_event("recovery_attempted", {"strategy": "retry"})
                return "recovered"

        result = await operation_with_recovery_logging()

        assert result == "recovered"
        assert len(events) == 2
        assert events[0]["event"] == "error_occurred"
        assert events[1]["event"] == "recovery_attempted"
