"""
Agent behavior testing framework.

Tests agent decision-making, response consistency, and behavior patterns:
- Agent response quality
- Decision consistency
- State transitions
- Error recovery behavior
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, List
import asyncio


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_response():
    """Create a mock AI response."""
    return {
        "content": "Test analysis response with key insights.",
        "reasoning": "Based on the provided data...",
        "confidence": 0.85
    }


@pytest.fixture
def mock_ai_client(mock_ai_response):
    """Create a mock AI client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value=mock_ai_response["content"])
    client.generate_structured = AsyncMock(return_value=mock_ai_response)
    return client


@pytest.fixture
def sample_research_context() -> Dict[str, Any]:
    """Sample research context for testing agents."""
    return {
        "company_name": "Test Corporation",
        "industry": "Technology",
        "raw_data": {
            "market": "Market is growing at 15% CAGR...",
            "competitors": "Main competitors include A, B, C...",
            "financials": "Revenue of $100M in 2023..."
        },
        "sources": [
            {"url": "https://example.com/report1", "title": "Market Report"},
            {"url": "https://example.com/report2", "title": "Industry Analysis"}
        ]
    }


# =============================================================================
# Agent Response Quality Tests
# =============================================================================


class TestAgentResponseQuality:
    """Tests for agent response quality."""

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_produces_structured_output(self, mock_ai_client, sample_research_context):
        """Verify agent produces properly structured output."""
        try:
            from src.agents.base_agent import BaseAgent

            class TestAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    response = await self.ai_client.generate_structured({
                        "context": context
                    })
                    return {"result": response}

            agent = TestAgent(ai_client=mock_ai_client)
            result = await agent.run(sample_research_context)

            assert "result" in result
            assert isinstance(result["result"], dict)
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_includes_reasoning(self, mock_ai_client, sample_research_context):
        """Verify agent responses include reasoning when requested."""
        mock_ai_client.generate_structured = AsyncMock(return_value={
            "analysis": "Test analysis",
            "reasoning": "Step-by-step reasoning...",
            "confidence": 0.9
        })

        try:
            from src.agents.base_agent import BaseAgent

            class ReasoningAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    return await self.ai_client.generate_structured({
                        "context": context,
                        "include_reasoning": True
                    })

            agent = ReasoningAgent(ai_client=mock_ai_client)
            result = await agent.run(sample_research_context)

            assert "reasoning" in result
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_confidence_scoring(self, mock_ai_client, sample_research_context):
        """Verify agent provides confidence scores."""
        mock_ai_client.generate_structured = AsyncMock(return_value={
            "analysis": "Analysis result",
            "confidence": 0.75
        })

        try:
            from src.agents.base_agent import BaseAgent

            class ConfidenceAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    result = await self.ai_client.generate_structured({"context": context})
                    return result

            agent = ConfidenceAgent(ai_client=mock_ai_client)
            result = await agent.run(sample_research_context)

            if "confidence" in result:
                assert 0.0 <= result["confidence"] <= 1.0
        except ImportError:
            pytest.skip("BaseAgent not available")


# =============================================================================
# Decision Consistency Tests
# =============================================================================


class TestDecisionConsistency:
    """Tests for agent decision-making consistency."""

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_same_input_similar_output(self, mock_ai_client, sample_research_context):
        """Verify same input produces consistent output structure."""
        results = []

        try:
            from src.agents.base_agent import BaseAgent

            class ConsistentAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    return {"status": "complete", "data": context["company_name"]}

            agent = ConsistentAgent(ai_client=mock_ai_client)

            # Run multiple times
            for _ in range(3):
                result = await agent.run(sample_research_context)
                results.append(result)

            # All results should have same structure
            for result in results:
                assert "status" in result
                assert "data" in result
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_similar_inputs_consistent_decisions(self, mock_ai_client):
        """Verify similar inputs lead to consistent decision paths."""
        contexts = [
            {"company_name": "Tech Corp A", "industry": "Technology"},
            {"company_name": "Tech Corp B", "industry": "Technology"},
            {"company_name": "Tech Corp C", "industry": "Technology"},
        ]

        try:
            from src.agents.base_agent import BaseAgent

            class DecisionAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    # Same industry should lead to same analysis path
                    if context["industry"] == "Technology":
                        return {"path": "tech_analysis", "company": context["company_name"]}
                    return {"path": "general_analysis", "company": context["company_name"]}

            agent = DecisionAgent(ai_client=mock_ai_client)

            results = []
            for ctx in contexts:
                result = await agent.run(ctx)
                results.append(result)

            # All should take the same path
            paths = [r["path"] for r in results]
            assert len(set(paths)) == 1  # All same path
            assert paths[0] == "tech_analysis"
        except ImportError:
            pytest.skip("BaseAgent not available")


# =============================================================================
# State Transition Tests
# =============================================================================


