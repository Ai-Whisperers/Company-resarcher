"""
Retry strategy implementation with exponential backoff and jitter.

Provides configurable retry logic for handling transient failures in external
service calls. Supports different retry policies based on exception types
and includes budget-aware retrying.

Example:
    strategy = RetryStrategy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
    )

    @strategy
    async def call_api():
        return await client.request()

    # Or with budget awareness
    result = await strategy.execute_with_budget(
        call_api,
        timeout_budget=TimeoutBudget(total_seconds=60),
    )
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import (
    Callable,
    TypeVar,
    ParamSpec,
    Optional,
    Any,
    Awaitable,
)
from functools import wraps

from .logger import setup_logger
from .exceptions import (
    CompanyResearcherError,
    AIRateLimitError,
    NetworkTimeoutError,
    RateLimitedError,
)

logger = setup_logger("retry_strategy")

P = ParamSpec("P")
T = TypeVar("T")


class RetryExhaustedError(CompanyResearcherError):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f"Retry exhausted after {attempts} attempts",
            details={
                "attempts": attempts,
                "last_error": str(last_exception),
                "last_error_type": type(last_exception).__name__,
            },
        )


class RetryBudgetExhaustedError(CompanyResearcherError):
    """Raised when timeout budget is exhausted during retry."""

    def __init__(self, attempts: int, remaining_budget: float):
        self.attempts = attempts
        self.remaining_budget = remaining_budget
        super().__init__(
            f"Retry budget exhausted after {attempts} attempts ({remaining_budget:.1f}s remaining)",
            details={"attempts": attempts, "remaining_budget": remaining_budget},
        )


@dataclass
class RetryStats:
    """Statistics for retry operations."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_retries: int = 0
    total_delay_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_calls == 0:
            return 100.0
        return (self.successful_calls / self.total_calls) * 100

    @property
    def average_retries_per_call(self) -> float:
        """Average number of retries per call."""
        if self.total_calls == 0:
            return 0.0
        return self.total_retries / self.total_calls

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_calls": self.total_calls,
            "successful": self.successful_calls,
            "failed": self.failed_calls,
            "total_retries": self.total_retries,
            "total_delay_seconds": round(self.total_delay_seconds, 2),
            "success_rate": f"{self.success_rate:.1f}%",
            "avg_retries": round(self.average_retries_per_call, 2),
        }


@dataclass
class RetryPolicy:
    """
    Defines retry behavior for specific exception types.

    Args:
        exception_types: Tuple of exception types this policy applies to
        max_attempts: Maximum retry attempts for these exceptions
        base_delay: Initial delay before first retry
        max_delay: Maximum delay between retries
        respect_retry_after: Whether to use Retry-After header if available
    """

    exception_types: tuple[type[Exception], ...]
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    respect_retry_after: bool = True


# Default retry policies for common scenarios
DEFAULT_TRANSIENT_POLICY = RetryPolicy(
    exception_types=(
        asyncio.TimeoutError,
        NetworkTimeoutError,
        ConnectionError,
        OSError,
    ),
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
)

DEFAULT_RATE_LIMIT_POLICY = RetryPolicy(
    exception_types=(AIRateLimitError, RateLimitedError),
    max_attempts=5,
    base_delay=5.0,
    max_delay=60.0,
    respect_retry_after=True,
)


