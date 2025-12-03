# PERF-013: Adaptive Search Timeout for Low-Result Queries

## Problem

The search tool uses a fixed 30-second timeout for ALL queries, even when it's clear no results exist. For obscure companies like Vox Paraguay, 150+ queries timeout at 30s each = 75+ minutes of waiting.

## Evidence from Logs

```
22:38:35 - search_tool - ERROR - Search timed out after 30s for '"Vox Paraguay" EBITDA margin'
22:38:35 - search_tool - ERROR - Search timed out after 30s for '"Vox Paraguay" revenue 2025'
22:38:35 - search_tool - ERROR - Search timed out after 30s for '"Vox Paraguay" annual report'
22:38:35 - search_tool - ERROR - Search timed out after 30s for '"Vox Paraguay" earnings report'
22:38:35 - search_tool - ERROR - Search timed out after 30s for '"Vox Paraguay" profit loss'
... (50+ more timeouts)
```

## Impact

- **Current**: 234 queries × 30s timeout potential = 117 minutes worst case
- **Vox Paraguay**: ~150 timeouts observed = ~75 minutes of waiting
- **All companies**: Adds 10-30 minutes per small/obscure company

## Proposed Solution

### 1. Progressive Timeout Reduction

Track timeout patterns and reduce timeout for subsequent similar queries:

```python
class AdaptiveSearchTimeout:
    def __init__(self, base_timeout: int = 30):
        self.base_timeout = base_timeout
        self.company_timeout_counts: Dict[str, int] = {}
        self.section_timeout_counts: Dict[str, int] = {}

    def get_timeout(self, company: str, section: str) -> int:
        """Reduce timeout if many failures for this company/section."""
        company_failures = self.company_timeout_counts.get(company, 0)
        section_failures = self.section_timeout_counts.get(f"{company}:{section}", 0)

        # After 5 failures in a section, reduce timeout to 10s
        if section_failures >= 5:
            return 10

        # After 20 failures for company, reduce timeout to 15s
        if company_failures >= 20:
            return 15

        return self.base_timeout

    def record_timeout(self, company: str, section: str):
        self.company_timeout_counts[company] = self.company_timeout_counts.get(company, 0) + 1
        key = f"{company}:{section}"
        self.section_timeout_counts[key] = self.section_timeout_counts.get(key, 0) + 1
```

### 2. Early Section Termination

If a section has 5+ consecutive timeouts, skip remaining queries in that section:

```python
async def research_section(self, section: str, queries: List[str]):
    consecutive_timeouts = 0
    max_consecutive = 5

    for query in queries:
        if consecutive_timeouts >= max_consecutive:
            logger.warning(f"Skipping remaining queries in {section} after {max_consecutive} timeouts")
            break

        result = await self.search(query)
        if result.timed_out:
            consecutive_timeouts += 1
        else:
            consecutive_timeouts = 0  # Reset on success
```

### 3. Company-Level Early Termination

If >50% of queries timeout across first 3 sections, reduce remaining sections:

```python
def should_reduce_research(self, results_so_far: List[SectionResult]) -> bool:
    if len(results_so_far) < 3:
        return False

    total_queries = sum(r.total_queries for r in results_so_far)
    total_timeouts = sum(r.timeout_count for r in results_so_far)

    timeout_rate = total_timeouts / total_queries if total_queries > 0 else 0

    if timeout_rate > 0.5:
        logger.warning(f"High timeout rate ({timeout_rate:.0%}), reducing remaining research")
        return True

    return False
```

## Files to Modify

- `src/tools/search_tool.py`
- `src/pipeline/comprehensive_research.py`
- New: `src/core/adaptive_timeout.py`

## Acceptance Criteria

- [ ] Timeout reduces after multiple failures for same company
- [ ] Sections terminate early after 5 consecutive timeouts
- [ ] Research reduces scope after >50% timeout rate
- [ ] Logging shows timeout adaptation decisions
- [ ] Time savings: 50%+ for obscure companies

## Priority

**HIGH** - Could save 30-60 minutes for small/dead companies.

## Estimate

3-4 hours implementation + testing
