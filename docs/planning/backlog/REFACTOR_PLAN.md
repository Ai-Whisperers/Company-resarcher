# Complete Refactoring, Modularization, Centralization & Abstraction Plan

## Executive Summary

This document outlines a comprehensive refactoring plan for the `src/` directory (246 files, ~88,000 LOC) to address:

- **Rate Limiter Fragmentation** - 3 incompatible systems
- **Configuration duplication** - 2 overlapping config files + 182 direct env reads
- **HTTP Client Duplication** - No unified client, duplicated 4x
- **AIClientManager God Object** - ~1000 LOC handling 7 responsibilities
- **AI Client Wrapper Soup** - 3 wrappers with no common base
- **Caching Scattered** - 5+ different cache implementations
- **Exception Handling** - 244 bare `except Exception:` blocks
- **Singleton overuse** - 134+ usages
- **Manager class ambiguity** - 35+ classes
- **Large monolithic files** - 10+ files over 900 lines

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Priority-Based Implementation Order

### 🔴 CRITICAL - Immediate (Sprint 1-2)

| Task | Files Affected | Effort | Impact |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 1. Rate Limiter Consolidation | 4 files | 8h | Prevents configuration drift |
| 2. Config Consolidation | 2 files | 4h | Single source of truth |
| 3. HTTP Client Abstraction | 6+ files | 6h | DRY, unified retry/timeout |

### 🟠 HIGH - Soon (Sprint 3-4)

| Task | Files Affected | Effort | Impact |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 4. AIClientManager Split | 1 → 4 files | 12h | Maintainability |
| 5. Cache Interface Unification | 5+ files | 6h | Consistent caching API |
| 6. Exception Handling Cleanup | 50+ files | 8h | Better debugging |
| 7. DelegatingAIClient Base | 3 files | 4h | Composable wrappers |

### 🟡 MEDIUM - Scheduled (Sprint 5-6)

| Task | Files Affected | Effort | Impact |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 8. Logger Cleanup | 321 calls | 2h (automated) | Consistency |
| 9. Provider Error Detection | 4 providers | 3h | Unified error handling |
| 10. Magic Numbers → Config | 10+ files | 2h | Configurability |
| 11. Service Standardization | 31 files | 4h | DI pattern |

### 🟢 LOWER - Future (Sprint 7+)

| Task | Files Affected | Effort | Impact |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 12. Singleton → DI Container | 10+ files | 6h | Testability |
| 13. Provider Registry | New | 3h | Plugin architecture |
| 14. File I/O Patterns | 27 files | 4h | Generic FileStorage |

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🔴 CRITICAL PHASE 1: Rate Limiter Consolidation (8h)

### Problem Statement

**3 incompatible rate limiting systems:**

| File | Implementation | Issue |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|
| `ai_rate_limiter.py` | Proactive token tracking | Used only by AI |
| `rate_limiter.py` | Token bucket pattern | Generic but unused |
| `manager.py:119-159` | Inline token bucket | Hardcoded, not reused |

**Root Cause:** Configuration drift between `api_limits.py` (authoritative) and actual usage. SearchManager ignores centralized config.

### Solution: Unified RateLimiterManager

```
src/core/rate_limiting/
├── __init__.py              # Public exports
├── config.py                # api_limits.py content (SINGLE SOURCE OF TRUTH)
├── base.py                  # BaseRateLimiter ABC
├── token_bucket.py          # TokenBucketRateLimiter
├── sliding_window.py        # SlidingWindowRateLimiter
├── manager.py               # RateLimiterManager (unified)
└── decorators.py            # @rate_limited decorator
```

### Implementation

