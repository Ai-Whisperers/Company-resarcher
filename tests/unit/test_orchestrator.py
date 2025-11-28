"""
Unit tests for ResearchOrchestrator.

Tests the orchestrator including:
- Initialization
- Dependency injection
- Research execution
- Singleton pattern
- Error handling
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import threading

from src.agents.orchestrator import (
    ResearchOrchestrator,
    get_orchestrator,
    reset_orchestrator,
)
from src.graph.state import ResearchState


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Mock response")
    return client


@pytest.fixture
def mock_agent_factory():
    """Create a mock agent factory."""
    with patch("src.agents.orchestrator.AgentFactory") as mock_factory_class:
        mock_factory = MagicMock()

        # Mock specialists
        mock_specialists = {
            "financial": MagicMock(),
            "market": MagicMock(),
            "sales": MagicMock(),
            "competitor": MagicMock(),
            "brand": MagicMock(),
        }
        mock_factory.create_specialists.return_value = mock_specialists

        # Mock other agents
        mock_factory.create_insight_generator.return_value = MagicMock()
        mock_factory.create_report_writer.return_value = MagicMock()
        mock_factory.create_critic.return_value = MagicMock()

        mock_factory_class.return_value = mock_factory
        yield mock_factory_class


@pytest.fixture
def mock_research_graph():
    """Create a mock research graph."""
    with patch("src.agents.orchestrator.ResearchGraph") as mock_graph_class:
        mock_graph = MagicMock()
        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={
            "company_name": "Test Corp",
            "website": "https://test.com",
            "drafts": {"report": "# Final Report"},
            "raw_data": [],
            "source_log": [],
            "financial_data": {},
            "market_data": {},
            "sales_data": {},
            "competitor_data": {},
            "brand_data": {},
            "current_wave": "review",
            "messages": [],
            "errors": [],
            "critique_feedback": None,
            "feedback_loop_count": 1,
        })
        mock_graph.compile.return_value = mock_compiled
        mock_graph_class.return_value = mock_graph
        yield mock_graph_class


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset orchestrator singleton before each test."""
    reset_orchestrator()
    yield
    reset_orchestrator()


# =============================================================================
# Initialization Tests
# =============================================================================


class TestOrchestratorInitialization:
    """Tests for ResearchOrchestrator initialization."""

    @pytest.mark.unit
    def test_creates_agent_factory(self, mock_agent_factory, mock_research_graph):
        """Verify orchestrator creates agent factory."""
        orchestrator = ResearchOrchestrator()

        mock_agent_factory.assert_called_once()

    @pytest.mark.unit
    def test_creates_specialists(self, mock_agent_factory, mock_research_graph):
        """Verify orchestrator creates all specialists."""
        orchestrator = ResearchOrchestrator()

        factory_instance = mock_agent_factory.return_value
        factory_instance.create_specialists.assert_called_once()

    @pytest.mark.unit
    def test_creates_insight_generator(self, mock_agent_factory, mock_research_graph):
        """Verify orchestrator creates insight generator."""
        orchestrator = ResearchOrchestrator()

        factory_instance = mock_agent_factory.return_value
        factory_instance.create_insight_generator.assert_called_once()

    @pytest.mark.unit
    def test_creates_report_writer(self, mock_agent_factory, mock_research_graph):
        """Verify orchestrator creates report writer."""
        orchestrator = ResearchOrchestrator()

        factory_instance = mock_agent_factory.return_value
        factory_instance.create_report_writer.assert_called_once()

    @pytest.mark.unit
    def test_creates_critic(self, mock_agent_factory, mock_research_graph):
        """Verify orchestrator creates critic."""
        orchestrator = ResearchOrchestrator()

        factory_instance = mock_agent_factory.return_value
        factory_instance.create_critic.assert_called_once()

    @pytest.mark.unit
    def test_compiles_graph(self, mock_agent_factory, mock_research_graph):
        """Verify orchestrator compiles the graph."""
        orchestrator = ResearchOrchestrator()

        mock_graph_instance = mock_research_graph.return_value
        mock_graph_instance.compile.assert_called_once()

    @pytest.mark.unit
    def test_passes_ai_client_to_factory(self, mock_agent_factory, mock_research_graph, mock_ai_client):
        """Verify AI client is passed to factory."""
        orchestrator = ResearchOrchestrator(ai_client=mock_ai_client)

        mock_agent_factory.assert_called_once_with(
            ai_client=mock_ai_client,
            use_local_tools=False,
        )

    @pytest.mark.unit
    def test_passes_use_local_tools_to_factory(self, mock_agent_factory, mock_research_graph):
        """Verify use_local_tools is passed to factory."""
        orchestrator = ResearchOrchestrator(use_local_tools=True)

        mock_agent_factory.assert_called_once_with(
            ai_client=None,
            use_local_tools=True,
        )


