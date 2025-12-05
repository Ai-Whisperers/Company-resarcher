# DO-009: Complex Code Lacks Comments

**Priority**: Medium
**Category**: Documentation
**Status**: Open
**Effort**: Large (ongoing)

## Problem

Complex algorithms and business logic lack inline comments explaining the "why" behind decisions.

## Impact

- Difficult to understand intent
- Higher risk of breaking changes
- Slower code reviews
- Knowledge loss when developers leave

## Areas Needing Comments

### High Complexity Areas
1. `src/graph/graph_builder.py` - Graph construction logic
2. `src/core/smart_router.py` - Model selection algorithm
3. `src/agents/orchestrator.py` - Research coordination
4. `src/services/json_parser_helper.py` - Noise-tolerant parsing
5. `src/core/rate_limited_client.py` - Rate limiting logic

### Business Logic
1. `src/agents/specialists.py` - Research strategies
2. `src/core/alpha_miner.py` - Signal detection
3. `src/core/quant_engine.py` - Quantitative analysis

## Comment Guidelines

**Good comments explain WHY, not WHAT:**

```python
# Bad: Increment counter
counter += 1

# Good: Rate limiter requires minimum 100ms between requests
# to avoid 429 errors from OpenAI's token bucket algorithm
await asyncio.sleep(0.1)
```

**Document non-obvious decisions:**

```python
# Using Groq for initial parsing because it's 10x faster
# and accuracy doesn't matter for this pre-processing step
response = await groq_client.generate(...)
```

## Acceptance Criteria

- [ ] Complex algorithms have explanatory comments
- [ ] Non-obvious business decisions documented
- [ ] Magic numbers explained
- [ ] Workarounds have context (why, ticket refs)
