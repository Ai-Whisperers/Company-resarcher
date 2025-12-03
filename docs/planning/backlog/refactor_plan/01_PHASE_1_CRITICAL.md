# Phase 1: Critical Refactoring (Sprint 1-2)

## 1. Rate Limiter Consolidation

**Effort:** 8h
**Impact:** Prevents configuration drift
**Files Affected:** 4 files

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

## 2. Config Consolidation

**Effort:** 4h
**Impact:** Single source of truth
**Files Affected:** 2 files

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

## 3. HTTP Client Abstraction

**Effort:** 6h
**Impact:** DRY, unified retry/timeout
**Files Affected:** 6+ files

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling
