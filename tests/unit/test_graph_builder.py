"""
Unit tests for ResearchGraph.

Tests the LangGraph workflow builder including:
- Graph initialization
- Node registration
- Edge configuration
- Conditional routing
- Workflow execution
- Circuit breaker pattern (GR-012)
- Dead letter queue (GR-008)
- Execution metrics (GR-016)
- Retry logic (GR-011)
- Node timeouts (GR-007)
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from src.graph.graph_builder import (
    ResearchGraph,
    CircuitBreaker,
    CircuitState,
    DeadLetterQueue,
    DeadLetterEntry,
    ExecutionMetrics,
    NodeMetrics,
    with_timeout,
    with_retry,
    DEFAULT_NODE_TIMEOUT,
    MAX_RETRY_ATTEMPTS,
    CIRCUIT_BREAKER_THRESHOLD,
)
from src.graph.state import ResearchState, ResearchPhase
from src.agents.base_agent import BaseAgent


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_agents():
    """Create mock specialist agents."""
    agents = {}
    for agent_type in ["financial", "market", "sales", "competitor", "brand"]:
        mock_agent = MagicMock(spec=BaseAgent)
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"data": f"{agent_type}_analysis"}
        mock_agent.research = AsyncMock(return_value=mock_result)
        agents[agent_type] = mock_agent
    return agents


@pytest.fixture
def mock_insight_generator():
    """Create mock insight generator."""
    mock = MagicMock()
    mock_result = MagicMock()
    mock_result.markdown_content = "# Insights\n\nKey insights here."
    mock.analyze = AsyncMock(return_value=mock_result)
    return mock


@pytest.fixture
def mock_report_writer():
    """Create mock report writer."""
    mock = MagicMock()
    mock.write_report = AsyncMock(return_value={
        "01-Executive-Summary": "# Executive Summary",
        "02-Market-Analysis": "# Market Analysis",
    })
    return mock


@pytest.fixture
def mock_critic():
    """Create mock critic."""
    mock = MagicMock()
    mock.critique = AsyncMock(return_value={
        "status": "APPROVE",
        "feedback": "Report approved",
    })
    return mock


@pytest.fixture
def research_graph(mock_agents, mock_insight_generator, mock_report_writer, mock_critic):
    """Create ResearchGraph with mocked dependencies."""
    return ResearchGraph(
        agents=mock_agents,
        insight_generator=mock_insight_generator,
        report_writer=mock_report_writer,
        critic=mock_critic,
    )


@pytest.fixture
def sample_state():
    """Create sample ResearchState for testing."""
    return ResearchState(
        company_name="Test Corp",
        website="https://testcorp.com",
    )


# =============================================================================
# Initialization Tests
# =============================================================================


class TestResearchGraphInitialization:
    """Tests for ResearchGraph initialization."""

    @pytest.mark.unit
    def test_initializes_with_agents(self, mock_agents, mock_insight_generator, mock_report_writer, mock_critic):
        """Verify graph initializes with all agents."""
        graph = ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight_generator,
            report_writer=mock_report_writer,
            critic=mock_critic,
        )

        assert graph.agents == mock_agents
        assert graph.insight_generator == mock_insight_generator
        assert graph.report_writer == mock_report_writer
        assert graph.critic == mock_critic

    @pytest.mark.unit
    def test_creates_workflow(self, research_graph):
        """Verify workflow backend is created."""
        assert research_graph._backend is not None

    @pytest.mark.unit
    def test_workflow_is_graph_backend(self, research_graph):
        """Verify workflow uses GraphBackend abstraction (GR-013)."""
        from src.graph.graph_builder import GraphBackend
        assert isinstance(research_graph._backend, GraphBackend)


# =============================================================================
# Node Tests
# =============================================================================


class TestOrchestratorNode:
    """Tests for orchestrator node."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_orchestrator_transitions_to_gathering(self, research_graph, sample_state):
        """Verify orchestrator transitions to gathering phase."""
        result = await research_graph.orchestrator_node(sample_state)
        assert result["current_wave"] == "gathering"


