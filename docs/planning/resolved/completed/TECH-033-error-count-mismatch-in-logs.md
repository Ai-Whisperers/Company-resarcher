# TECH-033: Error Count Mismatch in Logs

## Priority: LOW
## Category: Technical Debt/Observability
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Log messages show incorrect error counts, specifically showing `failed_queries=0` when all queries actually failed. This makes debugging and monitoring unreliable.

## Problem Statement

### Observed Log Output:
```
INFO: Research phase completed - total_sources=0 failed_queries=0 search_time=0.52s
```

### Reality:
- All 5 search queries failed to return results
- 0 sources collected
- But `failed_queries=0` is reported

### Expected Log Output:
```
INFO: Research phase completed - total_sources=0 failed_queries=5 search_time=0.52s
WARNING: All queries failed, no sources collected
```

## Root Cause Analysis

### 1. Error Counter Not Incremented

```python
# Current code pattern
failed_count = 0
for query in queries:
    try:
        results = await search(query)
        if results:
            all_results.extend(results)
        # BUG: Empty results not counted as failure
    except Exception as e:
        failed_count += 1  # Only increments on exception
        logger.error(f"Query failed: {e}")

# Problem: Query returning [] is not counted as failure
```

### 2. Silent Failures Not Tracked

```python
# Search provider returns empty list instead of raising
async def search(self, query: str) -> List[SearchResult]:
    try:
        response = await self._client.get(...)
        if response.status_code != 200:
            return []  # Silent failure - not counted
        return self._parse_results(response.json())
    except Exception:
        return []  # Silent failure - not counted
```

### 3. Success Defined Incorrectly

```python
# Current definition: success = no exception
# Correct definition: success = non-empty results
```

## Proposed Solutions

### Solution 1: Track Empty Results as Failures

```python
# src/tools/search/manager.py

class SearchMetrics:
    """Track search operation metrics."""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    empty_queries: int = 0
    total_results: int = 0

    def record_query(self, results: List[SearchResult], error: Optional[Exception] = None):
        self.total_queries += 1

        if error:
            self.failed_queries += 1
        elif not results:
            self.empty_queries += 1
        else:
            self.successful_queries += 1
            self.total_results += len(results)

    @property
    def effective_failures(self) -> int:
        """Queries that didn't produce usable results."""
        return self.failed_queries + self.empty_queries

async def search_multiple(self, queries: List[str]) -> Tuple[List[SearchResult], SearchMetrics]:
    metrics = SearchMetrics()
    all_results = []

    for query in queries:
        try:
            results = await self.search(query)
            metrics.record_query(results)
            all_results.extend(results)
        except Exception as e:
            metrics.record_query([], error=e)
            logger.error(f"Query failed: {e}")

    return all_results, metrics
```

### Solution 2: Detailed Search Statistics

```python
# src/tools/search/statistics.py

from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class QueryStats:
    query: str
    provider: str
    result_count: int
    duration_ms: float
    error: Optional[str] = None
    status: str = "success"  # success, empty, error

@dataclass
class SearchStatistics:
    queries: List[QueryStats] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.queries)

    @property
    def successful(self) -> int:
        return len([q for q in self.queries if q.status == "success"])

    @property
    def empty(self) -> int:
        return len([q for q in self.queries if q.status == "empty"])

    @property
    def failed(self) -> int:
        return len([q for q in self.queries if q.status == "error"])

    @property
    def total_results(self) -> int:
        return sum(q.result_count for q in self.queries)

    def summary(self) -> str:
        return (
            f"total_queries={self.total} "
            f"successful={self.successful} "
            f"empty={self.empty} "
            f"failed={self.failed} "
            f"total_results={self.total_results}"
        )

    def log(self):
        logger.info(f"Search statistics: {self.summary()}")

        if self.failed > 0 or self.empty > 0:
            for q in self.queries:
                if q.status != "success":
                    logger.warning(f"  {q.status.upper()}: '{q.query}' ({q.error or 'no results'})")
```

