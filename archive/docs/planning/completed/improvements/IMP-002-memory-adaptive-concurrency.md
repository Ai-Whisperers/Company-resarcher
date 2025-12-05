# IMP-002: Memory-Adaptive Concurrency

## Problem Statement

Running too many concurrent tasks (especially browser-based ones) can crash the system by exhausting memory. We currently use fixed concurrency limits which are either too conservative or too aggressive.

## Proposed Solution

Implement a `MemoryAdaptiveDispatcher` like in `crawl4ai`. This dispatcher monitors system memory usage and dynamically adjusts the number of concurrent tasks to keep usage within safe limits.

## Implementation Steps

1.  Implement a `MemoryMonitor` to check RAM usage.
2.  Create a `Dispatcher` class that manages a semaphore.
3.  In the loop, check memory before starting a new task.
4.  If memory is high, wait or reduce concurrency.

## Code Example

```python
class MemoryAdaptiveDispatcher:
    async def dispatch(self, tasks):
        while tasks:
            if self.monitor.get_memory_usage() > self.max_memory_percent:
                await asyncio.sleep(1)
                continue
            # Start next task
```

## Acceptance Criteria

- [ ] System does not crash OOM (Out Of Memory) during heavy loads.
- [ ] Concurrency maximizes utilization of available RAM.
- [ ] Logs show dynamic adjustment of active tasks.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/async_dispatcher.py`