```python
# src/core/rate_limiting/config.py
# Move all limits from api_limits.py here
class RateLimitConfig:
    """Single source of truth for all rate limits"""

    AI_LIMITS = {
        "openai": {"requests_per_minute": 60, "tokens_per_minute": 90000},
        "anthropic": {"requests_per_minute": 50, "tokens_per_minute": 100000},
        "gemini": {"requests_per_minute": 60, "tokens_per_minute": 60000},
        "groq": {"requests_per_minute": 30, "tokens_per_minute": 6000},
    }

    SEARCH_LIMITS = {
        "tavily": {"requests_per_minute": 100},
        "brave": {"requests_per_minute": 15},
        "serper": {"requests_per_minute": 100},
        "duckduckgo": {"requests_per_minute": 20},
    }

# src/core/rate_limiting/manager.py
class RateLimiterManager:
    """Unified rate limiter for all providers"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._limiters: Dict[str, BaseRateLimiter] = {}

    def get_limiter(self, provider: str, category: str = "ai") -> BaseRateLimiter:
        """Get or create rate limiter for provider"""
        key = f"{category}:{provider}"
        if key not in self._limiters:
            limits = self._get_limits(provider, category)
            self._limiters[key] = TokenBucketRateLimiter(**limits)
        return self._limiters[key]

    async def acquire(self, provider: str, category: str = "ai", tokens: int = 1) -> bool:
        """Acquire rate limit tokens"""
        limiter = self.get_limiter(provider, category)
        return await limiter.acquire(tokens)
```

### Migration Steps

1. Create `src/core/rate_limiting/` package
2. Move `api_limits.py` content to `rate_limiting/config.py`
3. Implement unified `RateLimiterManager`
4. Update `ai_rate_limiter.py` to use new manager
5. Update `SearchManager` to use new manager
6. Delete inline implementation in `manager.py:119-159`
7. Deprecate old `rate_limiter.py`

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🔴 CRITICAL PHASE 2: Configuration Consolidation (4h)

### Problem Statement

**2 overlapping config files:**

| File | Duplicated Classes |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|
| `config.py` (805 LOC) | AIProviderConfig, BrowserConfig |
| `configs.py` (100+ LOC) | AIProviderConfig, BrowserConfig |

**Plus:** 182 direct `os.getenv()` calls scattered across codebase

### Solution: Single Config Package

**Current State:**

- `config.py` (805 lines) - Pydantic Settings with 20+ Config classes
- `configs.py` (336 lines) - Duplicate config models
- 182 direct `os.getenv()` calls scattered across codebase
- `constants.py` (37 lines) - Hardcoded defaults

**Target State:**

```
src/core/config/
├── __init__.py          # Public exports
├── base.py              # BaseConfig, ConfigLoader
├── providers.py         # AI provider configs (OpenAI, Anthropic, etc.)
├── services.py          # Service configs (cache, search, browser)
├── pipeline.py          # Pipeline and research configs
├── database.py          # Database and Redis configs
├── server.py            # Server and API configs
└── defaults.py          # All default values (replaces constants.py)
```

**Actions:**

1. Create `src/core/config/` package
2. Migrate all configs from `config.py` and `configs.py`
3. Replace all 182 `os.getenv()` calls with config resolution
4. Delete `configs.py` (duplicate)
5. Move `constants.py` content to `defaults.py`

**Before:**

```python
# base_agent.py (line 34)
MAX_CONCURRENT_QUERIES = int(os.getenv("AGENT_MAX_CONCURRENT_QUERIES", "5"))
```

**After:**

```python
# base_agent.py
from core.config import get_config
config = get_config()
MAX_CONCURRENT_QUERIES = config.agent.max_concurrent_queries
```

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

### Migration Steps

1. Create `src/core/config/` package
2. Merge `config.py` + `configs.py` into categorized modules
3. Delete `configs.py` after migration
4. Move `constants.py` content to `config/defaults.py`
5. Create automated script to find/replace all `os.getenv()` calls
6. Add `ConfigValidator` for startup validation

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🔴 CRITICAL PHASE 3: HTTP Client Abstraction (6h)

### Problem Statement

**Each search provider implements HTTP handling independently:**

| File | Issue |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|
| `brave.py` | Direct aiohttp |
| `serper.py` | Direct aiohttp |
| `bing.py` | Direct aiohttp |
| `jina.py` | Direct aiohttp with custom headers |

**Duplicated ~4x:** Session handling, retry logic, timeout handling

### Solution: HTTPSearchProvider Base Class

```
src/tools/search/
├── http/
│   ├── __init__.py
│   ├── base.py              # HTTPSearchProvider base class
│   ├── session.py           # Shared session management
│   ├── retry.py             # Unified retry logic
│   └── exceptions.py        # HTTP-specific exceptions
```