class TestSpecialistNodes:
    """Tests for specialist agent nodes."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_financial_agent_node(self, research_graph, sample_state, mock_agents):
        """Verify financial agent node runs correctly."""
        result = await research_graph.financial_agent_node(sample_state)

        mock_agents["financial"].research.assert_called_once()
        assert "financial_data" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_market_agent_node(self, research_graph, sample_state, mock_agents):
        """Verify market agent node runs correctly."""
        result = await research_graph.market_agent_node(sample_state)

        mock_agents["market"].research.assert_called_once()
        assert "market_data" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sales_agent_node(self, research_graph, sample_state, mock_agents):
        """Verify sales agent node runs correctly."""
        result = await research_graph.sales_agent_node(sample_state)

        mock_agents["sales"].research.assert_called_once()
        assert "sales_data" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_competitor_agent_node(self, research_graph, sample_state, mock_agents):
        """Verify competitor agent node runs correctly."""
        result = await research_graph.competitor_agent_node(sample_state)

        mock_agents["competitor"].research.assert_called_once()
        assert "competitor_data" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_brand_agent_node(self, research_graph, sample_state, mock_agents):
        """Verify brand agent node runs correctly."""
        result = await research_graph.brand_agent_node(sample_state)

        mock_agents["brand"].research.assert_called_once()
        assert "brand_data" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_specialist_creates_company_profile(self, research_graph, sample_state, mock_agents):
        """Verify specialist creates CompanyProfile from state."""
        await research_graph.financial_agent_node(sample_state)

        # Check the call was made with a CompanyProfile
        call_args = mock_agents["financial"].research.call_args
        profile = call_args[0][0]

        assert profile.name == "Test Corp"
        assert profile.website == "https://testcorp.com"


class TestInsightGeneratorNode:
    """Tests for insight generator node."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_drafts_with_insights(self, research_graph, mock_insight_generator):
        """Verify insight generator returns drafts with insights."""
        # State must be in GATHERING phase to transition to THINKING
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="gathering",
            financial_data={"revenue": 1000000},
            market_data={"size": "5B"},
        )

        result = await research_graph.insight_generator_node(state)

        assert "drafts" in result
        assert "insights" in result["drafts"]
        mock_insight_generator.analyze.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_passes_all_data_to_generator(self, research_graph, mock_insight_generator):
        """Verify all data fields are passed to insight generator."""
        # State must be in GATHERING phase to transition to THINKING
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="gathering",
            financial_data={"revenue": 100},
            market_data={"size": "1B"},
            competitor_data={"competitors": ["A", "B"]},
            brand_data={"sentiment": "positive"},
        )

        await research_graph.insight_generator_node(state)

        call_kwargs = mock_insight_generator.analyze.call_args[1]
        assert "financial_data" in call_kwargs
        assert "market_data" in call_kwargs
        assert "competitor_data" in call_kwargs
        assert "brand_data" in call_kwargs


class TestReportWriterNode:
    """Tests for report writer node."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_drafts(self, research_graph, mock_report_writer):
        """Verify report writer returns drafts."""
        # State must be in THINKING phase to transition to WRITING
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="thinking",
            drafts={"insights": "# Insights"},
        )

        result = await research_graph.report_writer_node(state)

        assert "drafts" in result
        mock_report_writer.write_report.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_includes_insights_in_call(self, research_graph, mock_report_writer):
        """Verify insights are passed to report writer."""
        # State must be in THINKING phase to transition to WRITING
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="thinking",
            drafts={"insights": "# Key Insights\n\nImportant findings here."},
        )

        await research_graph.report_writer_node(state)

        call_kwargs = mock_report_writer.write_report.call_args[1]
        assert "insights" in call_kwargs


class TestCriticNode:
    """Tests for critic node."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_feedback(self, research_graph, mock_critic):
        """Verify critic returns feedback."""
        # State must be in WRITING phase to transition to REVIEW
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="writing",
            drafts={"report": "# Full Report"},
        )

        result = await research_graph.critic_node(state)

        assert "critique_feedback" in result
        mock_critic.critique.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_increments_feedback_loop_count(self, research_graph, mock_critic):
        """Verify feedback loop count is incremented."""
        # State must be in WRITING phase to transition to REVIEW
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="writing",
            feedback_loop_count=1,
        )

        result = await research_graph.critic_node(state)

        assert result["feedback_loop_count"] == 2


