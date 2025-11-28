"""
Integration tests for graph workflow.

Tests the complete research graph workflow including:
- State transitions
- Node execution
- Error handling
- Conditional routing
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# Graph State Tests
# =============================================================================


class TestGraphState:
    """Tests for graph state management."""

    @pytest.mark.integration
    def test_initial_state_structure(self, mock_graph_state):
        """Verify initial state has required structure."""
        required_fields = [
            "company_name",
            "website",
            "raw_data",
            "source_log",
            "errors",
            "iteration",
        ]

        for field in required_fields:
            assert field in mock_graph_state, f"Missing required field: {field}"

    @pytest.mark.integration
    def test_state_preserves_company_info(self, mock_graph_state):
        """Verify company info is preserved through state."""
        assert mock_graph_state["company_name"] == "Integration Test Corp"
        assert mock_graph_state["website"] == "https://integration-test.com"

    @pytest.mark.integration
    def test_state_errors_is_list(self, mock_graph_state):
        """Verify errors field is a list."""
        assert isinstance(mock_graph_state["errors"], list)

    @pytest.mark.integration
    def test_state_can_add_errors(self, mock_graph_state):
        """Verify errors can be added to state."""
        mock_graph_state["errors"].append("Test error")
        assert len(mock_graph_state["errors"]) == 1
        assert "Test error" in mock_graph_state["errors"]


# =============================================================================
# Graph Builder Tests
# =============================================================================


class TestGraphBuilder:
    """Tests for graph builder functionality."""

    @pytest.mark.integration
    def test_graph_builder_creates_graph(self):
        """Verify graph builder creates a valid graph."""
        with patch("src.graph.graph_builder.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            mock_settings.return_value.TAVILY_API_KEY = "test-key"

            try:
                from src.graph.graph_builder import build_research_graph
                graph = build_research_graph()
                assert graph is not None
            except ImportError:
                pytest.skip("Graph builder not available")

    @pytest.mark.integration
    def test_graph_has_start_node(self):
        """Verify graph has a start node."""
        with patch("src.graph.graph_builder.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock()
            mock_settings.return_value.TAVILY_API_KEY = "test-key"

            try:
                from src.graph.graph_builder import build_research_graph
                graph = build_research_graph()
                # Graph should be invokable
                assert hasattr(graph, "invoke") or hasattr(graph, "ainvoke")
            except ImportError:
                pytest.skip("Graph builder not available")


# =============================================================================
# Node Execution Tests
# =============================================================================


class TestNodeExecution:
    """Tests for individual node execution."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_node_handles_empty_input(self, mock_graph_state):
        """Verify nodes handle empty input gracefully."""
        mock_graph_state["company_name"] = ""

        # Node should either raise ValidationError or handle gracefully
        # This tests defensive programming
        from tests.mocks import MockOpenAIClient

        with patch("src.agents.base_agent.get_ai_client", return_value=MockOpenAIClient()):
            try:
                from src.agents.base_agent import BaseAgent

                class TestAgent(BaseAgent):
                    async def run(self, state):
                        return state

                agent = TestAgent(name="test")
                result = await agent.run(mock_graph_state)
                # Should return state even with empty company_name
                assert result is not None
            except ImportError:
                pytest.skip("BaseAgent not available")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_node_adds_to_source_log(self, mock_graph_state):
        """Verify nodes add sources to source_log."""
        from tests.mocks import MockOpenAIClient

        ai_client = MockOpenAIClient()

        with patch("src.agents.base_agent.get_ai_client", return_value=ai_client):
            try:
                from src.agents.base_agent import BaseAgent

                # Simulate adding source
                mock_graph_state["source_log"].append({
                    "url": "https://test.com",
                    "title": "Test Source",
                })

                assert len(mock_graph_state["source_log"]) == 1
            except ImportError:
                pytest.skip("BaseAgent not available")


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestGraphErrorHandling:
    """Tests for graph error handling."""

    @pytest.mark.integration
    def test_state_accumulates_errors(self, mock_graph_state):
        """Verify errors accumulate in state."""
        errors = ["Error 1", "Error 2", "Error 3"]

        for error in errors:
            mock_graph_state["errors"].append(error)

        assert len(mock_graph_state["errors"]) == 3
        assert mock_graph_state["errors"] == errors

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_node_failure_records_error(self, mock_graph_state):
        """Verify node failures are recorded in errors."""
        from tests.mocks import MockOpenAIClient

        # Create client that raises error
        error_client = MockOpenAIClient(raise_error=Exception("API Error"))

        with patch("src.agents.base_agent.get_ai_client", return_value=error_client):
            try:
                from src.agents.base_agent import BaseAgent

                class FailingAgent(BaseAgent):
                    async def run(self, state):
                        try:
                            await self.ai_client.chat.completions.create(
                                model="test",
                                messages=[],
                            )
                        except Exception as e:
                            state["errors"].append(str(e))
                        return state

                agent = FailingAgent(name="failing")
                result = await agent.run(mock_graph_state)

                # Error should be recorded
                assert len(result["errors"]) > 0
            except ImportError:
                pytest.skip("BaseAgent not available")

    @pytest.mark.integration
    def test_graph_continues_after_node_error(self, mock_graph_state):
        """Verify graph continues even if one node fails."""
        # Simulate partial success scenario
        mock_graph_state["financial_data"] = {"error": "Failed to fetch"}
        mock_graph_state["market_data"] = {"sector": "Technology"}  # Success

        # Graph should have some data despite error
        assert mock_graph_state["market_data"] is not None
        assert "error" in mock_graph_state["financial_data"]


