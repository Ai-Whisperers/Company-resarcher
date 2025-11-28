# AG-004: Unhandled Async Failures in Gather

**Priority**: Critical
**Effort**: Medium (1-3 days)
**Type**: Reliability / Error Handling

## Problem

`asyncio.gather()` calls don't properly handle individual task failures:

```python
# base_agent.py:144
results = await asyncio.gather(*tasks, return_exceptions=True)
# Results contain exceptions but are not checked

# deep_research.py:337
results = await asyncio.gather(*tasks)
results = [r for r in results if r is not None]  # Filters but doesn't log errors
```

## Locations

- `src/agents/base_agent.py:144` - `_gather_data()` method
- `src/agents/deep_research.py:337` - `deep_research()` method

## Impact

1. **Silent failures**: Errors swallowed without logging
2. **Partial data**: Research continues with incomplete data
3. **Debugging difficulty**: No indication of which tasks failed

## Recommended Fix

```python
async def _gather_data(self, queries: List[str]) -> List[ResearchSource]:
    tasks = [self._search_single(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    sources = []
    for query, result in zip(queries, results):
        if isinstance(result, Exception):
            logger.error(f"Query '{query}' failed: {result}")
            continue
        if result:
            sources.extend(result)

    if not sources:
        logger.warning("All queries failed - no data gathered")

    return sources
```

## Acceptance Criteria

- [ ] All gather() calls handle exceptions explicitly
- [ ] Failed tasks logged with context
- [ ] Partial success handled gracefully
- [ ] Metrics/counters for success/failure rates
- [ ] Tests for partial failure scenarios
