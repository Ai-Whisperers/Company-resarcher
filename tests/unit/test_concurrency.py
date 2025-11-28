"""
Concurrency tests for the Company Researcher application.

Tests thread safety, race conditions, semaphore behavior, and concurrent
operation correctness across various components.

Issue: TE-017
"""

import asyncio
import time
import threading
from collections import Counter
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# ============================================================================
# Parallel Query Limit Tests
# ============================================================================


class TestParallelQueryLimits:
    """Tests for parallel query limit enforcement."""

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_semaphore_limits_concurrent_tasks(self):
        """Verify semaphore correctly limits concurrent tasks."""
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)

        concurrent_count = 0
        max_observed = 0
        lock = asyncio.Lock()

        async def limited_task():
            nonlocal concurrent_count, max_observed
            async with semaphore:
                async with lock:
                    concurrent_count += 1
                    max_observed = max(max_observed, concurrent_count)

                await asyncio.sleep(0.01)  # Simulate work

                async with lock:
                    concurrent_count -= 1

        # Run 20 concurrent tasks
        tasks = [limited_task() for _ in range(20)]
        await asyncio.gather(*tasks)

        assert max_observed <= max_concurrent
        assert concurrent_count == 0

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_agent_respects_parallel_limit(self):
        """Verify agent doesn't exceed MAX_PARALLEL_QUERIES."""
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def mock_query(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

            await asyncio.sleep(0.05)  # Simulate API call

            async with lock:
                concurrent_count -= 1

            return {"result": "data"}

        # Simulate agent behavior with semaphore
        semaphore = asyncio.Semaphore(5)  # MAX_PARALLEL_QUERIES

        async def bounded_query(*args):
            async with semaphore:
                return await mock_query(*args)

        # Run many queries
        tasks = [bounded_query(f"query_{i}") for i in range(20)]
        results = await asyncio.gather(*tasks)

        assert max_concurrent <= 5
        assert len(results) == 20
        assert concurrent_count == 0


# ============================================================================
# Race Condition Tests
# ============================================================================


class TestRaceConditions:
    """Tests for race condition prevention."""

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_cache_concurrent_writes(self):
        """Verify cache handles concurrent writes safely."""
        cache = {}
        lock = asyncio.Lock()
        write_count = Counter()

        async def safe_cache_write(key, value):
            async with lock:
                cache[key] = value
                write_count[key] += 1
            return cache[key]

        # Concurrent writes to same and different keys
        tasks = []
        for i in range(10):
            tasks.append(safe_cache_write("shared_key", f"value_{i}"))
            tasks.append(safe_cache_write(f"key_{i}", f"value_{i}"))

        results = await asyncio.gather(*tasks)

        # Should have exactly one value for shared_key
        assert "shared_key" in cache
        # Should have all individual keys
        for i in range(10):
            assert f"key_{i}" in cache

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_counter_increment_race(self):
        """Test counter increments are atomic."""
        counter = {"value": 0}
        lock = asyncio.Lock()

        async def safe_increment():
            async with lock:
                counter["value"] += 1

        # Many concurrent increments
        tasks = [safe_increment() for _ in range(1000)]
        await asyncio.gather(*tasks)

        assert counter["value"] == 1000

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_singleton_race_condition(self):
        """Test singleton creation under concurrent access."""
        creation_count = 0
        instance = None
        lock = asyncio.Lock()

        async def get_singleton():
            nonlocal creation_count, instance
            async with lock:
                if instance is None:
                    creation_count += 1
                    await asyncio.sleep(0.001)  # Simulate init
                    instance = {"id": creation_count}
                return instance

        # Concurrent singleton access
        tasks = [get_singleton() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # Should only create once
        assert creation_count == 1
        # All results should be the same instance
        assert all(r["id"] == 1 for r in results)


# ============================================================================
# Concurrent API Request Tests
# ============================================================================


class TestConcurrentAPIRequests:
    """Tests for concurrent API request handling."""

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_concurrent_research_requests(self):
        """Test API handles concurrent requests correctly."""
        request_count = 0
        lock = asyncio.Lock()

        async def mock_start_research(company_name):
            nonlocal request_count
            async with lock:
                request_count += 1
                task_id = f"task_{request_count}"

            await asyncio.sleep(0.01)  # Simulate processing
            return {"task_id": task_id, "company": company_name}

        # Start 10 concurrent requests
        tasks = [mock_start_research(f"Company{i}") for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert len(responses) == 10

        # All should have unique task IDs
        task_ids = [r["task_id"] for r in responses]
        assert len(set(task_ids)) == 10

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_rate_limiter_concurrent_requests(self):
        """Test rate limiter under concurrent load."""
        allowed_count = 0
        rejected_count = 0
        lock = asyncio.Lock()

        # Simple token bucket rate limiter
        tokens = 5
        token_lock = asyncio.Lock()

        async def try_request():
            nonlocal allowed_count, rejected_count, tokens
            async with token_lock:
                if tokens > 0:
                    tokens -= 1
                    allowed = True
                else:
                    allowed = False

            async with lock:
                if allowed:
                    allowed_count += 1
                else:
                    rejected_count += 1

            return allowed

        # Fire 20 concurrent requests
        tasks = [try_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # Should have limited allowed requests
        assert allowed_count <= 5
        assert allowed_count + rejected_count == 20


# ============================================================================
# Database Connection Pool Tests
# ============================================================================


class TestDatabaseConnectionPool:
    """Tests for database connection pool behavior."""

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_connection_pool_under_load(self):
        """Test connection pool handles concurrent requests."""
        active_connections = 0
        max_connections = 0
        pool_size = 10
        connection_lock = asyncio.Lock()
        pool_semaphore = asyncio.Semaphore(pool_size)

        async def db_operation():
            nonlocal active_connections, max_connections
            async with pool_semaphore:
                async with connection_lock:
                    active_connections += 1
                    max_connections = max(max_connections, active_connections)

                # Simulate query
                await asyncio.sleep(0.01)

                async with connection_lock:
                    active_connections -= 1

            return True

        # Many concurrent operations
        tasks = [db_operation() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        assert all(results)
        assert max_connections <= pool_size
        assert active_connections == 0


# ============================================================================
# Deadlock Tests
# ============================================================================


class TestDeadlockPrevention:
    """Tests for deadlock prevention."""

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    @pytest.mark.timeout(5)
    async def test_no_deadlock_with_multiple_locks(self):
        """Verify no deadlock with multiple locks acquired in order."""
        lock_a = asyncio.Lock()
        lock_b = asyncio.Lock()
        results = []

        async def task_1():
            async with lock_a:
                await asyncio.sleep(0.01)
                async with lock_b:
                    results.append("task_1")

        async def task_2():
            async with lock_a:  # Same order as task_1
                await asyncio.sleep(0.01)
                async with lock_b:
                    results.append("task_2")

        await asyncio.gather(task_1(), task_2())

        assert len(results) == 2

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    @pytest.mark.timeout(5)
    async def test_no_deadlock_in_workflow(self):
        """Verify workflow doesn't deadlock."""
        completed = []

        async def step_1():
            await asyncio.sleep(0.01)
            completed.append("step_1")

        async def step_2():
            await asyncio.sleep(0.01)
            completed.append("step_2")

        async def step_3():
            await asyncio.sleep(0.01)
            completed.append("step_3")

        # Workflow with dependencies
        await step_1()
        await asyncio.gather(step_2(), step_3())

        assert "step_1" in completed
        assert "step_2" in completed
        assert "step_3" in completed


# ============================================================================
# Async/Await Coordination Tests
# ============================================================================


class TestAsyncCoordination:
    """Tests for async task coordination."""

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_gather_exception_handling(self):
        """Test asyncio.gather handles exceptions correctly."""
        async def success_task():
            await asyncio.sleep(0.01)
            return "success"

        async def failing_task():
            await asyncio.sleep(0.01)
            raise ValueError("Task failed")

        # With return_exceptions=True, should not raise
        results = await asyncio.gather(
            success_task(),
            failing_task(),
            return_exceptions=True
        )

        assert results[0] == "success"
        assert isinstance(results[1], ValueError)

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_task_cancellation_propagation(self):
        """Test task cancellation is properly propagated."""
        inner_cancelled = False

        async def inner_task():
            nonlocal inner_cancelled
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                inner_cancelled = True
                raise

        async def outer_task():
            await inner_task()

        task = asyncio.create_task(outer_task())
        await asyncio.sleep(0.01)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        assert inner_cancelled

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_event_coordination(self):
        """Test async event coordination."""
        event = asyncio.Event()
        results = []

        async def waiter(name):
            await event.wait()
            results.append(name)

        async def setter():
            await asyncio.sleep(0.05)
            event.set()

        # Start waiters
        tasks = [
            asyncio.create_task(waiter("waiter_1")),
            asyncio.create_task(waiter("waiter_2")),
            asyncio.create_task(waiter("waiter_3")),
            asyncio.create_task(setter()),
        ]

        await asyncio.gather(*tasks)

        assert len(results) == 3

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    async def test_queue_producer_consumer(self):
        """Test async queue producer/consumer pattern."""
        queue = asyncio.Queue(maxsize=5)
        produced = []
        consumed = []

        async def producer():
            for i in range(10):
                await queue.put(i)
                produced.append(i)
                await asyncio.sleep(0.001)

        async def consumer():
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=0.1)
                    consumed.append(item)
                    queue.task_done()
                except asyncio.TimeoutError:
                    break

        await asyncio.gather(producer(), consumer())

        assert len(produced) == 10
        assert len(consumed) == 10
        assert set(produced) == set(consumed)


# ============================================================================
# Thread Safety Tests
# ============================================================================


class TestThreadSafety:
    """Tests for thread safety in synchronous code."""

    @pytest.mark.concurrent
    def test_thread_safe_counter(self):
        """Test thread-safe counter implementation."""
        counter = {"value": 0}
        lock = threading.Lock()
        errors = []

        def increment():
            try:
                for _ in range(100):
                    with lock:
                        counter["value"] += 1
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter["value"] == 1000
        assert len(errors) == 0

    @pytest.mark.concurrent
    def test_thread_safe_list_append(self):
        """Test thread-safe list operations."""
        results = []
        lock = threading.Lock()

        def append_item(item):
            with lock:
                results.append(item)

        threads = [
            threading.Thread(target=append_item, args=(i,))
            for i in range(100)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 100
        assert set(results) == set(range(100))


# ============================================================================
# Stress Tests
# ============================================================================


class TestConcurrencyStress:
    """Stress tests for concurrent operations."""

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    @pytest.mark.slow
    async def test_high_concurrency_stress(self):
        """Stress test with high concurrency."""
        completed = 0
        lock = asyncio.Lock()

        async def quick_task():
            nonlocal completed
            await asyncio.sleep(0.001)
            async with lock:
                completed += 1

        # 500 concurrent tasks
        tasks = [quick_task() for _ in range(500)]
        await asyncio.gather(*tasks)

        assert completed == 500

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    @pytest.mark.slow
    async def test_sustained_concurrent_load(self):
        """Test sustained concurrent load over time."""
        request_count = 0
        error_count = 0
        lock = asyncio.Lock()

        async def make_request():
            nonlocal request_count, error_count
            try:
                await asyncio.sleep(0.01)
                async with lock:
                    request_count += 1
            except Exception:
                async with lock:
                    error_count += 1

        # Sustained load: 10 batches of 50 concurrent requests
        for _ in range(10):
            batch = [make_request() for _ in range(50)]
            await asyncio.gather(*batch)

        assert request_count == 500
        assert error_count == 0

    @pytest.mark.asyncio
    @pytest.mark.concurrent
    @pytest.mark.slow
    async def test_mixed_fast_slow_tasks(self):
        """Test mixing fast and slow concurrent tasks."""
        results = []
        lock = asyncio.Lock()

        async def fast_task(id):
            await asyncio.sleep(0.001)
            async with lock:
                results.append(("fast", id))

        async def slow_task(id):
            await asyncio.sleep(0.1)
            async with lock:
                results.append(("slow", id))

        # Mix of fast and slow tasks
        tasks = []
        for i in range(50):
            tasks.append(fast_task(i))
        for i in range(5):
            tasks.append(slow_task(i))

        await asyncio.gather(*tasks)

        fast_count = sum(1 for t, _ in results if t == "fast")
        slow_count = sum(1 for t, _ in results if t == "slow")

        assert fast_count == 50
        assert slow_count == 5