### Implementation

```python
# src/tools/search/http/base.py
class HTTPSearchProvider(ABC):
    """Base class for HTTP-based search providers"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create shared session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self._default_headers()
            )
        return self._session

    @abstractmethod
    def _default_headers(self) -> Dict[str, str]:
        """Provider-specific headers"""
        pass

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Unified request with retry and error handling"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                async with session.request(method, url, **kwargs) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        await asyncio.sleep(retry_after)
                        continue
                    resp.raise_for_status()
                    return await resp.json()
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise SearchProviderError(f"{self.name} request failed: {e}")
                await asyncio.sleep(2 ** attempt)

    async def close(self) -> None:
        """Cleanup session"""
        if self._session and not self._session.closed:
            await self._session.close()
```

### Migration Example

```python
# Before (brave.py)
class BraveSearchProvider:
    async def search(self, query: str) -> List[SearchResult]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.api_key},
                params={"q": query}
            ) as resp:
                data = await resp.json()
                return self._parse_results(data)

# After
class BraveSearchProvider(HTTPSearchProvider):
    name = "brave"
    base_url = "https://api.search.brave.com/res/v1"

    def _default_headers(self) -> Dict[str, str]:
        return {"X-Subscription-Token": self.api_key}

    async def search(self, query: str) -> List[SearchResult]:
        data = await self._request("GET", "/web/search", params={"q": query})
        return self._parse_results(data)
```

### Migration Steps

1. Create `src/tools/search/http/` package
2. Implement `HTTPSearchProvider` base class
3. Migrate providers in order: brave → serper → bing → jina
4. Add shared session pool
5. Integrate with unified rate limiter

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟠 HIGH PHASE 4: AIClientManager Split (12h)

### Problem Statement

**God Object handling 7 responsibilities in ~1000 LOC:**

1. Provider initialization
2. Fallback chain management
3. Circuit breaker coordination
4. Rate limit checking
5. Cache integration
6. Retry logic
7. Model routing

### Solution: Extract into Focused Classes

```
src/core/ai/
├── __init__.py
├── manager.py               # AIClientManager (slim coordinator ~200 LOC)
├── factory.py               # ProviderFactory - creates clients
├── chain.py                 # FallbackChainManager - manages provider order
├── coordinator.py           # ProviderCoordinator - orchestrates calls
└── routing.py               # ModelRouter - routes to optimal provider
```

### Implementation

```python
# src/core/ai/factory.py
class ProviderFactory:
    """Creates AI client instances"""

    def __init__(self, config: AIConfig):
        self.config = config
        self._clients: Dict[str, BaseAIClient] = {}

    def create(self, provider: str) -> BaseAIClient:
        """Create client for provider"""
        if provider not in self._clients:
            self._clients[provider] = self._create_client(provider)
        return self._clients[provider]

    def _create_client(self, provider: str) -> BaseAIClient:
        providers = {
            "openai": OpenAIClient,
            "anthropic": AnthropicClient,
            "gemini": GeminiClient,
            "groq": GroqClient,
        }
        client_cls = providers.get(provider)
        if not client_cls:
            raise ValueError(f"Unknown provider: {provider}")
        return client_cls(self.config.get_provider_config(provider))

# src/core/ai/chain.py
class FallbackChainManager:
    """Manages provider fallback order"""

    def __init__(self, providers: List[str], circuit_breakers: Dict[str, CircuitBreaker]):
        self.providers = providers
        self.circuit_breakers = circuit_breakers

    def get_available_providers(self) -> List[str]:
        """Get providers with open circuits"""
        return [
            p for p in self.providers
            if not self.circuit_breakers.get(p, CircuitBreaker()).is_open
        ]

    def record_success(self, provider: str) -> None:
        if provider in self.circuit_breakers:
            self.circuit_breakers[provider].record_success()

    def record_failure(self, provider: str) -> None:
        if provider in self.circuit_breakers:
            self.circuit_breakers[provider].record_failure()

# src/core/ai/manager.py (slim)
class AIClientManager:
    """Slim coordinator - delegates to specialized components"""

    def __init__(
        self,
        factory: ProviderFactory,
        chain: FallbackChainManager,
        rate_limiter: RateLimiterManager,
        cache: Optional[AICache] = None
    ):
        self.factory = factory
        self.chain = chain
        self.rate_limiter = rate_limiter
        self.cache = cache

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate with fallback chain"""
        for provider in self.chain.get_available_providers():
            try:
                await self.rate_limiter.acquire(provider, "ai")
                client = self.factory.create(provider)
                result = await client.generate(prompt, **kwargs)
                self.chain.record_success(provider)
                return result
            except AIProviderError as e:
                self.chain.record_failure(provider)
                continue
        raise AllProvidersFailedError()
```

