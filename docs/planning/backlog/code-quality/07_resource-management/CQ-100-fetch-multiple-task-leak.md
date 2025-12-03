# CQ-100: Task Memory Leak in fetch_multiple()

## Metadata
- **Severity**: HIGH
- **Category**: Resource Management
- **File**: [src/tools/browser/tool.py](src/tools/browser/tool.py#L281-L317)
- **Lines**: 281-317
- **Effort**: M
- **Status**: Open

## Problem

The `fetch_multiple()` method creates async tasks but doesn't properly cancel them if an error occurs. This can lead to:
1. Memory leaks from orphaned tasks
2. Resource exhaustion (browser pages not closed)
3. Unexpected background work continuing after error

## Current Code

```python
async def fetch_multiple(self, urls: List[str]) -> List[FetchResult]:
    """Fetch multiple URLs concurrently."""
    tasks = [self.fetch(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to fetch {urls[i]}: {result}")
            processed.append(FetchResult(url=urls[i], success=False, error=str(result)))
        else:
            processed.append(result)

    return processed
```

## Why This Is a Problem

1. **No cancellation on failure**: If the gather is cancelled (e.g., timeout), tasks continue running
2. **Resource leak**: Each task may hold browser pages, connections, memory
3. **Silent background work**: Tasks may complete after caller has moved on
4. **Memory pressure**: Long-running tasks accumulate without cleanup

## Solution

Properly manage task lifecycle with cancellation:

```python
async def fetch_multiple(
    self,
    urls: List[str],
    timeout: float = 30.0
) -> List[FetchResult]:
    """
    Fetch multiple URLs concurrently with proper cleanup.

    Args:
        urls: List of URLs to fetch
        timeout: Maximum time for all fetches (default: 30s)

    Returns:
        List of FetchResult objects
    """
    if not urls:
        return []

    # Create tasks explicitly for cancellation control
    tasks = [
        asyncio.create_task(self.fetch(url), name=f"fetch-{i}")
        for i, url in enumerate(urls)
    ]

    try:
        # Wait with timeout
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"fetch_multiple timed out after {timeout}s")
        # Cancel all pending tasks
        await self._cancel_tasks(tasks)
        # Return partial results
        results = await self._collect_partial_results(tasks, urls)
    except asyncio.CancelledError:
        # Propagate cancellation but cleanup first
        await self._cancel_tasks(tasks)
        raise
    except Exception:
        # Unexpected error - cleanup and re-raise
        await self._cancel_tasks(tasks)
        raise

    return self._process_results(results, urls)

async def _cancel_tasks(self, tasks: List[asyncio.Task]) -> None:
    """Cancel all pending tasks and wait for completion."""
    for task in tasks:
        if not task.done():
            task.cancel()

    # Wait for all cancellations to complete
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def _collect_partial_results(
    self,
    tasks: List[asyncio.Task],
    urls: List[str]
) -> List[Union[FetchResult, Exception]]:
    """Collect results from completed tasks."""
    results = []
    for i, task in enumerate(tasks):
        if task.done() and not task.cancelled():
            try:
                results.append(task.result())
            except Exception as e:
                results.append(e)
        else:
            results.append(TimeoutError(f"Fetch timed out: {urls[i]}"))
    return results

def _process_results(
    self,
    results: List[Union[FetchResult, Exception]],
    urls: List[str]
) -> List[FetchResult]:
    """Convert raw results to FetchResult objects."""
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to fetch {urls[i]}: {result}")
            processed.append(FetchResult(
                url=urls[i],
                success=False,
                error=str(result)
            ))
        else:
            processed.append(result)
    return processed
```

### Using TaskGroup (Python 3.11+)

```python
async def fetch_multiple(self, urls: List[str]) -> List[FetchResult]:
    """Fetch multiple URLs using TaskGroup for automatic cleanup."""
    results = {}

    async with asyncio.TaskGroup() as tg:
        for url in urls:
            task = tg.create_task(self._fetch_with_result(url))
            results[url] = task

    return [
        results[url].result() if not results[url].cancelled() else
        FetchResult(url=url, success=False, error="Cancelled")
        for url in urls
    ]
```

## Testing

```python
import asyncio
import pytest

async def test_fetch_multiple_cancellation():
    """Test that tasks are cancelled on timeout."""
    tool = BrowserTool()
    started_tasks = []

    async def slow_fetch(url):
        started_tasks.append(url)
        await asyncio.sleep(10)  # Simulate slow fetch
        return FetchResult(url=url, success=True)

    with patch.object(tool, 'fetch', side_effect=slow_fetch):
        results = await tool.fetch_multiple(
            ["http://a.com", "http://b.com"],
            timeout=0.1
        )

    # All should be timeout errors
    assert all(not r.success for r in results)
    assert all("timeout" in r.error.lower() for r in results)

async def test_fetch_multiple_cleanup_on_error():
    """Test resources cleaned up on unexpected error."""
    tool = BrowserTool()
    active_tasks = []

    async def tracking_fetch(url):
        task_id = len(active_tasks)
        active_tasks.append(task_id)
        try:
            await asyncio.sleep(5)
        finally:
            active_tasks.remove(task_id)

    with patch.object(tool, 'fetch', side_effect=tracking_fetch):
        try:
            task = asyncio.create_task(
                tool.fetch_multiple(["http://a.com", "http://b.com"])
            )
            await asyncio.sleep(0.1)
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass

    # All tasks should be cleaned up
    await asyncio.sleep(0.1)
    assert len(active_tasks) == 0
```

## Related Issues

- CQ-108: Playwright cleanup not guaranteed
- CQ-112: Sequential async should use gather
