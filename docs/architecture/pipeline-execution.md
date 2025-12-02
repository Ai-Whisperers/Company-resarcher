# Pipeline Execution Model

This document describes how research pipelines execute, including parallel vs sequential modes, timeout handling, and stage coordination.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PipelineOrchestrator                          │
│  - Creates RequestContext with timeout budget                    │
│  - Initiates ResearchPipeline                                    │
│  - Handles errors and aggregates results                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ResearchPipeline                             │
│  - Manages stage execution                                       │
│  - Supports parallel or sequential mode                          │
│  - Tracks progress and timing                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Stage   │    │  Stage   │    │  Stage   │
    │ (Market) │    │(Finance) │    │(Compete) │
    └──────────┘    └──────────┘    └──────────┘
```

## Execution Modes

### Parallel Mode (Default)

```python
# All stages run concurrently
async def execute_parallel(stages, context):
    tasks = [stage.execute(context) for stage in stages]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Characteristics:**
- Faster overall execution (limited by slowest stage)
- Higher resource usage (concurrent AI calls, searches)
- Independent stage failures don't block others

**When to use:**
- Production environments with good rate limits
- When speed is priority over resource usage
- Default mode for API requests

### Sequential Mode

```python
# Stages run one at a time
async def execute_sequential(stages, context):
    results = []
    for stage in stages:
        result = await stage.execute(context)
        results.append(result)
    return results
```

**Characteristics:**
- Slower overall execution
- Lower resource usage
- Easier to debug (predictable order)
- Can use results from earlier stages

**When to use:**
- Development and debugging
- Rate-limited environments
- When stages depend on each other

## Stage Execution Flow

Each stage follows this execution pattern:

```
1. Stage receives PipelineContext
   └── Contains: company profile, timeout budget, shared state

2. Generate search queries
   └── Agent creates domain-specific queries

3. Execute searches (parallel within stage)
   └── Bounded by AGENT_MAX_CONCURRENT_QUERIES

4. Fetch page content
   └── Browser tool extracts text from URLs

5. Analyze with AI
   └── Send prompt with context to AI provider

6. Return StageResult
   └── Contains: markdown content, sources, timing
```

## Timeout Management

### Timeout Budget

```python
# Created by orchestrator
budget = TimeoutBudget(total_seconds=1800)  # 30 minutes

# Passed to each stage
stage.execute(context)  # context contains budget

# Stage checks remaining time
if budget.remaining() < 60:
    logger.warning("Low time budget, reducing queries")
```

### Stage Timeouts

Each stage has configurable timeout:

```python
# Environment variables
MARKET_STAGE_TIMEOUT_SECONDS=300
FINANCIAL_STAGE_TIMEOUT_SECONDS=300
COMPETITOR_STAGE_TIMEOUT_SECONDS=300
```

### Timeout Handling

```python
try:
    result = await asyncio.wait_for(
        stage.execute(context),
        timeout=stage_timeout
    )
except asyncio.TimeoutError:
    logger.warning(f"Stage {stage.name} timed out")
    result = StageResult(
        status="timeout",
        content="Research incomplete due to timeout"
    )
```

## Error Handling

### Stage Errors

Errors in individual stages don't fail the entire pipeline:

```python
results = await asyncio.gather(*tasks, return_exceptions=True)

for result in results:
    if isinstance(result, Exception):
        logger.error(f"Stage failed: {result}")
        # Continue with other results
```

### Partial Results

Pipeline returns partial results when some stages fail:

```python
{
    "status": "partial",
    "completed_stages": ["market", "financial"],
    "failed_stages": ["competitor"],
    "results": { ... }
}
```

## Progress Tracking

### Stage Progress Events

```python
# Emitted during execution
await context.emit_progress(
    stage="market",
    status="searching",
    progress=0.3,
    message="Searching for market data..."
)
```

### CLI Progress Display

```
[=====>                    ] 25% Market Analysis
  ├── Searching: 3/5 queries complete
  └── Found 12 sources
```

## Concurrency Control

### Within-Stage Parallelism

```python
# Bounded by semaphore
semaphore = asyncio.Semaphore(MAX_CONCURRENT_QUERIES)

async def search_with_limit(query):
    async with semaphore:
        return await search_tool.search(query)

# All queries run, but max 5 at a time
results = await asyncio.gather(*[
    search_with_limit(q) for q in queries
])
```

### Cross-Stage Resources

Shared resources use instance reuse:

```python
# Singleton search tool
search_tool = get_shared_search_tool()

# Singleton browser tool
browser_tool = get_shared_browser_tool()

# Both have internal rate limiting
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `RESEARCH_TIMEOUT_SECONDS` | 1800 | Overall pipeline timeout |
| `AGENT_MAX_CONCURRENT_QUERIES` | 5 | Parallel queries per stage |
| `LLM_TIMEOUT_SECONDS` | 120 | AI request timeout |
| `SEARCH_TIMEOUT_SECONDS` | 30 | Search timeout |

## Debugging Tips

### Enable Verbose Logging

```bash
python main.py --name "Company" -vv
```

### Trace Stage Execution

```python
# Logs show stage transitions
2025-12-01 10:00:00 [INFO] Stage 'market' starting
2025-12-01 10:00:05 [INFO] Stage 'market' searching (5 queries)
2025-12-01 10:00:15 [INFO] Stage 'market' analyzing (12 sources)
2025-12-01 10:00:30 [INFO] Stage 'market' completed (30.2s)
```

### Sequential Mode for Debugging

```bash
python main.py --sequential --name "Company"
```

## Related Documentation

- [Architecture Overview](README.md)
- [Reliability Patterns](../planning/resolved/architecture/ARCH-005-reliability-patterns.md)
- [Troubleshooting Guide](../troubleshooting.md)
