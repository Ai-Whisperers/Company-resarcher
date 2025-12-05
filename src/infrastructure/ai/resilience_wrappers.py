"""
Resilience wrappers for LangChain Runnables.

Wraps our existing circuit breaker, rate limiting, and timeout
patterns around LangChain components for consistent resilience.

These wrappers implement the LangChain Runnable interface, allowing
them to be composed with other LangChain components.

Usage:
    from langchain_anthropic import ChatAnthropic
    from src.infrastructure.ai.resilience_wrappers import (
        CircuitBreakerRunnable,
        RateLimitedRunnable,
        TimeoutRunnable,
    )

    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    # Wrap with circuit breaker
    model = CircuitBreakerRunnable(model, name="claude")

    # Wrap with rate limiting
    model = RateLimitedRunnable(model, provider="anthropic")

    # Wrap with timeout
    model = TimeoutRunnable(model, timeout_seconds=120)

    # Use as normal
    response = await model.ainvoke([HumanMessage(content="Hello")])
"""

import asyncio
from typing import (
    Any,
    Optional,
    Iterator,
    AsyncIterator,
    List,
    Union,
    TypeVar,
    Generic,
)
from functools import wraps

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.callbacks import CallbackManagerForLLMRun

from src.core.logging import setup_logger
from src.core.exceptions import AITimeoutError

logger = setup_logger("resilience_wrappers")

T = TypeVar("T")


class CircuitBreakerRunnable(Runnable[Input, Output]):
    """
    Wraps a Runnable with circuit breaker protection.

    Uses our existing CircuitBreaker implementation to prevent
    cascading failures when an AI provider is having issues.

    The circuit breaker tracks failures and "opens" after a threshold,
    failing fast instead of waiting for timeouts.

    Args:
        runnable: The LangChain runnable to protect
        name: Circuit breaker name (for tracking/logging)
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before testing recovery
        success_threshold: Successes needed to close from half-open
    """

    def __init__(
        self,
        runnable: Runnable[Input, Output],
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        self.runnable = runnable
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        # Get or create circuit breaker from registry
        from src.lib.resilience.circuit_breaker import get_circuit_registry

        self._circuit_breaker = get_circuit_registry().get_or_create(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
        )

    @property
    def InputType(self) -> type[Input]:
        """Return the input type of the wrapped runnable."""
        return self.runnable.InputType

    @property
    def OutputType(self) -> type[Output]:
        """Return the output type of the wrapped runnable."""
        return self.runnable.OutputType

    def invoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """Synchronous invocation with circuit breaker."""
        # Check circuit state
        if not self._circuit_breaker.can_execute():
            retry_after = self._circuit_breaker.time_until_retry()
            from src.lib.resilience.circuit_breaker import CircuitOpenError

            raise CircuitOpenError(self.name, retry_after)

        try:
            result = self.runnable.invoke(input, config, **kwargs)
            self._circuit_breaker.record_success()
            return result
        except Exception as e:
            self._circuit_breaker.record_failure(e)
            raise

    async def ainvoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """Async invocation with circuit breaker."""
        # Check and acquire
        await self._circuit_breaker.acquire()

        try:
            result = await self.runnable.ainvoke(input, config, **kwargs)
            self._circuit_breaker.record_success()
            return result
        except Exception as e:
            self._circuit_breaker.record_failure(e)
            raise

    def stream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Iterator[Output]:
        """Streaming with circuit breaker."""
        if not self._circuit_breaker.can_execute():
            retry_after = self._circuit_breaker.time_until_retry()
            from src.infrastructure.resilience.circuit_breaker import CircuitOpenError

            raise CircuitOpenError(self.name, retry_after)

        try:
            for chunk in self.runnable.stream(input, config, **kwargs):
                yield chunk
            self._circuit_breaker.record_success()
        except Exception as e:
            self._circuit_breaker.record_failure(e)
            raise

    async def astream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Output]:
        """Async streaming with circuit breaker."""
        await self._circuit_breaker.acquire()

        try:
            async for chunk in self.runnable.astream(input, config, **kwargs):
                yield chunk
            self._circuit_breaker.record_success()
        except Exception as e:
            self._circuit_breaker.record_failure(e)
            raise

    def batch(
        self,
        inputs: List[Input],
        config: Optional[Union[RunnableConfig, List[RunnableConfig]]] = None,
        **kwargs: Any,
    ) -> List[Output]:
        """Batch invocation with circuit breaker."""
        if not self._circuit_breaker.can_execute():
            retry_after = self._circuit_breaker.time_until_retry()
            from src.infrastructure.resilience.circuit_breaker import CircuitOpenError

            raise CircuitOpenError(self.name, retry_after)

        try:
            results = self.runnable.batch(inputs, config, **kwargs)
            self._circuit_breaker.record_success()
            return results
        except Exception as e:
            self._circuit_breaker.record_failure(e)
            raise

    async def abatch(
        self,
        inputs: List[Input],
        config: Optional[Union[RunnableConfig, List[RunnableConfig]]] = None,
        **kwargs: Any,
    ) -> List[Output]:
        """Async batch invocation with circuit breaker."""
        await self._circuit_breaker.acquire()

        try:
            results = await self.runnable.abatch(inputs, config, **kwargs)
            self._circuit_breaker.record_success()
            return results
        except Exception as e:
            self._circuit_breaker.record_failure(e)
            raise

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return self._circuit_breaker.stats.to_dict()


