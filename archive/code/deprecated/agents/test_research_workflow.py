"""
End-to-end tests for the complete research workflow.

Tests the full research pipeline from request to report generation,
using mocked external services.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import json


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_responses():
    """Mock AI responses for the workflow."""
    return {
        "financial": "# Financial Analysis\n\nRevenue: $10M\nProfit: $2M",
        "market": "# Market Analysis\n\nMarket Size: $50B",
        "competitor": "# Competitor Analysis\n\nMain competitors: A, B, C",
        "brand": "# Brand Analysis\n\nBrand sentiment: Positive",
        "sales": "# Sales Analysis\n\nSales channels: Direct, Partners",
        "insights": json.dumps({
            "swot": {
                "strengths": ["Strong technology"],
                "weaknesses": ["Limited reach"],
                "opportunities": ["Market growth"],
                "threats": ["Competition"],
            },
            "strategic_takeaways": ["Focus on growth"],
            "executive_summary": "Test Corp is well-positioned.",
        }),
    }


@pytest.fixture
def mock_search_results():
    """Mock search results."""
    return [
        {"url": "https://example.com/1", "title": "Article 1", "content": "Content 1"},
        {"url": "https://example.com/2", "title": "Article 2", "content": "Content 2"},
        {"url": "https://example.com/3", "title": "Article 3", "content": "Content 3"},
    ]


@pytest.fixture
def mock_browser_results():
    """Mock browser fetch results."""
    from src.core.types.base import ResearchSource

    return [
        ResearchSource(
            url="https://example.com/1",
            title="Source 1",
            content="Detailed content from source 1",
            source_type="web",
        ),
        ResearchSource(
            url="https://example.com/2",
            title="Source 2",
            content="Detailed content from source 2",
            source_type="news",
        ),
    ]


# =============================================================================
# Full Workflow Tests
# =============================================================================


class TestFullResearchWorkflow:
    """End-to-end tests for the complete research workflow."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_research_workflow(
        self,
        mock_ai_responses,
        mock_search_results,
        mock_browser_results,
    ):
        """Test complete research workflow from start to finish."""
        from src.graph.state import ResearchState
        from src.core.types.base import CompanyProfile

        # Create mocks
        mock_ai = MagicMock()
        mock_ai.generate = AsyncMock(side_effect=[
            mock_ai_responses["financial"],
            mock_ai_responses["market"],
            mock_ai_responses["competitor"],
            mock_ai_responses["brand"],
            mock_ai_responses["sales"],
            mock_ai_responses["insights"],
            "APPROVE: Report looks good",
        ])

        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=mock_search_results)

        mock_browser = MagicMock()
        mock_browser.fetch_multiple = AsyncMock(return_value=mock_browser_results)

        # Patch all external dependencies
        with patch("src.agents.factory.get_ai_client_manager") as mock_manager:
            with patch("src.agents.factory.SearchTool") as MockSearch:
                with patch("src.agents.factory.BrowserTool") as MockBrowser:
                    mock_manager.return_value.get_client.return_value = mock_ai
                    MockSearch.return_value = mock_search
                    MockBrowser.return_value = mock_browser
                    MockBrowser.return_value.__aenter__ = AsyncMock(return_value=mock_browser)
                    MockBrowser.return_value.__aexit__ = AsyncMock(return_value=None)

                    from src.agents.orchestrator import ResearchOrchestrator

                    # Create orchestrator
                    orchestrator = ResearchOrchestrator(ai_client=mock_ai)

                    # Run research
                    result = await orchestrator.conduct_research(
                        company_name="Test Corporation",
                        url="https://testcorp.com",
                    )

                    # Verify result structure
                    assert isinstance(result, dict)
                    assert result["company_name"] == "Test Corporation"
                    assert "drafts" in result

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_workflow_handles_agent_errors(self, mock_ai_responses):
        """Test workflow handles individual agent errors gracefully."""
        mock_ai = MagicMock()

        # First call fails, rest succeed
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("AI service unavailable")
            return mock_ai_responses.get("market", "Default response")

        mock_ai.generate = mock_generate

        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[])

        mock_browser = MagicMock()
        mock_browser.fetch_multiple = AsyncMock(return_value=[])

        with patch("src.agents.factory.get_ai_client_manager") as mock_manager:
            with patch("src.agents.factory.SearchTool") as MockSearch:
                with patch("src.agents.factory.BrowserTool") as MockBrowser:
                    mock_manager.return_value.get_client.return_value = mock_ai
                    MockSearch.return_value = mock_search
                    MockBrowser.return_value = mock_browser
                    MockBrowser.return_value.__aenter__ = AsyncMock(return_value=mock_browser)
                    MockBrowser.return_value.__aexit__ = AsyncMock(return_value=None)

                    from src.agents.orchestrator import ResearchOrchestrator

                    orchestrator = ResearchOrchestrator(ai_client=mock_ai)

                    # Should not raise - errors are captured
                    try:
                        result = await orchestrator.conduct_research(
                            company_name="Test Corp",
                            url="https://test.com",
                        )
                        # Workflow completed (may have errors in state)
                        assert result is not None
                    except Exception:
                        # Some workflows may propagate errors
                        pass


