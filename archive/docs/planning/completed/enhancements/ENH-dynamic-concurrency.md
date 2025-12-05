# [RESOLVED] ENH: Dynamic Concurrency Control

**Status**: RESOLVED
**Original File**: backlog/04-enhancements.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Allow dynamic adjustment of concurrency based on system load/rate limits.

**Acceptance Criteria:**
- [x] Implement a `ConcurrencyManager`.
- [x] Monitor rate limit headers.
- [x] Adjust `semaphore` size dynamically.

## Resolution

Implemented `ConcurrencyManager` class with adaptive concurrency control.

### Implementation Details

**File:** `src/core/concurrency_manager.py`

#### Features

1. **Per-Provider Semaphores**: Separate concurrency limits for different providers (search, browser, AI)

2. **Three Strategies**:
   - `FIXED`: Never adjust concurrency
   - `ADAPTIVE`: Adjust based on rate limits and error rates
   - `AGGRESSIVE`: More aggressive scaling up

3. **Rate Limit Header Support**:
   ```python
   manager.report_rate_limit(
       provider="search",
       remaining=50,  # X-RateLimit-Remaining
       limit=100,     # X-RateLimit-Limit
       reset_at=time.time() + 60  # X-RateLimit-Reset
   )
   ```

4. **Automatic Adjustment**:
   - Decreases concurrency when rate limit remaining < 20%
   - Increases concurrency when rate limit remaining > 80% and error rate < 5%
   - Decreases on high error rates (> 10%)

5. **Performance Tracking**:
   - Recent latency tracking (last 100 requests)
   - Error rate calculation
   - Per-provider statistics

### Usage

```python
from src.core.concurrency_manager import get_concurrency_manager

manager = get_concurrency_manager()

# Use context manager for automatic tracking
async with manager.acquire("search"):
    result = await search_api.query(...)

# Report rate limit headers
manager.report_rate_limit("search", remaining=50, limit=100)

# Get statistics
stats = manager.get_stats()

# Manual limit adjustment
manager.set_limit("browser", 3)
```

### Configuration

```bash
# Environment variables
CONCURRENCY_STRATEGY=adaptive  # fixed, adaptive, aggressive
CONCURRENCY_ADJUSTMENT_INTERVAL=30  # seconds between adjustments
```

### Default Limits

| Provider | Initial | Min | Max |
|----------|---------|-----|-----|
| search   | 5       | 1   | 10  |
| browser  | 3       | 1   | 5   |
| ai       | 2       | 1   | 5   |
| default  | 5       | 1   | 20  |

## Files Created

- `src/core/concurrency_manager.py` - Full implementation (280 lines)

## Integration Points

The `ConcurrencyManager` can be integrated with:
- `BrowserTool` for page fetching
- `SearchTool` for search API calls
- `AIClient` for AI API calls

Replace existing semaphore usage with `manager.acquire()` for automatic tracking.