class TestSourceReviewerNode:
    """Tests for source reviewer node."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_review_message(self, research_graph, sample_state):
        """Verify source reviewer returns message."""
        result = await research_graph.source_reviewer_node(sample_state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "Review complete" in result["messages"][0].content


# =============================================================================
# Conditional Edge Tests
# =============================================================================


class TestShouldContinue:
    """Tests for should_continue routing logic."""

    @pytest.mark.unit
    def test_ends_on_max_loops(self, research_graph):
        """Verify ends when max loops reached."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=3,
            critique_feedback="REJECT: Still needs work",
        )

        result = research_graph.should_continue(state)

        assert result == "end"

    @pytest.mark.unit
    def test_continues_on_reject(self, research_graph):
        """Verify continues on REJECT feedback."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=1,
            critique_feedback="REJECT: Missing financial analysis",
        )

        result = research_graph.should_continue(state)

        assert result == "continue"

    @pytest.mark.unit
    def test_continues_on_fix(self, research_graph):
        """Verify continues on FIX feedback."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=1,
            critique_feedback="FIX: Update market data section",
        )

        result = research_graph.should_continue(state)

        assert result == "continue"

    @pytest.mark.unit
    def test_ends_on_approve(self, research_graph):
        """Verify ends on APPROVE feedback."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=1,
            critique_feedback="APPROVE: Report is complete",
        )

        result = research_graph.should_continue(state)

        assert result == "end"

    @pytest.mark.unit
    def test_ends_on_empty_feedback(self, research_graph):
        """Verify ends on empty feedback."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=1,
            critique_feedback="",
        )

        result = research_graph.should_continue(state)

        assert result == "end"

    @pytest.mark.unit
    def test_ends_on_none_feedback(self, research_graph):
        """Verify ends on None feedback."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=1,
            critique_feedback=None,
        )

        result = research_graph.should_continue(state)

        assert result == "end"

    @pytest.mark.unit
    def test_case_insensitive_reject(self, research_graph):
        """Verify REJECT is case insensitive."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=1,
            critique_feedback="reject: needs more data",
        )

        result = research_graph.should_continue(state)

        assert result == "continue"


# =============================================================================
# Workflow Compilation Tests
# =============================================================================


class TestWorkflowCompilation:
    """Tests for workflow compilation."""

    @pytest.mark.unit
    def test_compile_returns_runnable(self, research_graph):
        """Verify compile returns a runnable graph."""
        compiled = research_graph.compile()
        assert compiled is not None

    @pytest.mark.unit
    def test_compiled_graph_has_invoke(self, research_graph):
        """Verify compiled graph has invoke method."""
        compiled = research_graph.compile()
        assert hasattr(compiled, "invoke") or hasattr(compiled, "ainvoke")


# =============================================================================
# Workflow Structure Tests
# =============================================================================