### Migration Steps

1. Create new files in `src/core/ai/`
2. Extract `ProviderFactory` from AIClientManager
3. Extract `FallbackChainManager` from AIClientManager
4. Extract routing logic to `ModelRouter`
5. Slim down `AIClientManager` to coordinator role
6. Update all imports

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟠 HIGH PHASE 5: Cache Interface Unification (6h)

### Problem Statement

**Caching scattered across 5+ files with different APIs:**

| File | Type | API |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| `cache.py` | File-based AI cache | `get()`, `set()` |
| `cached_ai_client.py` | Wrapper | Internal |
| `redis_cache.py` | Redis caching | Different API |
| `semantic_cache.py` | Semantic cache | `search()`, `store()` |
| `html_cache.py` | HTML cache | `get_cached()`, `cache()` |

### Solution: CacheProvider ABC

```
src/core/cache/
├── __init__.py
├── base.py                  # CacheProvider ABC
├── file.py                  # FileCacheProvider
├── redis.py                 # RedisCacheProvider
├── semantic.py              # SemanticCacheProvider
├── html.py                  # HTMLCacheProvider
└── manager.py               # CacheManager (facade)
```

### Implementation

```python
# src/core/cache/base.py
class CacheProvider(ABC):
    """Abstract base for all cache implementations"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value with optional TTL"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key, return True if existed"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or compute and store"""
        value = await self.get(key)
        if value is None:
            value = await factory()
            await self.set(key, value, ttl)
        return value

# src/core/cache/manager.py
class CacheManager:
    """Facade for multiple cache providers"""

    def __init__(self):
        self._providers: Dict[str, CacheProvider] = {}

    def register(self, name: str, provider: CacheProvider) -> None:
        self._providers[name] = provider

    def get_provider(self, name: str) -> CacheProvider:
        if name not in self._providers:
            raise ValueError(f"Cache provider not registered: {name}")
        return self._providers[name]

    @property
    def ai(self) -> CacheProvider:
        return self.get_provider("ai")

    @property
    def html(self) -> CacheProvider:
        return self.get_provider("html")

    @property
    def semantic(self) -> CacheProvider:
        return self.get_provider("semantic")
```

### Migration Steps

1. Create `src/core/cache/` package
2. Define `CacheProvider` ABC
3. Migrate each cache to implement ABC
4. Create `CacheManager` facade
5. Update all cache usages to use manager

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟠 HIGH PHASE 6: Exception Handling Cleanup (8h)

### Problem Statement

**244 bare `except Exception:` blocks across 50+ files**

Swallows specific exception types, hides bugs, makes debugging difficult.

### Solution: Specific Exception Handling

```python
# Pattern to replace
try:
    result = await some_operation()
except Exception as e:  # BAD
    logger.error(f"Failed: {e}")
    return None

# Replace with
try:
    result = await some_operation()
except SpecificError as e:
    logger.error(f"Specific failure: {e}")
    raise
except (NetworkError, TimeoutError) as e:
    logger.warning(f"Transient failure: {e}")
    return await fallback()
except Exception as e:
    logger.exception(f"Unexpected error: {e}")  # Full traceback
    raise UnexpectedError(f"Operation failed: {e}") from e
```

### Migration Steps (Automated + Manual)

1. **Automated scan** - Find all bare `except Exception:` blocks

   ```bash
   grep -rn "except Exception" src/ --include="*.py" | wc -l
   ```

2. **Categorize by module** - Group by file/module type