### Solution 3: Provider-Level Tracking

```python
# src/tools/search/manager.py

class SearchManager:
    def __init__(self):
        self._provider_stats: Dict[str, ProviderStats] = {}

    async def search_with_fallback(self, query: str) -> List[SearchResult]:
        for provider in self.providers:
            stats = self._provider_stats.setdefault(
                provider.name,
                ProviderStats(name=provider.name)
            )

            try:
                results = await provider.search(query)
                stats.record_attempt(success=bool(results), count=len(results))

                if results:
                    return results

            except Exception as e:
                stats.record_attempt(success=False, error=str(e))

        return []

    def get_provider_report(self) -> str:
        """Generate report of provider performance."""
        lines = ["Provider Statistics:"]
        for name, stats in self._provider_stats.items():
            lines.append(
                f"  {name}: {stats.success_rate:.1%} success, "
                f"{stats.total_attempts} attempts, "
                f"{stats.total_results} results"
            )
        return "\n".join(lines)
```

### Solution 4: Structured Logging with Metrics

```python
# src/utils/metrics.py

import structlog

logger = structlog.get_logger()

def log_search_completion(
    total_sources: int,
    queries_run: int,
    queries_successful: int,
    queries_empty: int,
    queries_failed: int,
    search_time: float,
):
    """Log search completion with accurate metrics."""

    logger.info(
        "research_phase_completed",
        total_sources=total_sources,
        queries_run=queries_run,
        queries_successful=queries_successful,
        queries_empty=queries_empty,
        queries_failed=queries_failed,
        effective_failure_rate=(queries_empty + queries_failed) / queries_run if queries_run > 0 else 0,
        search_time_seconds=search_time,
    )

    # Warn if high failure rate
    if queries_run > 0 and (queries_empty + queries_failed) / queries_run > 0.5:
        logger.warning(
            "high_query_failure_rate",
            rate=(queries_empty + queries_failed) / queries_run,
            recommendation="Check search provider configuration and query quality"
        )
```

## Files to Modify

1. `src/tools/search/manager.py` - Add proper metrics tracking
2. `src/pipeline/stages/research.py` - Use metrics in logging
3. `src/utils/metrics.py` - New file for metrics utilities (optional)

## Acceptance Criteria

- [ ] `failed_queries` accurately reflects queries that returned no results
- [ ] Distinguish between "empty results" and "error" failures
- [ ] Warning logged when all queries fail
- [ ] Per-provider statistics available
- [ ] Metrics include result counts, not just success/fail

## Testing Plan

1. **All Queries Fail Test**
   - Mock search to return empty for all queries
   - Verify `failed_queries` or `empty_queries` = total queries

2. **Mixed Results Test**
   - 2 queries succeed, 2 return empty, 1 throws exception
   - Verify accurate breakdown in logs

3. **Provider Fallback Test**
   - Primary provider fails, fallback succeeds
   - Verify provider-level stats are accurate

## Metrics Format

### Current (Bad):
```
INFO: Research phase completed - total_sources=0 failed_queries=0
```

### Proposed (Good):
```
INFO: Research phase completed
  - Queries: 5 total, 0 successful, 3 empty, 2 errors
  - Sources: 0 collected
  - Duration: 0.52s
WARNING: All queries produced no results
  - "Personal Paraguay market share" → empty
  - "Personal Paraguay competitors" → empty
  - "Personal Paraguay industry" → error: timeout
  - ...
```

## Related Issues

- BUG-038: Search fallback not triggering
- BUG-041: Analysis returns all N/A
- FE-011: Research quality metrics

## Notes

Accurate logging is essential for debugging and monitoring production systems. This issue makes it impossible to diagnose search problems from logs alone.

Consider adding:
1. Structured logging (JSON format) for log aggregation
2. Metrics export (Prometheus/StatsD) for dashboards
3. Alert thresholds for high failure rates
