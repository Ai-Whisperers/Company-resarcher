# TE-004: No Load/Performance Testing

**Priority**: Critical
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

The application has no load or performance testing infrastructure. Given that it processes concurrent research requests, makes multiple API calls, and performs web scraping, understanding performance characteristics is critical for production readiness.

## Current State

- No load tests exist
- No performance benchmarks
- No response time tracking
- No memory usage tests
- No concurrency stress tests

## Performance Concerns

1. **Concurrent Research Requests**:
   - Multiple research tasks running simultaneously
   - Shared resources (AI clients, rate limiters)
   - Unknown breaking point

2. **Memory Usage**:
   - Large research states accumulated
   - Browser instances for scraping
   - Cached AI responses

3. **API Rate Limits**:
   - Multiple LLM providers with limits
   - External API dependencies
   - No tests for graceful degradation

4. **Response Times**:
   - Full research takes unknown time
   - Individual agent performance unknown
   - Bottlenecks not identified

## Impact

- **Production failures**: System may fail under load
- **Poor user experience**: Unknown response times
- **Cost overruns**: Inefficient API usage
- **Scalability unknown**: Cannot plan capacity

## Proposed Solution

1. **Create load testing infrastructure**:
   ```python
   # Using locust or pytest-benchmark
   from locust import HttpUser, task

   class ResearchUser(HttpUser):
       @task
       def start_research(self):
           self.client.post("/api/v1/research", json={...})
   ```

2. **Create performance benchmarks**:
   ```python
   @pytest.mark.benchmark
   def test_ai_client_response_time(benchmark):
       """Benchmark AI client response time."""
       result = benchmark(ai_client.generate, prompt="test")
       assert benchmark.stats["mean"] < 2.0  # 2 seconds max
   ```

3. **Create memory usage tests**:
   ```python
   def test_memory_usage_bounded():
       """Verify memory doesn't grow unbounded."""
       import tracemalloc
       tracemalloc.start()
       # Run operation
       current, peak = tracemalloc.get_traced_memory()
       assert peak < 500 * 1024 * 1024  # 500MB max
   ```

4. **Create concurrency tests**:
   ```python
   @pytest.mark.slow
   async def test_concurrent_requests():
       """Test system handles concurrent requests."""
       tasks = [client.post("/research") for _ in range(10)]
       results = await asyncio.gather(*tasks)
       assert all(r.status_code == 200 for r in results)
   ```

## Acceptance Criteria

- [ ] Load testing tool configured (locust or k6)
- [ ] Performance benchmarks for critical paths
- [ ] Memory usage tests verify bounded growth
- [ ] Concurrency tests verify thread safety
- [ ] Performance baseline documented
- [ ] Tests run in CI (with limits for speed)

## Tools to Consider

- **locust**: Python-based load testing
- **k6**: Modern load testing tool
- **pytest-benchmark**: Benchmark plugin for pytest
- **memory_profiler**: Memory usage tracking

## Related Issues

- [TE-013](TE-013-slow-tests.md) - Tests are too slow
- [TE-017](TE-017-no-concurrent-tests.md) - No concurrency tests