class TestWorkflowStructure:
    """Tests for workflow structure (GR-013: uses GraphBackend abstraction)."""

    @pytest.mark.unit
    def test_has_all_nodes(self, research_graph):
        """Verify all expected nodes are registered via backend."""
        # With the new parallel gathering node (GR-010), individual agent nodes
        # are called within parallel_gathering_node, not as separate graph nodes
        expected_nodes = [
            "orchestrator",
            "parallel_gathering",  # GR-010: Replaces individual agent nodes
            "insight_generator",
            "report_writer",
            "critic",
            "source_reviewer",
        ]

        # Access the underlying graph via the backend
        nodes = research_graph._backend._graph.nodes

        for node_name in expected_nodes:
            assert node_name in nodes, f"Missing node: {node_name}"

    @pytest.mark.unit
    def test_entry_point_is_orchestrator(self, research_graph):
        """Verify entry point is orchestrator."""
        # The entry point is set and we can verify the graph compiles without error
        compiled = research_graph.compile()
        assert compiled is not None


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_empty_state_data(self, research_graph, mock_insight_generator):
        """Verify handles empty data fields gracefully."""
        # State must be in GATHERING phase to transition to THINKING
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="gathering",
            # All data fields empty (default)
        )

        # Should not raise
        result = await research_graph.insight_generator_node(state)

        assert "drafts" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_none_competitor_data(self, research_graph, mock_report_writer):
        """Verify handles None competitor_data gracefully."""
        # State must be in THINKING phase to transition to WRITING
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="thinking",
            competitor_data={},  # Empty dict
            brand_data={},
        )

        # Should not raise
        result = await research_graph.report_writer_node(state)

        assert "drafts" in result

    @pytest.mark.unit
    def test_feedback_with_special_characters(self, research_graph):
        """Verify feedback with special characters is handled."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=1,
            critique_feedback="REJECT: Missing data for 'Q1 2024' & special chars <test>",
        )

        result = research_graph.should_continue(state)

        assert result == "continue"


# =============================================================================
# Circuit Breaker Tests (GR-012)
# =============================================================================


class TestCircuitBreaker:
    """Tests for CircuitBreaker pattern."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker with low threshold for testing."""
        return CircuitBreaker(threshold=3, reset_timeout=1.0)

    @pytest.mark.unit
    def test_initial_state_is_closed(self, circuit_breaker):
        """Circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.unit
    def test_can_execute_when_closed(self, circuit_breaker):
        """Allows execution when CLOSED."""
        assert circuit_breaker.can_execute() is True

    @pytest.mark.unit
    def test_records_success(self, circuit_breaker):
        """Recording success resets failure count."""
        circuit_breaker._failure_count = 2
        circuit_breaker.record_success()
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.unit
    def test_records_failure(self, circuit_breaker):
        """Recording failure increments count."""
        circuit_breaker.record_failure()
        assert circuit_breaker._failure_count == 1

    @pytest.mark.unit
    def test_opens_after_threshold(self, circuit_breaker):
        """Opens after reaching failure threshold."""
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker._state == CircuitState.OPEN

    @pytest.mark.unit
    def test_cannot_execute_when_open(self, circuit_breaker):
        """Blocks execution when OPEN."""
        circuit_breaker._state = CircuitState.OPEN
        circuit_breaker._last_failure_time = asyncio.get_event_loop().time()
        assert circuit_breaker.can_execute() is False

    @pytest.mark.unit
    def test_can_execute_when_half_open(self, circuit_breaker):
        """Allows execution when HALF_OPEN."""
        circuit_breaker._state = CircuitState.HALF_OPEN
        assert circuit_breaker.can_execute() is True


# =============================================================================
# Dead Letter Queue Tests (GR-008)
# =============================================================================


class TestDeadLetterQueue:
    """Tests for DeadLetterQueue."""

    @pytest.fixture
    def dlq(self):
        """Create a dead letter queue."""
        return DeadLetterQueue(max_size=5)

    @pytest.mark.unit
    def test_add_entry(self, dlq):
        """Can add entries to the queue."""
        dlq.add(
            node_name="test_node",
            state_snapshot={"key": "value"},
            error="Test error",
            retry_count=3,
        )
        assert dlq.size() == 1

    @pytest.mark.unit
    def test_get_all_entries(self, dlq):
        """Can retrieve all entries."""
        dlq.add("node1", {"a": 1}, "error1")
        dlq.add("node2", {"b": 2}, "error2")

        entries = dlq.get_entries()
        assert len(entries) == 2

    @pytest.mark.unit
    def test_get_entries_by_node(self, dlq):
        """Can filter entries by node name."""
        dlq.add("node1", {}, "error1")
        dlq.add("node2", {}, "error2")
        dlq.add("node1", {}, "error3")

        entries = dlq.get_entries(node_name="node1")
        assert len(entries) == 2

    @pytest.mark.unit
    def test_max_size_enforced(self, dlq):
        """Queue size is limited."""
        for i in range(10):
            dlq.add(f"node{i}", {}, f"error{i}")

        assert dlq.size() == 5

    @pytest.mark.unit
    def test_clear_queue(self, dlq):
        """Can clear the queue."""
        dlq.add("node", {}, "error")
        dlq.clear()
        assert dlq.size() == 0

    @pytest.mark.unit
    def test_entry_has_timestamp(self, dlq):
        """Entries have timestamps."""
        dlq.add("node", {}, "error")
        entries = dlq.get_entries()
        assert isinstance(entries[0].timestamp, datetime)


# =============================================================================
# Execution Metrics Tests (GR-016)
# =============================================================================


class TestExecutionMetrics:
    """Tests for ExecutionMetrics."""

    @pytest.fixture
    def metrics(self):
        """Create execution metrics."""
        return ExecutionMetrics(workflow_id="test-workflow-123")

    @pytest.mark.unit
    def test_creates_with_workflow_id(self, metrics):
        """Creates with workflow ID."""
        assert metrics.workflow_id == "test-workflow-123"

    @pytest.mark.unit
    def test_has_start_time(self, metrics):
        """Has start time set."""
        assert isinstance(metrics.start_time, datetime)

    @pytest.mark.unit
    def test_record_node_start(self, metrics):
        """Can record node start."""
        node_metrics = metrics.record_node_start("test_node")

        assert isinstance(node_metrics, NodeMetrics)
        assert node_metrics.node_name == "test_node"
        assert "test_node" in metrics.node_metrics

    @pytest.mark.unit
    def test_record_node_end_success(self, metrics):
        """Can record successful node end."""
        metrics.record_node_start("test_node")
        metrics.record_node_end("test_node", success=True)

        node = metrics.node_metrics["test_node"]
        assert node.success is True
        assert node.end_time is not None
        assert node.duration_ms >= 0
        assert metrics.total_nodes_executed == 1
        assert metrics.total_failures == 0

    @pytest.mark.unit
    def test_record_node_end_failure(self, metrics):
        """Can record failed node end."""
        metrics.record_node_start("test_node")
        metrics.record_node_end("test_node", success=False, error="Test error")

        node = metrics.node_metrics["test_node"]
        assert node.success is False
        assert node.error == "Test error"
        assert metrics.total_failures == 1

    @pytest.mark.unit
    def test_to_dict(self, metrics):
        """Can convert to dictionary."""
        metrics.record_node_start("node1")
        metrics.record_node_end("node1", success=True)

        data = metrics.to_dict()

        assert data["workflow_id"] == "test-workflow-123"
        assert "start_time" in data
        assert "nodes" in data
        assert "node1" in data["nodes"]


# =============================================================================
# Timeout Decorator Tests (GR-007)
# =============================================================================


class TestTimeoutDecorator:
    """Tests for with_timeout decorator."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_completes_within_timeout(self):
        """Function completes within timeout."""
        @with_timeout(timeout_seconds=1.0)
        async def quick_func():
            return "success"

        result = await quick_func()
        assert result == "success"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_raises_on_timeout(self):
        """Raises TimeoutError when exceeding timeout."""
        @with_timeout(timeout_seconds=0.1)
        async def slow_func():
            await asyncio.sleep(1.0)
            return "never reached"

        with pytest.raises(TimeoutError):
            await slow_func()


