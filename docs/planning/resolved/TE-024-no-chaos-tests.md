# TE-024: No Chaos Engineering Tests

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Large

## Description

No chaos engineering tests exist to verify system resilience under failure conditions. The system's behavior when dependencies fail is unknown.

## Current State

- No chaos testing infrastructure
- Unknown behavior under failures
- No failover testing
- No recovery testing

## Impact

- **Unknown failure modes**: System behavior during outages unknown
- **No resilience validation**: Recovery mechanisms untested
- **Production surprises**: Failures discovered in production
- **Extended outages**: No tested recovery procedures

## Chaos Scenarios to Test

| Scenario | Expected Behavior |
|----------|-------------------|
| LLM API unavailable | Fallback to secondary provider |
| Search API timeout | Graceful degradation |
| Database connection lost | Queue requests, reconnect |
| Rate limit exceeded | Backoff and retry |
| Network partition | Timeout and recover |
| Memory pressure | Graceful shutdown |

## Proposed Solution

1. **Install chaos testing tools**:

   ```bash
   pip install chaos-monkey
   # or use pytest with manual chaos injection
   ```

2. **Create chaos fixtures**:

   ```python
   # tests/chaos/conftest.py
   import pytest
   from unittest.mock import patch
   import asyncio

   @pytest.fixture
   def chaos_network_timeout():
       """Simulate network timeouts."""
       async def timeout_response(*args, **kwargs):
           await asyncio.sleep(30)  # Longer than timeout
           raise asyncio.TimeoutError()

       with patch("aiohttp.ClientSession.get", timeout_response):
           yield

   @pytest.fixture
   def chaos_api_error():
       """Simulate API errors."""
       def error_response(*args, **kwargs):
           raise Exception("Service unavailable")

       with patch("openai.AsyncOpenAI.chat.completions.create", error_response):
           yield

   @pytest.fixture
   def chaos_rate_limit():
       """Simulate rate limiting."""
       def rate_limit_response(*args, **kwargs):
           raise RateLimitError("Rate limit exceeded")

       with patch("openai.AsyncOpenAI.chat.completions.create", rate_limit_response):
           yield
   ```

3. **Create resilience tests**:

   ```python
   # tests/chaos/test_llm_resilience.py
   @pytest.mark.chaos
   @pytest.mark.slow
   async def test_llm_failover(chaos_api_error):
       """Test failover when primary LLM fails."""
       router = SmartRouter()

       # Primary should fail, secondary should work
       result = await router.generate("test prompt")

       assert result is not None
       assert router.current_provider == "backup"

   @pytest.mark.chaos
   async def test_rate_limit_backoff(chaos_rate_limit):
       """Test exponential backoff on rate limits."""
       client = AIClient()

       start = time.time()
       result = await client.generate("test")
       elapsed = time.time() - start

       # Should have backed off before succeeding
       assert elapsed > 1.0
       assert client.retry_count > 0
   ```

4. **Create recovery tests**:

   ```python
   @pytest.mark.chaos
   async def test_database_reconnection():
       """Test database reconnects after connection loss."""
       # Simulate connection loss
       with simulate_db_disconnect():
           await asyncio.sleep(1)

       # Connection should be restored
       result = await db.execute("SELECT 1")
       assert result.scalar() == 1

   @pytest.mark.chaos
   async def test_partial_research_recovery():
       """Test research continues after partial failure."""
       # Fail financial agent
       with fail_agent("financial"):
           result = await orchestrator.run_research(...)

       # Other agents should have completed
       assert result.market_data is not None
       assert result.errors == ["financial: Agent failed"]
   ```

5. **Create resource pressure tests**:

   ```python
   @pytest.mark.chaos
   @pytest.mark.slow
   async def test_memory_pressure_handling():
       """Test behavior under memory pressure."""
       # Allocate large memory blocks
       large_data = ["x" * 1000000 for _ in range(100)]

       # System should still function
       result = await orchestrator.run_research(...)

       # Cleanup
       del large_data
       gc.collect()

       assert result is not None
   ```

## Acceptance Criteria

- [ ] Chaos fixtures for common failure modes
- [ ] Tests for LLM failover behavior
- [ ] Tests for rate limit handling
- [ ] Tests for database reconnection
- [ ] Tests for partial failure recovery
- [ ] Chaos tests marked with `@pytest.mark.chaos`
- [ ] Run chaos tests weekly (not on every PR)

## Related Issues

- [TE-016](TE-016-no-error-tests.md) - Missing error path tests
- [TE-004](TE-004-no-load-tests.md) - No load/performance testing