3. **Priority order:**

   - AI clients (critical path)
   - Pipeline stages (user-visible)
   - Tools (external integrations)
   - Services (business logic)

4. **For each block:**
   - Identify possible specific exceptions
   - Add appropriate handlers
   - Keep `Exception` only as absolute fallback with `logger.exception()`

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟠 HIGH PHASE 7: DelegatingAIClient Base (4h)

### Problem Statement

**AI Client Wrapper Soup:**

```python
CostTrackedAIClient(
    RateLimitedAIClient(
        CachedAIClient(
            BaseAIClient(...)
        )
    )
)
```

3 wrappers with no common base, similar patterns repeated.

### Solution: DelegatingAIClient Base

```python
# src/core/ai/wrappers/base.py
class DelegatingAIClient(BaseAIClient):
    """Base class for AI client wrappers/decorators"""

    def __init__(self, delegate: BaseAIClient):
        self._delegate = delegate

    async def generate(self, prompt: str, **kwargs) -> str:
        return await self._delegate.generate(prompt, **kwargs)

    async def generate_structured(self, prompt: str, schema: Dict) -> Dict:
        return await self._delegate.generate_structured(prompt, schema)

    # Delegate all other methods...

# src/core/ai/wrappers/cached.py
class CachedAIClient(DelegatingAIClient):
    """Adds caching to any AI client"""

    def __init__(self, delegate: BaseAIClient, cache: CacheProvider):
        super().__init__(delegate)
        self.cache = cache

    async def generate(self, prompt: str, **kwargs) -> str:
        cache_key = self._make_key(prompt, kwargs)
        return await self.cache.get_or_set(
            cache_key,
            lambda: self._delegate.generate(prompt, **kwargs)
        )

# src/core/ai/wrappers/rate_limited.py
class RateLimitedAIClient(DelegatingAIClient):
    """Adds rate limiting to any AI client"""

    def __init__(self, delegate: BaseAIClient, limiter: RateLimiterManager):
        super().__init__(delegate)
        self.limiter = limiter

    async def generate(self, prompt: str, **kwargs) -> str:
        await self.limiter.acquire(self._delegate.provider_name)
        return await self._delegate.generate(prompt, **kwargs)

# Composable usage
client = CachedAIClient(
    RateLimitedAIClient(
        CostTrackedAIClient(
            OpenAIClient(config)
        ),
        limiter
    ),
    cache
)
```

### Migration Steps

1. Create `DelegatingAIClient` base class
2. Refactor `CachedAIClient` to extend base
3. Refactor `RateLimitedAIClient` to extend base
4. Refactor `CostTrackedAIClient` to extend base
5. Update wrapper composition in manager

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟡 MEDIUM PHASE 8: Logger Cleanup (2h - Automated)

### Problem Statement

**321 repeated logger setup calls:**

```python
from ..core.logger import setup_logger
logger = setup_logger("module_name")
```

### Solution: Module-Level Logger Injection

```python
# Option A: Use Python's standard pattern
import logging
logger = logging.getLogger(__name__)

# Option B: Centralized registry
# src/core/logging/registry.py
class LoggerRegistry:
    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get(cls, name: str) -> logging.Logger:
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        return cls._loggers[name]

# Usage
from core.logging import get_logger
logger = get_logger(__name__)
```

### Automated Migration Script

```python
# scripts/migrate_loggers.py
import re
import os

OLD_PATTERN = r'from \.+core\.logger import setup_logger\nlogger = setup_logger\(["\'](\w+)["\']\)'
NEW_PATTERN = 'import logging\nlogger = logging.getLogger(__name__)'

for root, dirs, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            # Replace pattern in each file
            ...
```

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟡 MEDIUM PHASE 9: Provider Error Detection (3h)

### Problem Statement

**Inconsistent rate limit detection:**

| Provider | Detection Method |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| Anthropic | Native `RateLimitError` ✅ |
| OpenAI | Native `RateLimitError` ✅ |
| Gemini | String pattern matching ❌ |
| Groq | String pattern matching ❌ |

### Solution: ProviderErrorParser

