# AG-003: Unbounded Agent Cache Causing Memory Leaks

## Status: NOT APPLICABLE

> **Resolution**: After code review, this issue does not exist in the current codebase. The `AgentFactory` class does not maintain an agent cache - it creates fresh agent instances on each call to `create_specialists()`, `create_insight_generator()`, etc. There is no `_agents` dictionary or caching mechanism.
>
> **Reviewed**: 2024-11-28

---

## Original Description (for reference)

## Priority: Critical

## Description

The agent factory maintains a cache of created agents without any eviction policy or size limits. In long-running processes or under heavy load, this leads to:
- Continuous memory growth
- Eventual out-of-memory crashes
- Performance degradation from cache bloat

## Location

- **File**: `src/agents/factory.py`
- **Variable**: `_agent_cache` or similar
- **Lines**: Cache storage and retrieval

## Current Code Pattern

```python
class AgentFactory:
    def __init__(self):
        self._agents = {}  # No size limit

    def get_agent(self, agent_id: str):
        if agent_id not in self._agents:
            self._agents[agent_id] = self._create_agent(agent_id)
        return self._agents[agent_id]  # Never removed
```

## Problems

1. **No eviction**: Agents are never removed from cache
2. **No size limit**: Cache grows indefinitely
3. **No TTL**: Stale agents remain in memory
4. **Memory references**: Cached agents hold references to large objects

## Recommended Fix

```python
from functools import lru_cache
from cachetools import TTLCache
import weakref

class AgentFactory:
    def __init__(self, max_agents: int = 100, ttl_seconds: int = 3600):
        self._agent_cache = TTLCache(maxsize=max_agents, ttl=ttl_seconds)
        self._weak_refs = weakref.WeakValueDictionary()

    def get_agent(self, agent_id: str) -> BaseAgent:
        # Try weak reference first
        agent = self._weak_refs.get(agent_id)
        if agent is not None:
            return agent

        # Check TTL cache
        if agent_id in self._agent_cache:
            return self._agent_cache[agent_id]

        # Create new agent with bounded cache
        agent = self._create_agent(agent_id)
        self._agent_cache[agent_id] = agent
        self._weak_refs[agent_id] = agent
        return agent

    def clear_cache(self):
        """Manual cache clearing for testing/maintenance."""
        self._agent_cache.clear()
```

## Memory Analysis

Estimated memory per agent:
- Base agent object: ~1KB
- LLM client reference: ~5KB
- Conversation history: ~50KB (grows over time)
- Tool bindings: ~2KB
- **Total per agent**: ~60KB+ (grows with usage)

With 1000 cached agents: ~60MB+ of memory

## Impact

- **Severity**: High
- **Frequency**: Continuous during operation
- **Affected Components**: Entire application stability

## Monitoring Recommendations

```python
# Add cache metrics
def get_cache_stats(self):
    return {
        'size': len(self._agent_cache),
        'max_size': self._agent_cache.maxsize,
        'hits': self._cache_hits,
        'misses': self._cache_misses
    }
```

## Testing Requirements

- Load test with sustained agent creation
- Memory profiling over time
- Cache eviction verification
- TTL expiration tests

## Related Issues

- [CO-036](../core/CO-036-no-caching.md) - General caching strategy
- [GR-003](../graph/GR-003-unbounded-state.md) - Similar issue in graph state
