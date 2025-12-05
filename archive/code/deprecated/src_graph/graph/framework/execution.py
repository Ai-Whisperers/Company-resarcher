"""
Execution utilities (decorators, parallel execution) for the graph framework.
"""

import asyncio
from functools import wraps
from typing import Callable, Awaitable, TypeVar, Any, List, Tuple, Dict, Optional
import os

from src.core.logging import setup_logger

logger = setup_logger("graph_execution")

T = TypeVar("T")

# Configuration
DEFAULT_NODE_TIMEOUT = float(os.getenv("GRAPH_NODE_TIMEOUT_SECONDS", "300.0"))
MAX_RETRY_ATTEMPTS = int(os.getenv("GRAPH_MAX_RETRY_ATTEMPTS", "3"))
RETRY_BACKOFF_BASE = float(os.getenv("GRAPH_RETRY_BACKOFF_BASE", "2.0"))


def with_timeout(timeout_seconds: float = DEFAULT_NODE_TIMEOUT):
    """
    Decorator to add timeout to async node execution.

    Args:
        timeout_seconds: Maximum execution time in seconds
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                node_name = func.__name__
                logger.error(f"Node {node_name} timed out after {timeout_seconds}s")
                raise TimeoutError(
                    f"Node {node_name} exceeded timeout of {timeout_seconds}s"
                )

        return wrapper

    return decorator


def with_retry(
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    backoff_base: float = RETRY_BACKOFF_BASE,
    retryable_exceptions: tuple = (Exception,),
):
    """
    Decorator to add retry logic to async node execution.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_base: Base for exponential backoff
        retryable_exceptions: Tuple of exceptions that trigger retry
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_base**attempt
                        logger.warning(
                            f"Node {func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"Node {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            raise last_exception

        return wrapper

    return decorator


class ParallelNodeExecutor:
    """
    Execute multiple nodes in parallel with result aggregation.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        fail_fast: bool = False,
    ):
        """
        Initialize the parallel executor.

        Args:
            max_concurrent: Maximum number of concurrent node executions
            fail_fast: If True, cancel remaining tasks on first failure
        """
        self.max_concurrent = max_concurrent
        self.fail_fast = fail_fast
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def _run_node_with_semaphore(
        self,
        name: str,
        func: Callable,
        state: Any,
    ) -> Tuple[str, Dict[str, Any], Optional[str]]:
        """Execute a single node with semaphore control."""
        async with self._semaphore:  # type: ignore
            try:
                result = await func(state)
                return (name, result, None)
            except Exception as e:
                logger.error(f"Parallel node {name} failed: {e}")
                return (name, {}, str(e))

    async def _execute_fail_fast(
        self,
        tasks: List[asyncio.Task],
    ) -> List[Tuple[str, Dict[str, Any], Optional[str]]]:
        """Execute tasks with fail-fast behavior."""
        results: List[Tuple[str, Dict[str, Any], Optional[str]]] = []
        for coro in asyncio.as_completed(tasks):
            name, result, error = await coro
            if error:
                for task in tasks:
                    task.cancel()
                raise RuntimeError(f"Node {name} failed: {error}")
            results.append((name, result, error))
        return results

    def _merge_results(
        self,
        results: List[Tuple[str, Dict[str, Any], Optional[str]]],
        merge_strategy: str,
    ) -> Dict[str, Any]:
        """Merge results from parallel execution."""
        if merge_strategy == "collect":
            return {
                "parallel_results": {name: result for name, result, _ in results},
                "parallel_errors": [
                    f"{name}: {error}" for name, _, error in results if error
                ],
            }

        # Default merge strategy: update dict with each result
        merged: Dict[str, Any] = {}
        errors: List[str] = []
        for name, result, error in results:
            if error:
                errors.append(f"{name}: {error}")
            else:
                merged.update(result)
        if errors:
            merged["errors"] = merged.get("errors", []) + errors
        return merged

    async def execute_parallel(
        self,
        nodes: List[Tuple[str, Callable[..., Awaitable[Dict[str, Any]]]]],
        state: Any,
        merge_strategy: str = "merge",
    ) -> Dict[str, Any]:
        """
        Execute multiple node functions in parallel.

        Args:
            nodes: List of (node_name, node_function) tuples
            state: Current state to pass to each node
            merge_strategy: How to merge results - "merge" (dict update) or "collect" (list)

        Returns:
            Merged results from all nodes
        """
        if not self._semaphore:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        tasks = [
            asyncio.create_task(self._run_node_with_semaphore(name, func, state))
            for name, func in nodes
        ]

        if self.fail_fast:
            results = await self._execute_fail_fast(tasks)
        else:
            results = await asyncio.gather(*tasks)

        return self._merge_results(list(results), merge_strategy)


# Global parallel executor instance
_parallel_executor: Optional[ParallelNodeExecutor] = None


def get_parallel_executor(
    max_concurrent: int = 5,
    fail_fast: bool = False,
) -> ParallelNodeExecutor:
    """Get or create the global parallel executor."""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelNodeExecutor(
            max_concurrent=max_concurrent,
            fail_fast=fail_fast,
        )
    return _parallel_executor


def reset_parallel_executor() -> None:
    """Reset the global parallel executor."""
    global _parallel_executor
    _parallel_executor = None
