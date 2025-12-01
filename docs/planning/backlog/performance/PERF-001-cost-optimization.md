# PERF-001: Cost Optimization Suite

## Priority: High

## Category: Performance / Cost

## Status: Backlog

## Summary

Implement comprehensive cost optimization to reduce LLM and API expenses at scale.

## Problem Areas

| Issue | Impact |
|-------|--------|
| Full context passed between agents | Token multiplication |
| No response caching (Redis) | Repeated API calls |
| Using large models for simple tasks | Overspend on easy work |
| No cost tracking | Invisible budget drain |

## Implementation Tasks

### A. Tiered Model Routing

- [ ] Create `src/core/model_router.py` with `ModelRouter` class
- [ ] Define model tiers (simple/standard/complex) with pricing
- [ ] Implement task complexity estimation
- [ ] Route tasks to appropriate model based on complexity
- [ ] Add configuration for tier mappings

```python
TIERS = {
    "simple": {"model": "gpt-4o-mini", "tasks": ["summarization", "extraction"]},
    "standard": {"model": "gpt-4o", "tasks": ["analysis", "comparison"]},
    "complex": {"model": "claude-sonnet-4", "tasks": ["strategy", "deep_reasoning"]}
}
```

### B. Response Caching (Redis)

- [ ] Create `src/services/redis_cache.py` with `LLMCache` class
- [ ] Implement cache key generation (model + prompt hash)
- [ ] Add TTL configuration (default 24 hours)
- [ ] Create `get_or_generate()` pattern
- [ ] Add cache hit/miss metrics
- [ ] Document Redis setup in infrastructure guide

### C. Context Compression

- [ ] Create `src/services/context_compressor.py`
- [ ] Define per-agent context needs mapping
- [ ] Implement compression for agent handoffs
- [ ] Add token counting before/after compression
- [ ] Target 50%+ token reduction for handoffs

### D. Cost Tracking Dashboard

- [ ] Create `src/services/cost_tracker.py` with `CostTracker` class
- [ ] Define pricing per model (input/output tokens)
- [ ] Record cost events per request
- [ ] Generate cost summaries by agent, model, task type
- [ ] Add cost alerts/warnings for budget thresholds
- [ ] Export cost reports (JSON/CSV)

## Acceptance Criteria

- [ ] Model routing reduces average cost per request by 30%+
- [ ] Redis caching achieves 40%+ hit rate for repeated queries
- [ ] Context compression reduces inter-agent token usage by 50%+
- [ ] Cost tracking provides real-time visibility into spending
- [ ] All optimizations are configurable/toggleable

## Technical Notes

- Redis backend planned in `src/services/cache_service.py` (interface exists)
- Current file-based cache in `src/core/cache.py` can be extended
- Integrate with existing `CachedAIClient` wrapper pattern