@dataclass
class RetryStrategy:
    """
    Configurable retry strategy with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of attempts (including initial)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds (cap for exponential growth)
        exponential_base: Base for exponential backoff (default 2.0)
        jitter: Whether to add random jitter to prevent thundering herd
        jitter_factor: Maximum jitter as fraction of delay (0.0 to 1.0)
        policies: Custom retry policies for specific exception types
        retryable_exceptions: Exception types that trigger retry
        non_retryable_exceptions: Exception types that never retry

    Example:
        strategy = RetryStrategy(max_attempts=3, base_delay=1.0)

        @strategy
        async def flaky_operation():
            ...
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.25
    policies: list[RetryPolicy] = field(default_factory=list)
    retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (
            asyncio.TimeoutError,
            ConnectionError,
            OSError,
            AIRateLimitError,
            RateLimitedError,
        )
    )
    non_retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (
            KeyboardInterrupt,
            SystemExit,
            ValueError,
            TypeError,
        )
    )

    # Internal state
    _stats: RetryStats = field(default_factory=RetryStats, init=False)

    @property
    def stats(self) -> RetryStats:
        """Get retry statistics."""
        return self._stats

    def calculate_delay(
        self,
        attempt: int,
        exception: Optional[Exception] = None,
    ) -> float:
        """
        Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (1-based)
            exception: The exception that triggered retry (for Retry-After)

        Returns:
            Delay in seconds
        """
        # Check for Retry-After in rate limit exceptions
        if exception:
            retry_after = getattr(exception, "retry_after", None)
            if retry_after and retry_after > 0:
                logger.debug(f"Using Retry-After header: {retry_after}s")
                return min(retry_after, self.max_delay)

        # Find applicable policy
        policy = self._get_policy_for_exception(exception)

        # Use policy values or defaults
        base = policy.base_delay if policy else self.base_delay
        max_d = policy.max_delay if policy else self.max_delay

        # Exponential backoff: base * (exponential_base ^ (attempt - 1))
        delay = base * (self.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, max_d)

        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay = delay + random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)  # Ensure minimum delay

        return delay

    def _get_policy_for_exception(
        self, exception: Optional[Exception]
    ) -> Optional[RetryPolicy]:
        """Find the most specific policy for an exception."""
        if exception is None:
            return None

        for policy in self.policies:
            if isinstance(exception, policy.exception_types):
                return policy
        return None

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should trigger a retry.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number (1-based)

        Returns:
            True if retry should be attempted
        """
        # Never retry certain exceptions
        if isinstance(exception, self.non_retryable_exceptions):
            return False

        # Check if we have attempts remaining
        policy = self._get_policy_for_exception(exception)
        max_attempts = policy.max_attempts if policy else self.max_attempts

        if attempt >= max_attempts:
            return False

        # Check if exception is retryable
        if isinstance(exception, self.retryable_exceptions):
            return True

        # Check policies
        for policy in self.policies:
            if isinstance(exception, policy.exception_types):
                return True

        return False

    async def execute(
        self,
        func: Callable[P, Awaitable[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from successful function call

        Raises:
            RetryExhaustedError: If all retries fail
        """
        self._stats.total_calls += 1
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                self._stats.successful_calls += 1
                if attempt > 1:
                    logger.info(f"Succeeded on attempt {attempt}")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed: {type(e).__name__}: {e}")

                if not self.should_retry(e, attempt):
                    self._stats.failed_calls += 1
                    raise

                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt, e)
                    self._stats.total_retries += 1
                    self._stats.total_delay_seconds += delay
                    logger.info(f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_attempts})")
                    await asyncio.sleep(delay)

        self._stats.failed_calls += 1
        raise RetryExhaustedError(self.max_attempts, last_exception)

    async def execute_with_budget(
        self,
        func: Callable[P, Awaitable[T]],
        timeout_budget: "TimeoutBudget",
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """
        Execute function with retry logic, respecting a timeout budget.

        Args:
            func: Async function to execute
            timeout_budget: Budget tracking remaining time
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from successful function call

        Raises:
            RetryBudgetExhaustedError: If budget exhausted before success
            RetryExhaustedError: If all retries fail
        """
        self._stats.total_calls += 1
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            # Check budget before attempt
            remaining = timeout_budget.remaining()
            if remaining <= 0:
                self._stats.failed_calls += 1
                raise RetryBudgetExhaustedError(attempt - 1, remaining)

            try:
                # Execute with remaining budget as timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=remaining,
                )
                self._stats.successful_calls += 1
                return result

            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} timed out (budget: {remaining:.1f}s)")
                # Don't retry timeout if budget exhausted
                if timeout_budget.remaining() <= 0:
                    self._stats.failed_calls += 1
                    raise RetryBudgetExhaustedError(attempt, 0)

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed: {type(e).__name__}: {e}")

                if not self.should_retry(e, attempt):
                    self._stats.failed_calls += 1
                    raise

            # Calculate delay but respect budget
            if attempt < self.max_attempts:
                delay = self.calculate_delay(attempt, last_exception)
                remaining = timeout_budget.remaining()

                if remaining <= delay:
                    # Not enough budget for delay + another attempt
                    logger.warning(f"Insufficient budget for retry ({remaining:.1f}s < {delay:.1f}s delay)")
                    self._stats.failed_calls += 1
                    raise RetryBudgetExhaustedError(attempt, remaining)

                # Reduce delay if it would consume too much budget
                # Reserve at least 5 seconds for the next attempt
                max_safe_delay = remaining - 5.0
                actual_delay = min(delay, max_safe_delay)

                if actual_delay > 0:
                    self._stats.total_retries += 1
                    self._stats.total_delay_seconds += actual_delay
                    logger.info(f"Retrying in {actual_delay:.2f}s (budget: {remaining:.1f}s)")
                    await asyncio.sleep(actual_delay)

        self._stats.failed_calls += 1
        raise RetryExhaustedError(self.max_attempts, last_exception)

    def __call__(self, func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        """Use as decorator."""

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await self.execute(func, *args, **kwargs)

        return wrapper


# =============================================================================
# Timeout Budget
# =============================================================================


@dataclass
class TimeoutBudget:
    """
    Tracks remaining time for an operation.

    Useful for distributing timeout across multiple sub-operations
    and respecting overall time limits during retries.

    Example:
        budget = TimeoutBudget(total_seconds=60)

        # Check remaining time
        if budget.has_time_remaining(min_required=10):
            result = await operation(timeout=budget.remaining())

        # Create sub-budget
        sub_budget = budget.consume(30)
    """

    total_seconds: float
    start_time: float = field(default_factory=time.monotonic)

    def elapsed(self) -> float:
        """Seconds elapsed since budget started."""
        return time.monotonic() - self.start_time

    def remaining(self) -> float:
        """Seconds remaining in budget."""
        return max(0.0, self.total_seconds - self.elapsed())

    def is_exhausted(self) -> bool:
        """Check if budget is fully consumed."""
        return self.remaining() <= 0

    def has_time_remaining(self, min_required: float = 0.0) -> bool:
        """Check if at least min_required seconds remain."""
        return self.remaining() >= min_required

    def consume(self, seconds: float) -> "TimeoutBudget":
        """
        Create a sub-budget with the specified seconds.

        The sub-budget will be capped by remaining time.
        """
        available = self.remaining()
        allocated = min(seconds, available)
        return TimeoutBudget(total_seconds=allocated)


# =============================================================================
# Convenience functions
# =============================================================================


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> RetryStrategy:
    """
    Create a retry strategy with common defaults.

    Example:
        @with_retry(max_attempts=5)
        async def flaky_api_call():
            ...
    """
    return RetryStrategy(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
    )


async def retry_async(
    func: Callable[P, Awaitable[T]],
    *args: P.args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    **kwargs: P.kwargs,
) -> T:
    """
    Execute an async function with default retry logic.

    Simple wrapper for one-off retries without creating a strategy.

    Example:
        result = await retry_async(api_call, param1, param2, max_attempts=5)
    """
    strategy = RetryStrategy(max_attempts=max_attempts, base_delay=base_delay)
    return await strategy.execute(func, *args, **kwargs)


__all__ = [
    "RetryStrategy",
    "RetryPolicy",
    "RetryStats",
    "RetryExhaustedError",
    "RetryBudgetExhaustedError",
    "TimeoutBudget",
    "with_retry",
    "retry_async",
    "DEFAULT_TRANSIENT_POLICY",
    "DEFAULT_RATE_LIMIT_POLICY",
]