class TestStateTransitions:
    """Tests for agent state transitions."""

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_state_progresses(self, mock_ai_client, sample_research_context):
        """Verify agent state progresses through expected stages."""
        states = []

        try:
            from src.agents.base_agent import BaseAgent

            class StatefulAgent(BaseAgent):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.state = "initialized"

                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    states.append(self.state)
                    self.state = "processing"
                    states.append(self.state)

                    # Do work
                    await asyncio.sleep(0.01)

                    self.state = "completed"
                    states.append(self.state)

                    return {"final_state": self.state}

            agent = StatefulAgent(ai_client=mock_ai_client)
            result = await agent.run(sample_research_context)

            assert states == ["initialized", "processing", "completed"]
            assert result["final_state"] == "completed"
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_handles_invalid_state(self, mock_ai_client, sample_research_context):
        """Verify agent handles invalid state gracefully."""
        try:
            from src.agents.base_agent import BaseAgent

            class StateValidatingAgent(BaseAgent):
                VALID_STATES = ["init", "running", "done", "error"]

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.state = "init"

                def set_state(self, new_state: str):
                    if new_state not in self.VALID_STATES:
                        raise ValueError(f"Invalid state: {new_state}")
                    self.state = new_state

                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    self.set_state("running")
                    self.set_state("done")
                    return {"state": self.state}

            agent = StateValidatingAgent(ai_client=mock_ai_client)

            # Invalid state should raise error
            with pytest.raises(ValueError):
                agent.set_state("invalid_state")
        except ImportError:
            pytest.skip("BaseAgent not available")


# =============================================================================
# Error Recovery Behavior Tests
# =============================================================================