class RateLimitedRunnable(Runnable[Input, Output]):
    """
    Wraps a Runnable with rate limiting.

    Uses our existing rate limiter infrastructure to prevent
    exceeding API rate limits.

    Args:
        runnable: The LangChain runnable to protect
        provider: Provider name for rate limit configuration
        requests_per_minute: Override default RPM (optional)
    """

    def __init__(
        self,
        runnable: Runnable[Input, Output],
        provider: str,
        requests_per_minute: Optional[int] = None,
    ):
        self.runnable = runnable
        self.provider = provider
        self.requests_per_minute = requests_per_minute

        # Get rate limiter from manager
        from src.lib.resilience.rate_limiting import rate_limiter_manager

        self._rate_limiter_manager = rate_limiter_manager

    @property
    def InputType(self) -> type[Input]:
        """Return the input type of the wrapped runnable."""
        return self.runnable.InputType

    @property
    def OutputType(self) -> type[Output]:
        """Return the output type of the wrapped runnable."""
        return self.runnable.OutputType

    def invoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """
        Synchronous invocation with rate limiting.

        Note: Sync rate limiting uses blocking wait which may not be ideal.
        Prefer ainvoke for async contexts.
        """
        # For sync, we do a blocking acquire
        import time
        from src.infrastructure.resilience.rate_limiting import rate_limiter_manager

        limiter = rate_limiter_manager.get_limiter(self.provider)
        if limiter:
            # Simple sync wait (blocking)
            while not limiter.try_acquire():
                time.sleep(0.1)

        return self.runnable.invoke(input, config, **kwargs)

    async def ainvoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """Async invocation with rate limiting."""
        from src.infrastructure.resilience.rate_limiting import rate_limiter_manager

        # Acquire rate limit token
        await rate_limiter_manager.acquire(self.provider)

        return await self.runnable.ainvoke(input, config, **kwargs)

    def stream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Iterator[Output]:
        """Streaming with rate limiting (applied at start)."""
        import time
        from src.infrastructure.resilience.rate_limiting import rate_limiter_manager

        limiter = rate_limiter_manager.get_limiter(self.provider)
        if limiter:
            while not limiter.try_acquire():
                time.sleep(0.1)

        yield from self.runnable.stream(input, config, **kwargs)

    async def astream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Output]:
        """Async streaming with rate limiting (applied at start)."""
        from src.infrastructure.resilience.rate_limiting import rate_limiter_manager

        await rate_limiter_manager.acquire(self.provider)

        async for chunk in self.runnable.astream(input, config, **kwargs):
            yield chunk

    async def abatch(
        self,
        inputs: List[Input],
        config: Optional[Union[RunnableConfig, List[RunnableConfig]]] = None,
        **kwargs: Any,
    ) -> List[Output]:
        """Async batch with rate limiting per request."""
        from src.infrastructure.resilience.rate_limiting import rate_limiter_manager

        # Acquire for each input
        for _ in inputs:
            await rate_limiter_manager.acquire(self.provider)

        return await self.runnable.abatch(inputs, config, **kwargs)