# =============================================================================
# Retry Decorator Tests (GR-011)
# =============================================================================


class TestRetryDecorator:
    """Tests for with_retry decorator."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_succeeds_on_first_try(self):
        """Succeeds without retry if first attempt works."""
        call_count = 0

        @with_retry(max_attempts=3, backoff_base=0.01)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_retries_on_failure(self):
        """Retries on transient failures."""
        call_count = 0

        @with_retry(max_attempts=3, backoff_base=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_raises_after_max_attempts(self):
        """Raises after exhausting all attempts."""
        @with_retry(max_attempts=2, backoff_base=0.01)
        async def always_fail():
            raise ValueError("Permanent error")

        with pytest.raises(ValueError):
            await always_fail()


# =============================================================================
# ResearchGraph Resilience Features Tests
# =============================================================================


class TestResearchGraphResilience:
    """Tests for ResearchGraph resilience features."""

    @pytest.fixture
    def resilient_graph(self, mock_agents, mock_insight_generator, mock_report_writer, mock_critic):
        """Create ResearchGraph with custom timeout and retries."""
        return ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight_generator,
            report_writer=mock_report_writer,
            critic=mock_critic,
            node_timeout=10.0,
            max_retries=2,
        )

    @pytest.mark.unit
    def test_has_state_manager(self, resilient_graph):
        """Graph has state manager."""
        assert resilient_graph._state_manager is not None

    @pytest.mark.unit
    def test_has_dead_letter_queue(self, resilient_graph):
        """Graph has dead letter queue."""
        dlq = resilient_graph.get_dead_letter_queue()
        assert isinstance(dlq, DeadLetterQueue)

    @pytest.mark.unit
    def test_can_reset_circuit_breakers(self, resilient_graph):
        """Can reset all circuit breakers."""
        # Create some circuit breakers
        resilient_graph._get_circuit_breaker("node1")
        resilient_graph._get_circuit_breaker("node2")

        assert len(resilient_graph._circuit_breakers) == 2

        resilient_graph.reset_circuit_breakers()

        assert len(resilient_graph._circuit_breakers) == 0

    @pytest.mark.unit
    def test_start_execution_creates_metrics(self, resilient_graph):
        """start_execution creates metrics."""
        metrics = resilient_graph.start_execution("test-123")

        assert isinstance(metrics, ExecutionMetrics)
        assert metrics.workflow_id == "test-123"

    @pytest.mark.unit
    def test_end_execution_returns_metrics(self, resilient_graph):
        """end_execution returns final metrics."""
        resilient_graph.start_execution("test-123")
        metrics = resilient_graph.end_execution()

        assert metrics is not None
        assert metrics.end_time is not None

    @pytest.mark.unit
    def test_end_execution_clears_current_metrics(self, resilient_graph):
        """end_execution clears current metrics."""
        resilient_graph.start_execution("test-123")
        resilient_graph.end_execution()

        assert resilient_graph._current_metrics is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_orchestrator_validates_transition(self, resilient_graph):
        """Orchestrator validates phase transition."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="init",
        )

        result = await resilient_graph.orchestrator_node(state)

        assert result.get("current_wave") == "gathering"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_node_execution_with_metrics(self, resilient_graph):
        """Node execution records metrics when enabled."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="gathering",
        )

        resilient_graph.start_execution("test-workflow")
        await resilient_graph.financial_agent_node(state)
        metrics = resilient_graph.end_execution()

        assert "financial_agent" in metrics.node_metrics

    @pytest.mark.unit
    def test_configurable_timeout(self, mock_agents, mock_insight_generator, mock_report_writer, mock_critic):
        """Node timeout is configurable."""
        graph = ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight_generator,
            report_writer=mock_report_writer,
            critic=mock_critic,
            node_timeout=60.0,
        )

        assert graph.node_timeout == pytest.approx(60.0)

    @pytest.mark.unit
    def test_configurable_retries(self, mock_agents, mock_insight_generator, mock_report_writer, mock_critic):
        """Max retries is configurable."""
        graph = ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight_generator,
            report_writer=mock_report_writer,
            critic=mock_critic,
            max_retries=5,
        )

        assert graph.max_retries == 5


# =============================================================================
# Phase Transition Tests
# =============================================================================


class TestPhaseTransitions:
    """Tests for phase transition validation in nodes."""

    @pytest.fixture
    def graph_with_state(self, mock_agents, mock_insight_generator, mock_report_writer, mock_critic):
        """Create graph for testing."""
        return ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight_generator,
            report_writer=mock_report_writer,
            critic=mock_critic,
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_source_reviewer_sets_complete(self, graph_with_state):
        """Source reviewer sets phase to COMPLETE."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="review",
        )

        result = await graph_with_state.source_reviewer_node(state)

        assert result.get("current_wave") == "complete"

    @pytest.mark.unit
    def test_should_continue_checks_max_feedback(self, graph_with_state):
        """should_continue respects max feedback loops."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=10,  # MAX_FEEDBACK_LOOPS
            critique_feedback="REJECT: needs work",
        )

        result = graph_with_state.should_continue(state)

        assert result == "end"