```python
# src/core/ai/errors/parser.py
class ProviderErrorParser:
    """Unified error detection across providers"""

    RATE_LIMIT_PATTERNS = {
        "gemini": [r"quota exceeded", r"rate limit", r"429"],
        "groq": [r"rate_limit_exceeded", r"too many requests"],
    }

    @classmethod
    def is_rate_limit_error(cls, provider: str, error: Exception) -> bool:
        """Check if error is a rate limit error"""
        # Native exceptions
        if isinstance(error, (RateLimitError, anthropic.RateLimitError)):
            return True

        # Pattern matching for others
        error_str = str(error).lower()
        patterns = cls.RATE_LIMIT_PATTERNS.get(provider, [])
        return any(re.search(p, error_str) for p in patterns)

    @classmethod
    def is_transient_error(cls, error: Exception) -> bool:
        """Check if error is transient (should retry)"""
        return isinstance(error, (TimeoutError, ConnectionError)) or \
               cls.is_rate_limit_error("any", error)
```

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟡 MEDIUM PHASE 10: Magic Numbers → Config (2h)

### Problem Statement

**Hardcoded values scattered across codebase:**

| Location | Value |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|
| `ai_client.py:520` | `failure_threshold=5` |
| `smart_router.py:28` | `COUNTER_RESET_INTERVAL = 3600` |
| `rate_limited_client.py` | `10/min, 500/hour limits` |

### Solution: Move to Config

```python
# src/core/config/resilience.py
class ResilienceConfig(BaseSettings):
    circuit_breaker_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_THRESHOLD")
    circuit_breaker_reset_seconds: int = Field(default=60, env="CIRCUIT_BREAKER_RESET")
    counter_reset_interval: int = Field(default=3600, env="COUNTER_RESET_INTERVAL")
    default_rate_limit_per_minute: int = Field(default=10, env="DEFAULT_RATE_LIMIT_MIN")
    default_rate_limit_per_hour: int = Field(default=500, env="DEFAULT_RATE_LIMIT_HOUR")
```

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟡 MEDIUM PHASE 11: Service Standardization (4h)

### Problem Statement

**31 service files with mixed initialization patterns:**

- Some use `__init__` with dependency injection
- Some use singletons
- Some use factory functions
- Some use static methods

### Solution: ServiceBase Interface

```python
# src/services/base.py
class ServiceBase(ABC):
    """Base class for all services"""

    def __init__(self, config: Any, **dependencies):
        self.config = config
        self._inject_dependencies(dependencies)

    def _inject_dependencies(self, deps: Dict[str, Any]) -> None:
        for name, value in deps.items():
            setattr(self, name, value)

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup service resources"""
        pass

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Check service health"""
        pass
```

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟢 LOWER PHASE 12: Singleton → DI Container (6h)

(See detailed implementation in existing Phase 2 section below)

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟢 LOWER PHASE 13: Provider Registry (3h)

### Problem Statement

No central registry for all providers (AI, search, browser). Each type managed separately.

### Solution: Plugin Architecture

```python
# src/core/providers/registry.py
class ProviderRegistry:
    """Central registry for all provider types"""

    def __init__(self):
        self._providers: Dict[str, Dict[str, BaseProvider]] = {
            "ai": {},
            "search": {},
            "browser": {},
        }

    def register(self, category: str, name: str, provider: BaseProvider) -> None:
        self._providers[category][name] = provider

    def get(self, category: str, name: str) -> BaseProvider:
        return self._providers[category][name]

    def list_providers(self, category: str) -> List[str]:
        return list(self._providers[category].keys())

    def discover_plugins(self, plugin_dir: str) -> None:
        """Auto-discover and register providers from plugins"""
        ...
```

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## 🟢 LOWER PHASE 14: File I/O Patterns (4h)

### Problem Statement

**27 files with duplicated file I/O pattern:**

```python
try:
    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    logger.warning(f"Invalid JSON: {e}")
except IOError as e:
    logger.warning(f"Failed to read: {e}")
```

### Solution: Generic FileStorage