class TimeoutRunnable(Runnable[Input, Output]):
    """
    Wraps a Runnable with timeout protection.

    Prevents requests from hanging indefinitely by enforcing
    a maximum execution time.

    Args:
        runnable: The LangChain runnable to protect
        timeout_seconds: Maximum execution time in seconds
    """

    def __init__(
        self,
        runnable: Runnable[Input, Output],
        timeout_seconds: float = 120.0,
    ):
        self.runnable = runnable
        self.timeout_seconds = timeout_seconds

    @property
    def InputType(self) -> type[Input]:
        """Return the input type of the wrapped runnable."""
        return self.runnable.InputType

    @property
    def OutputType(self) -> type[Output]:
        """Return the output type of the wrapped runnable."""
        return self.runnable.OutputType

    def invoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """
        Synchronous invocation with timeout.

        Note: Sync timeout uses threading which may not work for all cases.
        Prefer ainvoke for async contexts.
        """
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.runnable.invoke, input, config, **kwargs)
            try:
                return future.result(timeout=self.timeout_seconds)
            except concurrent.futures.TimeoutError:
                raise AITimeoutError(f"AI call timed out after {self.timeout_seconds}s")

    async def ainvoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """Async invocation with timeout."""
        try:
            return await asyncio.wait_for(
                self.runnable.ainvoke(input, config, **kwargs),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise AITimeoutError(f"AI call timed out after {self.timeout_seconds}s")

    def stream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Iterator[Output]:
        """
        Streaming with timeout.

        Note: Timeout applies to total streaming time, not individual chunks.
        """
        import time

        start_time = time.monotonic()

        for chunk in self.runnable.stream(input, config, **kwargs):
            if time.monotonic() - start_time > self.timeout_seconds:
                raise AITimeoutError(
                    f"AI streaming timed out after {self.timeout_seconds}s"
                )
            yield chunk

    async def astream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Output]:
        """
        Async streaming with timeout.

        Note: Timeout applies to total streaming time, not individual chunks.
        """
        import time

        start_time = time.monotonic()

        async for chunk in self.runnable.astream(input, config, **kwargs):
            if time.monotonic() - start_time > self.timeout_seconds:
                raise AITimeoutError(
                    f"AI streaming timed out after {self.timeout_seconds}s"
                )
            yield chunk

    async def abatch(
        self,
        inputs: List[Input],
        config: Optional[Union[RunnableConfig, List[RunnableConfig]]] = None,
        **kwargs: Any,
    ) -> List[Output]:
        """Async batch with timeout."""
        try:
            return await asyncio.wait_for(
                self.runnable.abatch(inputs, config, **kwargs),
                timeout=self.timeout_seconds * len(inputs),  # Scale with batch size
            )
        except asyncio.TimeoutError:
            raise AITimeoutError(
                f"AI batch timed out after {self.timeout_seconds * len(inputs)}s"
            )


class RetryRunnable(Runnable[Input, Output]):
    """
    Wraps a Runnable with retry logic.

    Implements exponential backoff with jitter for transient failures.

    Args:
        runnable: The LangChain runnable to protect
        max_attempts: Maximum retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        retry_exceptions: Exception types to retry (defaults to common transient errors)
    """

    def __init__(
        self,
        runnable: Runnable[Input, Output],
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retry_exceptions: Optional[tuple] = None,
    ):
        self.runnable = runnable
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

        # Default retry exceptions
        if retry_exceptions is None:
            from src.core.exceptions import AIRateLimitError

            self.retry_exceptions = (
                AIRateLimitError,
                ConnectionError,
                TimeoutError,
            )
        else:
            self.retry_exceptions = retry_exceptions

    @property
    def InputType(self) -> type[Input]:
        """Return the input type of the wrapped runnable."""
        return self.runnable.InputType

    @property
    def OutputType(self) -> type[Output]:
        """Return the output type of the wrapped runnable."""
        return self.runnable.OutputType

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        import random

        delay = min(
            self.base_delay * (self.exponential_base**attempt),
            self.max_delay,
        )
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return delay + jitter

    def invoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """Synchronous invocation with retries."""
        import time

        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return self.runnable.invoke(input, config, **kwargs)
            except self.retry_exceptions as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_attempts} after {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)

        raise last_exception

    async def ainvoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Output:
        """Async invocation with retries."""
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return await self.runnable.ainvoke(input, config, **kwargs)
            except self.retry_exceptions as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_attempts} after {delay:.1f}s: {e}"
                    )
                    await asyncio.sleep(delay)

        raise last_exception


def wrap_with_resilience(
    runnable: Runnable[Input, Output],
    provider: str,
    circuit_breaker: bool = True,
    rate_limiting: bool = True,
    timeout: bool = True,
    retry: bool = False,
    timeout_seconds: float = 120.0,
) -> Runnable[Input, Output]:
    """
    Convenience function to wrap a runnable with multiple resilience layers.

    Args:
        runnable: The LangChain runnable to protect
        provider: Provider name for circuit breaker and rate limiting
        circuit_breaker: Enable circuit breaker
        rate_limiting: Enable rate limiting
        timeout: Enable timeout
        retry: Enable retry logic
        timeout_seconds: Timeout in seconds

    Returns:
        Wrapped runnable with requested resilience layers
    """
    if retry:
        runnable = RetryRunnable(runnable)

    if circuit_breaker:
        runnable = CircuitBreakerRunnable(
            runnable,
            name=f"langchain_{provider}",
        )

    if rate_limiting:
        runnable = RateLimitedRunnable(runnable, provider=provider)

    if timeout:
        runnable = TimeoutRunnable(runnable, timeout_seconds=timeout_seconds)

    return runnable
