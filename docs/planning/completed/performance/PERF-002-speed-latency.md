# PERF-002: Speed & Latency Optimization

## Priority: High

## Category: Performance / Speed

## Status: Backlog

## Summary

Reduce research task completion time and improve perceived responsiveness.

## Problem Areas

| Issue | Current State | Target |
|-------|---------------|--------|
| Sequential agent execution | Some parallel, some sequential | Full parallel where possible |
| No response streaming | Users wait for full response | Real-time streaming |
| Cold start data fetching | Fetch on demand | Speculative pre-fetching |
| Per-agent timeouts | Global timeout only | Smart per-agent budgets |

## Implementation Tasks

### A. Enhanced Parallel Agent Execution

- [ ] Create `src/pipeline/smart_parallel_executor.py`
- [ ] Implement semaphore-based concurrency control
- [ ] Add priority ordering for agent groups
- [ ] Handle per-agent timeouts (120s default)
- [ ] Track timing metrics per agent
- [ ] Support dependency-aware execution order

```python
async def execute_agents(
    agents: list[BaseAgent],
    company: CompanyProfile,
    priority_order: list[str] = None
) -> dict
```

### B. Streaming Responses

- [ ] Create `src/core/streaming_client.py`
- [ ] Implement `generate_streaming()` with chunk callbacks
- [ ] Add WebSocket support for real-time updates
- [ ] Stream partial results to UI as agents complete
- [ ] Implement progress indicators per stage

### C. Speculative Execution

- [ ] Create `src/pipeline/speculative_executor.py`
- [ ] Pre-fetch common data (web search, website, news)
- [ ] Cache speculative results for agent use
- [ ] Cancel unused speculations on completion
- [ ] Measure hit rate for speculative fetches

### D. Smart Timeout Budget

- [ ] Implement `TimeoutBudget` context manager
- [ ] Allocate time per stage based on priority
- [ ] Dynamically adjust remaining budget
- [ ] Graceful degradation when budget exhausted
- [ ] Log timeout patterns for optimization

## Acceptance Criteria

- [ ] Average research time reduced by 40%+
- [ ] First response streaming within 5 seconds
- [ ] Speculative fetching achieves 60%+ utilization
- [ ] No single agent blocks pipeline for >2 minutes
- [ ] User sees progress updates every 10 seconds

## Technical Notes

- Existing `ParallelResearchStage` can be enhanced
- WebSocket support needed for API streaming
- Consider `asyncio.TaskGroup` for Python 3.11+