```python
# src/core/storage/file.py
class FileStorage(Generic[T]):
    """Generic file storage with serialization"""

    def __init__(
        self,
        path: Path,
        serializer: Serializer[T] = JSONSerializer()
    ):
        self.path = path
        self.serializer = serializer

    def read(self, default: Optional[T] = None) -> Optional[T]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return self.serializer.deserialize(f.read())
        except FileNotFoundError:
            return default
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Invalid data in {self.path}: {e}")
            return default

    def write(self, data: T) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.serializer.serialize(data))
```

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

# IMPLEMENTATION SUMMARY

## Complete Sprint Breakdown

### Sprint 1-2: CRITICAL FIXES (18h total)

| # | Task | Effort | Dependencies |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 1 | Rate Limiter Consolidation | 8h | None |
| 2 | Config Consolidation | 4h | None |
| 3 | HTTP Client Abstraction | 6h | None |

**Deliverables:**

- `src/core/rate_limiting/` package
- Unified `config.py` (delete `configs.py`)
- `src/tools/search/http/` base class

### Sprint 3-4: HIGH PRIORITY (30h total)

| # | Task | Effort | Dependencies |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 4 | AIClientManager Split | 12h | Phase 1 |
| 5 | Cache Interface Unification | 6h | None |
| 6 | Exception Handling Cleanup | 8h | None |
| 7 | DelegatingAIClient Base | 4h | Phase 4 |

**Deliverables:**

- `src/core/ai/` reorganized (factory, chain, coordinator)
- `src/core/cache/` unified interface
- 244 exception blocks cleaned up
- Composable AI client wrappers

### Sprint 5-6: MEDIUM PRIORITY (11h total)

| # | Task | Effort | Dependencies |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 8 | Logger Cleanup | 2h | Automated script |
| 9 | Provider Error Detection | 3h | Phase 4 |
| 10 | Magic Numbers → Config | 2h | Phase 2 |
| 11 | Service Standardization | 4h | None |

**Deliverables:**

- Consistent logging across 321 files
- `ProviderErrorParser` class
- All magic numbers in config
- `ServiceBase` interface for 31 services

### Sprint 7+: LOWER PRIORITY (13h total)

| # | Task | Effort | Dependencies |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| 12 | Singleton → DI Container | 6h | Phase 4-5 |
| 13 | Provider Registry | 3h | Phases 1-7 |
| 14 | File I/O Patterns | 4h | None |

**Deliverables:**

- All singletons use DI container
- Central `ProviderRegistry`
- Generic `FileStorage<T>` class

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Total Effort Estimation

| Priority | Tasks | Effort | Sprints |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|
| 🔴 CRITICAL | 3 | 18h | 1-2 |
| 🟠 HIGH | 4 | 30h | 3-4 |
| 🟡 MEDIUM | 4 | 11h | 5-6 |
| 🟢 LOWER | 3 | 13h | 7+ |
| **TOTAL** | **14** | **72h** | **~7 sprints** |

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Migration Strategy

### Step 1: Create New Structure

- Create new directories without removing old code
- Implement new abstractions alongside existing code

### Step 2: Gradual Migration

- Migrate one module at a time
- Update imports progressively
- Run tests after each migration

### Step 3: Deprecation

- Mark old code as deprecated
- Add warnings for direct usage
- Document migration path

### Step 4: Cleanup

- Remove deprecated code
- Update all imports
- Final testing and documentation

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Success Metrics

| Metric | Current | Target |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

-----|
| Singleton usages | 134 | 0 (use DI container) |
| Direct os.getenv() calls | 182 | 0 (use config) |
| Config sources | 3 | 1 |
| Manager classes without base | 35 | 0 |
| Files > 1000 lines | 6 | 0 |
| Files > 500 lines | 20+ | < 10 |
| Bare except Exception blocks | 244 | 0 |
| Tool implementations with common base | 0 | 47 |
| Test coverage | ~40% | > 80% |

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Risk Mitigation

### Risk 1: Breaking Changes

- **Mitigation:** Maintain backward compatibility during transition
- **Strategy:** Create adapters for old APIs

### Risk 2: Regression Bugs

- **Mitigation:** Comprehensive test suite before migration
- **Strategy:** Run tests after each change

### Risk 3: Timeline Slippage

- **Mitigation:** Prioritize high-impact changes
- **Strategy:** Deliver in incremental phases

### Risk 4: Knowledge Loss

