# TE-017: No Concurrency Tests

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

The system uses extensive async/await and parallel processing (semaphores, concurrent API calls), but there are no tests verifying thread safety or concurrent operation correctness.

## Current State

- No tests for concurrent request handling
- No tests for race conditions
- No tests for shared resource access
- No tests for semaphore behavior
- No tests for async task coordination

## Concurrency Points in Codebase

1. **BaseAgent parallelization**: `MAX_PARALLEL_QUERIES = 5`
2. **API concurrent requests**: Multiple research tasks
3. **Cached AI client**: Shared cache access
4. **Rate limiter**: Shared state
5. **Database sessions**: Connection pool

## Impact

- **Race conditions**: Data corruption under load
- **Deadlocks**: System hangs
- **Resource exhaustion**: Unbounded parallelism
- **Inconsistent state**: Concurrent modifications

## Proposed Solution

1. **Test parallel query limits**:

   ```python
   @pytest.mark.asyncio
   async def test_agent_respects_parallel_limit():
       """Verify agent doesn't exceed MAX_PARALLEL_QUERIES."""
       concurrent_count = 0
       max_concurrent = 0

       async def mock_query(*args):
           nonlocal concurrent_count, max_concurrent
           concurrent_count += 1
           max_concurrent = max(max_concurrent, concurrent_count)
           await asyncio.sleep(0.1)  # Simulate API call
           concurrent_count -= 1
           return "result"

       agent = BaseAgent(mock_ai_client)
       agent._execute_query = mock_query

       # Run 20 queries
       await agent.gather_data(queries=["q"] * 20)

       assert max_concurrent <= 5  # MAX_PARALLEL_QUERIES
   ```

2. **Test race conditions**:

   ```python
   @pytest.mark.asyncio
   async def test_cache_race_condition():
       """Verify cache handles concurrent writes."""
       cache = CachedAIClient()

       async def write_cache(key, value):
           await cache.set(key, value)
           await asyncio.sleep(0.01)
           return await cache.get(key)

       # Concurrent writes to same key
       results = await asyncio.gather(*[
           write_cache("key", f"value_{i}")
           for i in range(10)
       ])

       # All results should be consistent (no corruption)
       assert all(r.startswith("value_") for r in results)
   ```

3. **Test concurrent API requests**:

   ```python
   @pytest.mark.asyncio
   async def test_concurrent_research_requests(api_client):
       """Test API handles concurrent requests."""
       async def start_research(company_name):
           return api_client.post("/api/v1/research", json={
               "company_name": company_name,
               "website": f"https://{company_name.lower()}.com"
           })

       # Start 10 concurrent requests
       responses = await asyncio.gather(*[
           start_research(f"Company{i}")
           for i in range(10)
       ])

       # All should succeed
       assert all(r.status_code == 200 for r in responses)

       # All should have unique task IDs
       task_ids = [r.json()["task_id"] for r in responses]
       assert len(set(task_ids)) == 10
   ```

4. **Test database connection pool**:

   ```python
   @pytest.mark.asyncio
   async def test_database_connection_pool():
       """Test database handles concurrent connections."""
       async def db_operation(session):
           result = await session.execute(select(ResearchTask))
           return result.scalars().all()

       # Concurrent database operations
       async with async_session() as session:
           results = await asyncio.gather(*[
               db_operation(session)
               for _ in range(50)
           ])

       # All should complete without connection errors
       assert len(results) == 50
   ```

5. **Test deadlock scenarios**:

   ```python
   @pytest.mark.asyncio
   @pytest.mark.timeout(10)
   async def test_no_deadlock_in_agent_chain():
       """Verify agent chain doesn't deadlock."""
       # If this test times out, there's a deadlock
       result = await orchestrator.run_research(
           company_name="Test",
           website="https://test.com"
       )
       assert result is not None
   ```

## Acceptance Criteria

- [ ] Tests verify parallel query limits
- [ ] Tests check for race conditions in shared state
- [ ] Tests verify concurrent API request handling
- [ ] Tests verify database connection pool behavior
- [ ] Tests have timeouts to detect deadlocks
- [ ] Tests marked with `@pytest.mark.concurrent`

## Related Issues

- [TE-004](TE-004-no-load-tests.md) - No load/performance testing
- [TE-032](TE-032-no-test-isolation.md) - Tests not properly isolated