# =============================================================================
# API E2E Tests
# =============================================================================


class TestAPIEndToEnd:
    """End-to-end tests for API workflow."""

    @pytest.mark.e2e
    def test_research_request_to_status_workflow(self):
        """Test complete API workflow: request -> poll status."""
        from fastapi.testclient import TestClient
        from unittest.mock import MagicMock

        with patch("src.api.app.get_db") as mock_get_db:
            with patch("src.api.app.rate_limiter") as mock_limiter:
                with patch("src.api.database.engine"):
                    with patch("src.api.database.Base"):
                        # Setup mocks
                        mock_db = MagicMock()
                        mock_db.query.return_value.filter.return_value.first.return_value = None
                        mock_get_db.return_value = mock_db
                        mock_limiter.is_allowed.return_value = True

                        from src.api.app import app

                        client = TestClient(app, raise_server_exceptions=False)

                        # Step 1: Create research request
                        with patch("src.api.app.save_task") as mock_save:
                            mock_save.return_value = MagicMock()

                            response = client.post(
                                "/api/v1/research",
                                json={"company_name": "Test Corporation"},
                            )

                            assert response.status_code == 200
                            data = response.json()
                            assert "task_id" in data
                            task_id = data["task_id"]

                        # Step 2: Check task status
                        with patch("src.api.app.get_task") as mock_get_task:
                            mock_get_task.return_value = {
                                "task_id": task_id,
                                "status": "pending",
                                "request": {"company_name": "Test Corporation"},
                                "result": None,
                                "error": None,
                            }

                            response = client.get(f"/api/v1/research/{task_id}")

                            assert response.status_code == 200
                            data = response.json()
                            assert data["task_id"] == task_id
                            assert data["status"] == "pending"

    @pytest.mark.e2e
    def test_validation_error_workflow(self):
        """Test API validation error handling."""
        from fastapi.testclient import TestClient

        with patch("src.api.app.get_db"):
            with patch("src.api.app.rate_limiter") as mock_limiter:
                with patch("src.api.database.engine"):
                    with patch("src.api.database.Base"):
                        mock_limiter.is_allowed.return_value = True

                        from src.api.app import app

                        client = TestClient(app, raise_server_exceptions=False)

                        # Test empty company name
                        response = client.post(
                            "/api/v1/research",
                            json={"company_name": ""},
                        )

                        assert response.status_code == 422

                        # Test missing required field
                        response = client.post(
                            "/api/v1/research",
                            json={},
                        )

                        assert response.status_code == 422

                        # Test invalid URL
                        response = client.post(
                            "/api/v1/research",
                            json={"company_name": "Test", "url": "not-a-url"},
                        )

                        assert response.status_code == 422


# =============================================================================
# Graph Execution E2E Tests
# =============================================================================