# =============================================================================
# Research Execution Tests
# =============================================================================


class TestConductResearch:
    """Tests for conduct_research method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_creates_initial_state(self, mock_agent_factory, mock_research_graph):
        """Verify initial state is created correctly."""
        orchestrator = ResearchOrchestrator()

        result = await orchestrator.conduct_research(
            company_name="Test Corp",
            url="https://testcorp.com",
        )

        # Verify graph was invoked
        compiled = mock_research_graph.return_value.compile.return_value
        compiled.ainvoke.assert_called_once()

        # Check initial state
        call_args = compiled.ainvoke.call_args[0][0]
        assert call_args["company_name"] == "Test Corp"
        assert call_args["website"] == "https://testcorp.com"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_final_state_dict(self, mock_agent_factory, mock_research_graph):
        """Verify final state is returned as dict."""
        orchestrator = ResearchOrchestrator()

        result = await orchestrator.conduct_research(
            company_name="Test Corp",
            url="https://testcorp.com",
        )

        assert isinstance(result, dict)
        assert "company_name" in result
        assert "drafts" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_empty_url(self, mock_agent_factory, mock_research_graph):
        """Verify empty URL is handled."""
        orchestrator = ResearchOrchestrator()

        result = await orchestrator.conduct_research(
            company_name="Test Corp",
            url="",
        )

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_propagates_exceptions(self, mock_agent_factory, mock_research_graph):
        """Verify exceptions are propagated."""
        orchestrator = ResearchOrchestrator()

        compiled = mock_research_graph.return_value.compile.return_value
        compiled.ainvoke.side_effect = Exception("Graph execution failed")

        with pytest.raises(Exception) as exc_info:
            await orchestrator.conduct_research(
                company_name="Test Corp",
                url="https://testcorp.com",
            )

        assert "Graph execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_keyboard_interrupt(self, mock_agent_factory, mock_research_graph):
        """Verify KeyboardInterrupt is propagated."""
        orchestrator = ResearchOrchestrator()

        compiled = mock_research_graph.return_value.compile.return_value
        compiled.ainvoke.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            await orchestrator.conduct_research(
                company_name="Test Corp",
                url="https://testcorp.com",
            )


# =============================================================================
# Singleton Pattern Tests
# =============================================================================


class TestOrchestratorSingleton:
    """Tests for singleton pattern."""

    @pytest.mark.unit
    def test_get_orchestrator_creates_instance(self, mock_agent_factory, mock_research_graph):
        """Verify get_orchestrator creates instance."""
        orchestrator = get_orchestrator()

        assert orchestrator is not None
        assert isinstance(orchestrator, ResearchOrchestrator)

    @pytest.mark.unit
    def test_get_orchestrator_returns_same_instance(self, mock_agent_factory, mock_research_graph):
        """Verify get_orchestrator returns same instance."""
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()

        assert orchestrator1 is orchestrator2

    @pytest.mark.unit
    def test_reset_orchestrator_clears_instance(self, mock_agent_factory, mock_research_graph):
        """Verify reset_orchestrator clears the singleton."""
        orchestrator1 = get_orchestrator()
        reset_orchestrator()
        orchestrator2 = get_orchestrator()

        # Should be different instances after reset
        assert orchestrator1 is not orchestrator2

    @pytest.mark.unit
    def test_singleton_thread_safety(self, mock_agent_factory, mock_research_graph):
        """Verify singleton is thread-safe."""
        instances = []
        errors = []

        def get_instance():
            try:
                instance = get_orchestrator()
                instances.append(instance)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0

        # All instances should be the same
        assert len(set(id(i) for i in instances)) == 1


# =============================================================================
# Edge Cases
# =============================================================================


class TestOrchestratorEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unicode_company_name(self, mock_agent_factory, mock_research_graph):
        """Verify unicode company names are handled."""
        orchestrator = ResearchOrchestrator()

        result = await orchestrator.conduct_research(
            company_name="测试公司",
            url="https://test.com",
        )

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_special_characters_in_name(self, mock_agent_factory, mock_research_graph):
        """Verify special characters in company name are handled."""
        orchestrator = ResearchOrchestrator()

        result = await orchestrator.conduct_research(
            company_name="Test & Co., Inc. 'Quoted'",
            url="https://test.com",
        )

        assert result is not None

    @pytest.mark.unit
    def test_first_argument_takes_precedence_for_singleton(self, mock_agent_factory, mock_research_graph, mock_ai_client):
        """Verify first call configuration is used for singleton."""
        # First call with custom client
        orchestrator1 = get_orchestrator(ai_client=mock_ai_client)

        # Second call with different settings - should return same instance
        orchestrator2 = get_orchestrator(use_local_tools=True)

        assert orchestrator1 is orchestrator2
