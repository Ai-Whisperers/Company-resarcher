# Parallelization Pattern

## 📖 Overview

Execute independent tasks concurrently to reduce total execution time by splitting work, processing in parallel, and merging results.

## 🎯 Core Concept

```
Input → Split → [Task 1, Task 2, Task 3] → Normalize → Merge → Output
                 (parallel execution)
```

## 💡 Key Benefits

- **Speed**: N tasks in 1/N time (ideally)
- **Efficiency**: Maximize resource utilization
- **Scalability**: Handle larger workloads
- **Throughput**: Process more items

## 🏗️ Implementation in Marketing Agent

### Batch Video Generation

**Location**: `code/api/services/batch_video_agent.py`

```python
class BatchVideoAgent:
    def __init__(self, max_parallel=3):
        self.semaphore = asyncio.Semaphore(max_parallel)

    async def generate_videos(self, ideas: List[Idea]):
        tasks = [
            self._generate_with_limit(idea)
            for idea in ideas
        ]

        # Execute in parallel (max 3 concurrent)
        results = await asyncio.gather(*tasks)
        return results

    async def _generate_with_limit(self, idea):
        async with self.semaphore:
            return await self._generate_single_video(idea)
```

### Parallel Research (Potential)

```python
async def parallel_research(queries: List[str]):
    # Split queries
    tasks = [
        research_single_query(q)
        for q in queries
    ]

    # Execute in parallel
    results = await asyncio.gather(*tasks)

    # Normalize and merge
    return merge_research_results(results)
```

## 📊 Performance Impact

### Sequential vs Parallel

| Videos | Sequential | Parallel (3) | Speedup |
| ------ | ---------- | ------------ | ------- |
| 3      | 9 min      | 3 min        | 3x      |
| 15     | 45 min     | 15 min       | 3x      |
| 30     | 90 min     | 30 min       | 3x      |

## 🎓 Best Practices

### Do's ✅

- **Limit Concurrency**: Use semaphores (avoid overwhelming APIs)
- **Handle Errors**: One failure shouldn't break all
- **Normalize Results**: Ensure consistent format
- **Monitor Resources**: CPU, memory, API limits

### Don'ts ❌

- **Don't Go Unlimited**: Respect rate limits
- **Don't Ignore Dependencies**: Only parallelize independent tasks
- **Don't Skip Error Handling**: Use `gather` with `return_exceptions=True`

## 🔧 Implementation Patterns

### 1. Semaphore-Based (Current)

```python
semaphore = asyncio.Semaphore(max_parallel)

async with semaphore:
    result = await task()
```

### 2. Task Pool

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(func, items))
```

### 3. Queue-Based

```python
queue = asyncio.Queue()
workers = [
    asyncio.create_task(worker(queue))
    for _ in range(num_workers)
]

for item in items:
    await queue.put(item)
```

## 📈 Optimization Tips

### 1. Find Optimal Concurrency

```python
# Too low: Underutilized
max_parallel = 1  # Sequential

# Too high: Rate limit errors
max_parallel = 100  # Overwhelming

# Just right: Balance speed & stability
max_parallel = 3-5  # Optimal for most APIs
```

### 2. Error Handling

```python
results = await asyncio.gather(
    *tasks,
    return_exceptions=True  # Don't fail all on one error
)

# Filter successes and failures
successes = [r for r in results if not isinstance(r, Exception)]
failures = [r for r in results if isinstance(r, Exception)]
```

### 3. Progress Tracking

```python
from tqdm.asyncio import tqdm

results = await tqdm.gather(*tasks, desc="Processing")
```

## 🚀 Future Enhancements

### Parallel Research

```python
# Research multiple topics concurrently
topics = ["market", "competitors", "trends"]
results = await asyncio.gather(*[
    research_topic(t) for t in topics
])
```

### Parallel Ideation

```python
# Generate multiple idea variations
variations = await asyncio.gather(*[
    generate_variation(concept, i)
    for i in range(num_variations)
])
```

## 🎯 Use Cases

**Good for Parallelization**:

- ✅ Independent API calls
- ✅ File I/O operations
- ✅ Database queries
- ✅ Video/image generation

**Bad for Parallelization**:

- ❌ Sequential dependencies
- ❌ Shared state mutations
- ❌ CPU-bound tasks (use multiprocessing)
- ❌ Single-threaded APIs

## 📊 Monitoring

Track these metrics:

- **Concurrency level**: Active parallel tasks
- **Queue depth**: Pending tasks
- **Error rate**: Failed tasks
- **Throughput**: Tasks per second
- **Latency**: Time per task

## ⚠️ Edge Cases & Pitfalls

### Common Pitfalls

1.  **Rate Limits**: Launching 100 parallel API calls will trigger 429 errors.
    - _Fix_: Use a `Semaphore` to limit concurrency (e.g., max 5 active requests).
2.  **Order of Results**: `asyncio.gather` returns results in order, but `as_completed` does not.
    - _Fix_: If order matters, use `gather`. If speed matters (processing first result first), use `as_completed`.
3.  **Shared State**: Modifying a global variable from parallel tasks causes race conditions.
    - _Fix_: Keep tasks stateless or use locks (though locks reduce parallelism).

### Edge Cases

- **Partial Failure**: 9/10 tasks succeed, 1 fails.
- **Zombie Tasks**: A task hangs indefinitely, blocking the entire batch. (Use `timeout`).

## 🧪 Testing Strategy

### 1. Mock Latency

Simulate slow tasks to verify parallel execution speedup.

```python
async def mock_task(id, delay):
    await asyncio.sleep(delay)
    return id

# Test: 3 tasks of 1s should take ~1s total, not 3s.
```

### 2. Race Condition Check

Run the parallel logic with a shared counter (without locks) to see if it breaks (it shouldn't if designed correctly).

### 3. Eval Metrics

- **Speedup Factor**: `Sequential Time / Parallel Time`.
- **Throughput**: Tasks completed per second.

## 💻 Runnable Example

View a working example of Parallelization with Semaphores:
[03_parallelization.py](../examples/03_parallelization.py)

---

**Pattern Type**: Core Execution  
**Difficulty**: Medium  
**Impact**: High  
**Status**: ✅ Fully Implemented (Batch Video)  
**Next**: Extend to research phase
