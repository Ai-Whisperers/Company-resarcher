"""
Chaos engineering test fixtures.

Provides fixtures for simulating various failure conditions like network
timeouts, API errors, rate limits, and resource pressure.

Issue: TE-024
"""

import asyncio
from contextlib import contextmanager
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


# ============================================================================
# Network Chaos Fixtures
# ============================================================================


@pytest.fixture
def chaos_network_timeout():
    """
    Simulate network timeouts for all HTTP requests.

    Usage:
        def test_with_network_timeout(chaos_network_timeout):
            # All network requests will timeout
            result = await make_request()
    """
    async def timeout_response(*args, **kwargs):
        await asyncio.sleep(30)  # Longer than any reasonable timeout
        raise asyncio.TimeoutError("Network timeout")

    patches = []
    try:
        # Patch aiohttp
        p1 = patch("aiohttp.ClientSession.get", new=timeout_response)
        p2 = patch("aiohttp.ClientSession.post", new=timeout_response)
        patches.extend([p1.start(), p2.start()])
    except ModuleNotFoundError:
        pass

    try:
        # Patch httpx
        p3 = patch("httpx.AsyncClient.get", new=timeout_response)
        p4 = patch("httpx.AsyncClient.post", new=timeout_response)
        patches.extend([p3.start(), p4.start()])
    except ModuleNotFoundError:
        pass

    yield

    patch.stopall()


@pytest.fixture
def chaos_network_error():
    """Simulate network connection errors."""
    def connection_error(*args, **kwargs):
        raise ConnectionError("Network unreachable")

    with patch("socket.socket.connect", side_effect=connection_error):
        yield


@pytest.fixture
def chaos_dns_failure():
    """Simulate DNS resolution failures."""
    def dns_error(*args, **kwargs):
        raise OSError("Name or service not known")

    with patch("socket.getaddrinfo", side_effect=dns_error):
        yield


# ============================================================================
# API Chaos Fixtures
# ============================================================================


@pytest.fixture
def chaos_api_error():
    """Simulate general API errors."""
    def error_response(*args, **kwargs):
        raise Exception("Service unavailable")

    patches = {}

    try:
        patches["openai"] = patch(
            "openai.AsyncOpenAI.chat.completions.create",
            side_effect=error_response
        )
        patches["openai"].start()
    except (ModuleNotFoundError, AttributeError):
        pass

    yield

    for p in patches.values():
        try:
            p.stop()
        except Exception:
            pass


@pytest.fixture
def chaos_rate_limit():
    """Simulate rate limiting responses."""
    class RateLimitError(Exception):
        def __init__(self):
            super().__init__("Rate limit exceeded. Retry after 60 seconds.")
            self.retry_after = 60

    def rate_limit_response(*args, **kwargs):
        raise RateLimitError()

    patches = {}

    try:
        patches["openai"] = patch(
            "openai.AsyncOpenAI.chat.completions.create",
            side_effect=rate_limit_response
        )
        patches["openai"].start()
    except (ModuleNotFoundError, AttributeError):
        pass

    yield

    for p in patches.values():
        try:
            p.stop()
        except Exception:
            pass


@pytest.fixture
def chaos_intermittent_failure():
    """
    Simulate intermittent failures (50% failure rate).

    Useful for testing retry logic and circuit breakers.
    """
    call_count = {"value": 0}

    def intermittent(*args, **kwargs):
        call_count["value"] += 1
        if call_count["value"] % 2 == 0:
            raise Exception("Intermittent failure")
        return MagicMock()

    with patch("aiohttp.ClientSession.get", side_effect=intermittent):
        yield call_count


# ============================================================================
# Database Chaos Fixtures
# ============================================================================


@pytest.fixture
def chaos_db_disconnect():
    """Simulate database connection loss."""
    def db_error(*args, **kwargs):
        raise Exception("Connection lost to database server")

    with patch("sqlalchemy.engine.Engine.connect", side_effect=db_error):
        yield


@pytest.fixture
def chaos_db_timeout():
    """Simulate database query timeout."""
    def timeout(*args, **kwargs):
        raise TimeoutError("Query execution timeout")

    with patch("sqlalchemy.orm.Session.execute", side_effect=timeout):
        yield


@pytest.fixture
def chaos_db_deadlock():
    """Simulate database deadlock."""
    def deadlock(*args, **kwargs):
        raise Exception("Deadlock detected")

    with patch("sqlalchemy.orm.Session.commit", side_effect=deadlock):
        yield