- **Mitigation:** Document architecture decisions
- **Strategy:** Create architecture decision records (ADRs)

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Appendix A: File Mapping

### Files to Delete After Migration

- `src/core/configs.py` (merged into config/)
- `src/core/constants.py` (merged into config/defaults.py)
- `src/core/rate_limiter.py` (replaced by rate_limiting/)

### Files to Split

- `src/graph/graph_builder.py` (1,981 lines) → graph/builder/
- `src/pipeline/comprehensive_research.py` (1,400 lines) → pipeline/orchestration/
- `src/graph/state.py` (1,210 lines) → graph/state/
- `src/api/app.py` (1,114 lines) → api/routers/
- `src/core/validators.py` (980 lines) → core/validation/
- `src/core/ai_client.py` (963 lines) → core/ai/

### Files to Refactor In Place

- `src/core/cache.py` - Implement CacheProvider interface
- All 47 tool files - Extend BaseTool
- All search providers - Extend HTTPSearchProvider
- All AI client wrappers - Extend DelegatingAIClient

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Appendix B: New Package Structure

### Packages to Create

```
src/core/rate_limiting/     # Unified rate limiting
src/core/cache/             # Cache interface
src/core/ai/                # AI client reorganization
src/tools/search/http/      # HTTP provider base
src/core/storage/           # File I/O patterns
```

### Key New Classes

| Class | Purpose |
|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

----|### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---|
| RateLimiterManager | Unified rate limiting for all providers |
| CacheProvider | Abstract cache interface |
| CacheManager | Cache facade |
| ProviderFactory | Creates AI client instances |
| FallbackChainManager | Manages provider fallback order |
| DelegatingAIClient | Base for AI client wrappers |
| HTTPSearchProvider | Base for HTTP search providers |
| ProviderErrorParser | Unified error detection |
| ServiceBase | Standard service interface |
| FileStorage | Generic file I/O |

### Verification Steps

1. Create `tests/unit/test_rate_limiting.py` to test `RateLimiterManager` and `TokenBucketRateLimiter`
2. Verify rate limits are respected for different providers
3. Verify thread safety of the manager
4. Run: `pytest tests/unit/test_rate_limiting.py`

### Verification Steps

1. Run existing config tests: `pytest tests/unit/test_config.py`
2. Verify `Settings` singleton behavior is preserved
3. Verify environment variable overrides still work
4. Verify default values are correct

### Verification Steps

1. Run search tool tests: `pytest tests/unit/test_search_tool.py`
2. Verify HTTP session reuse (mocking `aiohttp.ClientSession`)
3. Verify retry logic triggers on 429/5xx errors
4. Verify timeout handling

### Verification Steps

1. Run AI client tests: `pytest tests/unit/test_ai_client.py`
2. Verify fallback chain logic works (mock failures in primary)
3. Verify circuit breaker state transitions
4. Verify factory creates correct client types

### Verification Steps

1. Run cache tests: `pytest tests/unit/test_cache.py`
2. Verify `get_or_set` behavior
3. Verify TTL expiration works
4. Verify different providers (Redis, File, etc.) adhere to the interface

### Verification Steps

1. Run exception tests: `pytest tests/unit/test_exceptions.py`
2. Verify specific exceptions are caught and handled, not just swallowed
3. Verify error logs contain useful tracebacks where appropriate

---

## Quick Reference: Priority Order

```
Sprint 1-2 (CRITICAL):
  1. Rate Limiter Consolidation (8h)
  2. Config Consolidation (4h)
  3. HTTP Client Abstraction (6h)

Sprint 3-4 (HIGH):
  4. AIClientManager Split (12h)
  5. Cache Interface Unification (6h)
  6. Exception Handling Cleanup (8h)
  7. DelegatingAIClient Base (4h)

Sprint 5-6 (MEDIUM):
  8. Logger Cleanup (2h)
  9. Provider Error Detection (3h)
  10. Magic Numbers → Config (2h)
  11. Service Standardization (4h)

Sprint 7+ (LOWER):
  12. Singleton → DI Container (6h)
  13. Provider Registry (3h)
  14. File I/O Patterns (4h)
```

**Total Estimated Effort: 72 hours**