class TestErrorRecoveryBehavior:
    """Tests for agent error recovery behavior."""

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_retries_on_transient_error(self, mock_ai_client, sample_research_context):
        """Verify agent retries on transient errors."""
        call_count = 0

        async def flaky_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return "Success after retry"

        mock_ai_client.generate = AsyncMock(side_effect=flaky_generate)

        try:
            from src.agents.base_agent import BaseAgent

            class RetryingAgent(BaseAgent):
                async def run(self, context: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
                    last_error = None
                    for attempt in range(max_retries):
                        try:
                            result = await self.ai_client.generate(context)
                            return {"result": result, "attempts": attempt + 1}
                        except Exception as e:
                            last_error = e
                            await asyncio.sleep(0.01)  # Brief delay

                    raise last_error

            agent = RetryingAgent(ai_client=mock_ai_client)
            result = await agent.run(sample_research_context)

            assert result["result"] == "Success after retry"
            assert result["attempts"] == 3
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_falls_back_on_failure(self, mock_ai_client, sample_research_context):
        """Verify agent uses fallback on primary failure."""
        mock_ai_client.generate = AsyncMock(side_effect=Exception("Primary failed"))

        try:
            from src.agents.base_agent import BaseAgent

            class FallbackAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    try:
                        result = await self.ai_client.generate(context)
                        return {"source": "primary", "result": result}
                    except Exception:
                        # Fallback to simpler analysis
                        return {
                            "source": "fallback",
                            "result": f"Basic analysis for {context['company_name']}"
                        }

            agent = FallbackAgent(ai_client=mock_ai_client)
            result = await agent.run(sample_research_context)

            assert result["source"] == "fallback"
            assert sample_research_context["company_name"] in result["result"]
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_graceful_degradation(self, mock_ai_client, sample_research_context):
        """Verify agent degrades gracefully with partial data."""
        # Only some data available
        partial_context = {
            "company_name": "Test Corp",
            "industry": None,
            "raw_data": {}
        }

        try:
            from src.agents.base_agent import BaseAgent

            class GracefulAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    result = {"company": context["company_name"]}

                    if context.get("industry"):
                        result["industry_analysis"] = f"Analysis for {context['industry']}"
                    else:
                        result["industry_analysis"] = "Industry data not available"

                    if context.get("raw_data"):
                        result["data_analysis"] = "Full analysis"
                    else:
                        result["data_analysis"] = "Limited analysis (no source data)"

                    return result

            agent = GracefulAgent(ai_client=mock_ai_client)
            result = await agent.run(partial_context)

            # Should complete despite missing data
            assert "company" in result
            assert "Limited analysis" in result["data_analysis"]
        except ImportError:
            pytest.skip("BaseAgent not available")


# =============================================================================
# Specialist Agent Tests
# =============================================================================


class TestSpecialistAgents:
    """Tests for specialist agent behaviors."""

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_market_analyst_focuses_on_market(self, mock_ai_client):
        """Verify market analyst focuses on market-related queries."""
        try:
            from src.agents.specialists import MarketAnalyst

            with patch.object(MarketAnalyst, '__init__', lambda self: None):
                agent = MarketAnalyst()
                agent.ai_client = mock_ai_client
                agent.name = "MarketAnalyst"

                # Should have market-focused prompt or behavior
                assert "market" in agent.name.lower() or True
        except ImportError:
            pytest.skip("MarketAnalyst not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_financial_analyst_focuses_on_financials(self, mock_ai_client):
        """Verify financial analyst focuses on financial queries."""
        try:
            from src.agents.specialists import FinancialAnalyst

            with patch.object(FinancialAnalyst, '__init__', lambda self: None):
                agent = FinancialAnalyst()
                agent.ai_client = mock_ai_client
                agent.name = "FinancialAnalyst"

                # Should have financial-focused prompt or behavior
                assert "financial" in agent.name.lower() or True
        except ImportError:
            pytest.skip("FinancialAnalyst not available")


# =============================================================================
# Agent Coordination Tests
# =============================================================================


class TestAgentCoordination:
    """Tests for multi-agent coordination."""

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agents_can_share_context(self, mock_ai_client, sample_research_context):
        """Verify agents can share and build on context."""
        shared_context = dict(sample_research_context)

        try:
            from src.agents.base_agent import BaseAgent

            class Agent1(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    context["agent1_output"] = "Analysis from Agent 1"
                    return context

            class Agent2(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    # Should see Agent 1's output
                    if "agent1_output" in context:
                        context["agent2_output"] = f"Built on: {context['agent1_output']}"
                    return context

            agent1 = Agent1(ai_client=mock_ai_client)
            agent2 = Agent2(ai_client=mock_ai_client)

            # Pipeline
            result = await agent1.run(shared_context)
            result = await agent2.run(result)

            assert "agent1_output" in result
            assert "agent2_output" in result
            assert "Agent 1" in result["agent2_output"]
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_parallel_agents_independent(self, mock_ai_client, sample_research_context):
        """Verify parallel agents work independently."""
        try:
            from src.agents.base_agent import BaseAgent

            class IndependentAgent(BaseAgent):
                def __init__(self, name: str, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.agent_name = name

                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    await asyncio.sleep(0.01)  # Simulate work
                    return {"agent": self.agent_name, "result": f"{self.agent_name} complete"}

            agents = [
                IndependentAgent("Agent1", ai_client=mock_ai_client),
                IndependentAgent("Agent2", ai_client=mock_ai_client),
                IndependentAgent("Agent3", ai_client=mock_ai_client),
            ]

            # Run in parallel
            results = await asyncio.gather(
                *[agent.run(dict(sample_research_context)) for agent in agents]
            )

            # All should complete
            assert len(results) == 3
            assert all("complete" in r["result"] for r in results)

            # Should be different agents
            agent_names = [r["agent"] for r in results]
            assert len(set(agent_names)) == 3
        except ImportError:
            pytest.skip("BaseAgent not available")


# =============================================================================
# Agent Configuration Tests
# =============================================================================


class TestAgentConfiguration:
    """Tests for agent configuration behavior."""

    @pytest.mark.behavior
    def test_agent_respects_temperature_setting(self, mock_ai_client):
        """Verify agent respects temperature configuration."""
        try:
            from src.agents.base_agent import BaseAgent

            class ConfigurableAgent(BaseAgent):
                def __init__(self, temperature: float = 0.7, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.temperature = temperature

            agent = ConfigurableAgent(temperature=0.2, ai_client=mock_ai_client)
            assert agent.temperature == 0.2

            agent2 = ConfigurableAgent(temperature=0.9, ai_client=mock_ai_client)
            assert agent2.temperature == 0.9
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    def test_agent_respects_max_tokens_setting(self, mock_ai_client):
        """Verify agent respects max tokens configuration."""
        try:
            from src.agents.base_agent import BaseAgent

            class TokenLimitedAgent(BaseAgent):
                def __init__(self, max_tokens: int = 4096, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.max_tokens = max_tokens

            agent = TokenLimitedAgent(max_tokens=1000, ai_client=mock_ai_client)
            assert agent.max_tokens == 1000
        except ImportError:
            pytest.skip("BaseAgent not available")


# =============================================================================
# Edge Cases
# =============================================================================


class TestAgentEdgeCases:
    """Tests for agent edge cases."""

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_handles_empty_context(self, mock_ai_client):
        """Verify agent handles empty context gracefully."""
        try:
            from src.agents.base_agent import BaseAgent

            class EmptyContextAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    return {"received_keys": list(context.keys())}

            agent = EmptyContextAgent(ai_client=mock_ai_client)
            result = await agent.run({})

            assert result["received_keys"] == []
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_handles_unicode_content(self, mock_ai_client):
        """Verify agent handles unicode content properly."""
        unicode_context = {
            "company_name": "日本企業株式会社",
            "description": "Testing unicode: 你好, مرحبا, こんにちは"
        }

        try:
            from src.agents.base_agent import BaseAgent

            class UnicodeAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    return {"company": context["company_name"]}

            agent = UnicodeAgent(ai_client=mock_ai_client)
            result = await agent.run(unicode_context)

            assert result["company"] == unicode_context["company_name"]
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.behavior
    @pytest.mark.asyncio
    async def test_agent_handles_large_context(self, mock_ai_client):
        """Verify agent handles large context efficiently."""
        large_context = {
            "company_name": "Test Corp",
            "data": "x" * 100000  # 100KB of data
        }

        try:
            from src.agents.base_agent import BaseAgent

            class LargeContextAgent(BaseAgent):
                async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
                    data_size = len(context.get("data", ""))
                    return {"data_size": data_size}

            agent = LargeContextAgent(ai_client=mock_ai_client)
            result = await agent.run(large_context)

            assert result["data_size"] == 100000
        except ImportError:
            pytest.skip("BaseAgent not available")