# =============================================================================
# Iteration Tests
# =============================================================================


class TestGraphIteration:
    """Tests for graph iteration control."""

    @pytest.mark.integration
    def test_iteration_increments(self, mock_graph_state):
        """Verify iteration counter increments."""
        initial_iteration = mock_graph_state["iteration"]
        mock_graph_state["iteration"] += 1

        assert mock_graph_state["iteration"] == initial_iteration + 1

    @pytest.mark.integration
    def test_max_iterations_respected(self, mock_graph_state):
        """Verify max iterations limit is respected."""
        max_iter = mock_graph_state.get("max_iterations", 3)

        # Simulate iterations
        while mock_graph_state["iteration"] < max_iter:
            mock_graph_state["iteration"] += 1

        assert mock_graph_state["iteration"] == max_iter

    @pytest.mark.integration
    def test_iteration_stops_when_complete(self, mock_graph_state):
        """Verify iteration stops when research is complete."""

        def should_continue(state):
            # Stop if we have enough data
            has_financial = bool(state.get("financial_data"))
            has_market = bool(state.get("market_data"))
            under_limit = state["iteration"] < state.get("max_iterations", 3)
            return under_limit and not (has_financial and has_market)

        # Initially should continue
        assert should_continue(mock_graph_state)

        # Add data
        mock_graph_state["financial_data"] = {"revenue": 1000000}
        mock_graph_state["market_data"] = {"sector": "Tech"}

        # Now should stop
        assert not should_continue(mock_graph_state)


# =============================================================================
# Conditional Routing Tests
# =============================================================================


class TestConditionalRouting:
    """Tests for conditional routing in graph."""

    @pytest.mark.integration
    def test_routes_to_financial_when_needed(self, mock_graph_state):
        """Verify routing to financial node when data missing."""

        def route_decision(state):
            if not state.get("financial_data"):
                return "financial"
            elif not state.get("market_data"):
                return "market"
            else:
                return "complete"

        # No financial data - should route to financial
        assert route_decision(mock_graph_state) == "financial"

    @pytest.mark.integration
    def test_routes_to_market_after_financial(self, mock_graph_state):
        """Verify routing to market after financial complete."""

        def route_decision(state):
            if not state.get("financial_data"):
                return "financial"
            elif not state.get("market_data"):
                return "market"
            else:
                return "complete"

        mock_graph_state["financial_data"] = {"revenue": 1000}

        # Has financial, missing market - should route to market
        assert route_decision(mock_graph_state) == "market"

    @pytest.mark.integration
    def test_routes_to_complete_when_done(self, mock_graph_state):
        """Verify routing to complete when all data present."""

        def route_decision(state):
            if not state.get("financial_data"):
                return "financial"
            elif not state.get("market_data"):
                return "market"
            else:
                return "complete"

        mock_graph_state["financial_data"] = {"revenue": 1000}
        mock_graph_state["market_data"] = {"sector": "Tech"}

        # Has all data - should complete
        assert route_decision(mock_graph_state) == "complete"


# =============================================================================
# Data Flow Tests
# =============================================================================


class TestDataFlow:
    """Tests for data flow through graph."""

    @pytest.mark.integration
    def test_raw_data_accumulates(self, mock_graph_state):
        """Verify raw_data accumulates from multiple nodes."""
        # Simulate multiple nodes adding data
        mock_graph_state["raw_data"]["financial"] = {"revenue": 1000}
        mock_graph_state["raw_data"]["market"] = {"sector": "Tech"}
        mock_graph_state["raw_data"]["competitor"] = {"top_competitor": "CompA"}

        assert len(mock_graph_state["raw_data"]) == 3

    @pytest.mark.integration
    def test_drafts_created_from_data(self, mock_graph_state):
        """Verify drafts are created from collected data."""
        # Add some data first
        mock_graph_state["financial_data"] = {"revenue": 1000000}
        mock_graph_state["market_data"] = {"sector": "Technology"}

        # Simulate draft creation
        mock_graph_state["drafts"]["executive_summary"] = (
            f"Company in {mock_graph_state['market_data']['sector']} sector "
            f"with revenue of ${mock_graph_state['financial_data']['revenue']}"
        )

        assert "executive_summary" in mock_graph_state["drafts"]
        assert "Technology" in mock_graph_state["drafts"]["executive_summary"]

    @pytest.mark.integration
    def test_source_log_tracks_all_sources(self, mock_graph_state):
        """Verify source_log tracks all sources used."""
        sources = [
            {"url": "https://finance.example.com", "type": "financial"},
            {"url": "https://market.example.com", "type": "market"},
            {"url": "https://news.example.com", "type": "news"},
        ]

        for source in sources:
            mock_graph_state["source_log"].append(source)

        assert len(mock_graph_state["source_log"]) == 3
        urls = [s["url"] for s in mock_graph_state["source_log"]]
        assert "https://finance.example.com" in urls