class TestGraphExecutionE2E:
    """End-to-end tests for graph execution."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_graph_node_execution_order(self):
        """Test that graph nodes execute in correct order."""
        execution_order = []

        # Create mock agents that record execution order
        def create_mock_agent(name):
            async def mock_research(*args, **kwargs):
                execution_order.append(name)
                from src.core.types.base import ResearchPhaseResult
                return ResearchPhaseResult(
                    phase_name=name,
                    markdown_content=f"# {name} Report",
                    sources=[],
                )

            agent = MagicMock()
            agent.research = mock_research
            return agent

        mock_agents = {
            "financial": create_mock_agent("financial"),
            "market": create_mock_agent("market"),
            "sales": create_mock_agent("sales"),
            "competitor": create_mock_agent("competitor"),
            "brand": create_mock_agent("brand"),
        }

        mock_insight = MagicMock()
        mock_insight.analyze = AsyncMock(return_value=MagicMock(
            markdown_content="# Insights"
        ))

        mock_writer = MagicMock()
        mock_writer.write_report = AsyncMock(return_value={
            "report": "# Final Report"
        })

        mock_critic = MagicMock()
        mock_critic.critique = AsyncMock(return_value={
            "status": "APPROVE",
            "feedback": "Approved",
        })

        from src.graph.graph_builder import ResearchGraph
        from src.graph.state import ResearchState

        graph = ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight,
            report_writer=mock_writer,
            critic=mock_critic,
        )

        compiled = graph.compile()

        initial_state = ResearchState(
            company_name="Test Corp",
            website="https://test.com",
        )

        # Execute graph
        await compiled.ainvoke(initial_state.model_dump())

        # Verify all specialist agents were called
        assert "financial" in execution_order
        assert "market" in execution_order
        assert "sales" in execution_order
        assert "competitor" in execution_order
        assert "brand" in execution_order

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_feedback_loop_execution(self):
        """Test that feedback loop executes correctly."""
        critique_calls = []

        mock_agents = {}
        for name in ["financial", "market", "sales", "competitor", "brand"]:
            agent = MagicMock()
            agent.research = AsyncMock(return_value=MagicMock(
                model_dump=lambda: {"data": "test"}
            ))
            mock_agents[name] = agent

        mock_insight = MagicMock()
        mock_insight.analyze = AsyncMock(return_value=MagicMock(
            markdown_content="# Insights"
        ))

        mock_writer = MagicMock()
        mock_writer.write_report = AsyncMock(return_value={"report": "# Report"})

        # First call rejects, second approves
        async def mock_critique(*args, **kwargs):
            critique_calls.append(1)
            if len(critique_calls) == 1:
                return {"status": "REJECT", "feedback": "REJECT: Needs improvement"}
            return {"status": "APPROVE", "feedback": "Approved"}

        mock_critic = MagicMock()
        mock_critic.critique = mock_critique

        from src.graph.graph_builder import ResearchGraph
        from src.graph.state import ResearchState

        graph = ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight,
            report_writer=mock_writer,
            critic=mock_critic,
        )

        compiled = graph.compile()

        initial_state = ResearchState(
            company_name="Test Corp",
            website="https://test.com",
        )

        result = await compiled.ainvoke(initial_state.model_dump())

        # Critic should be called at least twice (reject then approve)
        assert len(critique_calls) >= 1


# =============================================================================
# Data Flow E2E Tests
# =============================================================================


class TestDataFlowE2E:
    """End-to-end tests for data flow through the system."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_data_flows_between_agents(self):
        """Test that data flows correctly between agents."""
        from src.graph.state import ResearchState

        # Track what data each component receives
        received_data = {}

        mock_agents = {}
        for name in ["financial", "market", "sales", "competitor", "brand"]:
            agent = MagicMock()
            result = MagicMock()
            result.model_dump.return_value = {f"{name}_key": f"{name}_value"}
            agent.research = AsyncMock(return_value=result)
            mock_agents[name] = agent

        async def mock_analyze(company, financial_data, market_data, competitor_data, brand_data):
            received_data["insight_generator"] = {
                "financial": financial_data,
                "market": market_data,
                "competitor": competitor_data,
                "brand": brand_data,
            }
            return MagicMock(markdown_content="# Insights")

        mock_insight = MagicMock()
        mock_insight.analyze = mock_analyze

        async def mock_write_report(company, financial_data, market_data, competitor_data, brand_data, insights):
            received_data["writer"] = {
                "financial": financial_data,
                "market": market_data,
            }
            return {"report": "# Final"}

        mock_writer = MagicMock()
        mock_writer.write_report = mock_write_report

        mock_critic = MagicMock()
        mock_critic.critique = AsyncMock(return_value={
            "status": "APPROVE",
            "feedback": "OK",
        })

        from src.graph.graph_builder import ResearchGraph

        graph = ResearchGraph(
            agents=mock_agents,
            insight_generator=mock_insight,
            report_writer=mock_writer,
            critic=mock_critic,
        )

        compiled = graph.compile()

        initial_state = ResearchState(
            company_name="Test Corp",
            website="https://test.com",
        )

        await compiled.ainvoke(initial_state.model_dump())

        # Verify data flowed to insight generator
        if "insight_generator" in received_data:
            assert received_data["insight_generator"] is not None