# ============================================================================
# Resource Pressure Fixtures
# ============================================================================


@pytest.fixture
def chaos_memory_pressure():
    """
    Simulate memory pressure by allocating large objects.

    Note: This actually allocates memory, use with caution.
    """
    # Allocate 100MB of data
    large_data = ["x" * 1024 * 1024 for _ in range(100)]

    yield large_data

    # Force cleanup
    del large_data
    import gc
    gc.collect()


@pytest.fixture
def chaos_cpu_pressure():
    """
    Simulate CPU pressure with busy work.

    Note: This actually uses CPU, use with caution.
    """
    import threading
    import time

    stop_flag = {"value": False}

    def cpu_work():
        while not stop_flag["value"]:
            _ = sum(i * i for i in range(10000))

    threads = [threading.Thread(target=cpu_work) for _ in range(2)]
    for t in threads:
        t.start()

    yield

    stop_flag["value"] = True
    for t in threads:
        t.join(timeout=1)


@pytest.fixture
def chaos_disk_full():
    """Simulate disk full errors."""
    def disk_full(*args, **kwargs):
        raise OSError("No space left on device")

    with patch("builtins.open", side_effect=disk_full):
        yield


# ============================================================================
# Service Chaos Fixtures
# ============================================================================


@pytest.fixture
def chaos_slow_response():
    """Simulate very slow responses (but not timeouts)."""
    original_sleep = asyncio.sleep

    async def slow_sleep(duration):
        # Make everything 10x slower
        await original_sleep(duration * 10)

    with patch("asyncio.sleep", side_effect=slow_sleep):
        yield


@pytest.fixture
def chaos_corrupted_response():
    """Simulate corrupted/malformed responses."""
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.text = "<html>Error</html>"
    mock_response.status_code = 200

    with patch("aiohttp.ClientResponse", return_value=mock_response):
        yield mock_response


# ============================================================================
# Agent Failure Fixtures
# ============================================================================


@contextmanager
def fail_agent(agent_name):
    """
    Context manager to make a specific agent fail.

    Usage:
        with fail_agent("financial"):
            result = await orchestrator.run_research(...)
    """
    def agent_failure(*args, **kwargs):
        raise Exception(f"Agent {agent_name} failed")

    agent_paths = {
        "financial": "src.agents.sector_analyst.SectorAnalyst.analyze",
        "market": "src.agents.insight_generator.InsightGenerator.analyze",
        "critic": "src.agents.critic.Critic.review",
        "writer": "src.agents.writer.Writer.write",
    }

    if agent_name in agent_paths:
        with patch(agent_paths[agent_name], side_effect=agent_failure):
            yield
    else:
        yield


@pytest.fixture
def chaos_agent_failure():
    """
    Fixture providing the fail_agent context manager.

    Usage:
        def test_agent_failure(chaos_agent_failure):
            with chaos_agent_failure("financial"):
                result = await orchestrator.run_research(...)
    """
    return fail_agent


# ============================================================================
# Combined Chaos Scenarios
# ============================================================================


@pytest.fixture
def chaos_degraded_mode():
    """
    Simulate degraded mode: slow responses + intermittent failures.

    Represents a partially functioning system.
    """
    call_count = {"value": 0}

    async def degraded_response(*args, **kwargs):
        call_count["value"] += 1

        # Add delay
        await asyncio.sleep(1)

        # 30% failure rate
        if call_count["value"] % 3 == 0:
            raise Exception("Service degraded")

        return MagicMock(status_code=200, json=lambda: {"data": "ok"})

    with patch("aiohttp.ClientSession.get", new=degraded_response):
        yield call_count


@pytest.fixture
def chaos_cascade_failure():
    """
    Simulate cascade failures where one failure triggers others.

    This represents realistic failure scenarios in distributed systems.
    """
    failures = {"count": 0}

    def cascade(*args, **kwargs):
        failures["count"] += 1
        if failures["count"] > 3:
            raise Exception("Cascade failure: too many dependent failures")
        return MagicMock()

    patches = []

    # Patch multiple services to create cascade effect
    try:
        p1 = patch("aiohttp.ClientSession.get", side_effect=cascade)
        patches.append(p1.start())
    except Exception:
        pass

    yield failures

    patch.stopall()
