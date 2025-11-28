"""Tests for the evaluation suite."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.core.evaluation import (
    Evaluator,
    EvaluationReport,
    EvaluationResult,
    LLMJudge,
    MetricType,
    TestCase,
    evaluate_agent,
)


class TestTestCase:
    """Tests for TestCase class."""

    def test_create_test_case(self):
        """Test creating a test case."""
        tc = TestCase(
            test_id="tc_1",
            question="What is the capital of France?",
            expected_answer="Paris",
        )
        assert tc.test_id == "tc_1"
        assert tc.question == "What is the capital of France?"
        assert tc.expected_answer == "Paris"

    def test_test_case_with_context(self):
        """Test case with context."""
        tc = TestCase(
            test_id="tc_2",
            question="What is the company's revenue?",
            context="The company reported $10M in revenue in 2023.",
            expected_answer="$10M",
        )
        assert tc.context is not None

    def test_to_dict(self):
        """Test serialization."""
        tc = TestCase(
            test_id="tc_1",
            question="Test question",
            category="finance",
            metadata={"source": "manual"},
        )
        data = tc.to_dict()
        assert data["test_id"] == "tc_1"
        assert data["category"] == "finance"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "test_id": "tc_3",
            "question": "Loaded question",
            "expected_answer": "Answer",
            "category": "general",
        }
        tc = TestCase.from_dict(data)
        assert tc.test_id == "tc_3"
        assert tc.expected_answer == "Answer"


class TestEvaluationResult:
    """Tests for EvaluationResult class."""

    def test_create_result(self):
        """Test creating an evaluation result."""
        tc = TestCase(test_id="tc_1", question="Test")
        result = EvaluationResult(
            test_case=tc,
            agent_answer="Agent response",
        )
        assert result.agent_answer == "Agent response"
        assert result.passed is False

    def test_overall_score(self):
        """Test overall score calculation."""
        tc = TestCase(test_id="tc_1", question="Test")
        result = EvaluationResult(
            test_case=tc,
            agent_answer="Response",
            scores={
                MetricType.ACCURACY: 0.8,
                MetricType.RELEVANCE: 0.9,
                MetricType.COHERENCE: 0.7,
            },
        )
        # (0.8 + 0.9 + 0.7) / 3 = 0.8
        assert abs(result.overall_score - 0.8) < 0.01

    def test_overall_score_empty(self):
        """Test overall score with no scores."""
        tc = TestCase(test_id="tc_1", question="Test")
        result = EvaluationResult(test_case=tc, agent_answer="")
        assert result.overall_score == 0.0

    def test_to_dict(self):
        """Test serialization."""
        tc = TestCase(test_id="tc_1", question="Test")
        result = EvaluationResult(
            test_case=tc,
            agent_answer="Response",
            scores={MetricType.ACCURACY: 0.9},
            passed=True,
            latency_ms=150.0,
        )
        data = result.to_dict()
        assert data["test_id"] == "tc_1"
        assert data["scores"]["accuracy"] == 0.9
        assert data["passed"] is True


class TestEvaluationReport:
    """Tests for EvaluationReport class."""

    def test_create_report(self):
        """Test creating a report."""
        report = EvaluationReport(name="Test Report")
        assert report.name == "Test Report"
        assert report.total_tests == 0

    def test_add_results(self):
        """Test adding results."""
        report = EvaluationReport(name="Test")

        for i in range(5):
            tc = TestCase(test_id=f"tc_{i}", question=f"Q{i}")
            result = EvaluationResult(
                test_case=tc,
                agent_answer=f"A{i}",
                scores={MetricType.ACCURACY: 0.8 if i < 3 else 0.5},
                passed=i < 3,
            )
            report.results.append(result)

        assert report.total_tests == 5
        assert report.passed_tests == 3
        assert report.pass_rate == 0.6

    def test_average_score(self):
        """Test average score calculation."""
        report = EvaluationReport(name="Test")

        for score in [0.8, 0.9, 0.7]:
            tc = TestCase(test_id="tc", question="Q")
            result = EvaluationResult(
                test_case=tc,
                agent_answer="A",
                scores={MetricType.ACCURACY: score},
            )
            report.results.append(result)

        # Average of 0.8, 0.9, 0.7 = 0.8
        assert abs(report.average_score - 0.8) < 0.01

    def test_scores_by_metric(self):
        """Test scores grouped by metric."""
        report = EvaluationReport(name="Test")

        for i in range(3):
            tc = TestCase(test_id=f"tc_{i}", question="Q")
            result = EvaluationResult(
                test_case=tc,
                agent_answer="A",
                scores={
                    MetricType.ACCURACY: 0.8,
                    MetricType.RELEVANCE: 0.9,
                },
            )
            report.results.append(result)

        by_metric = report.scores_by_metric()
        assert MetricType.ACCURACY in by_metric
        assert MetricType.RELEVANCE in by_metric

    def test_scores_by_category(self):
        """Test scores grouped by category."""
        report = EvaluationReport(name="Test")

        categories = ["finance", "finance", "tech"]
        for i, cat in enumerate(categories):
            tc = TestCase(test_id=f"tc_{i}", question="Q", category=cat)
            result = EvaluationResult(
                test_case=tc,
                agent_answer="A",
                scores={MetricType.ACCURACY: 0.8},
            )
            report.results.append(result)

        by_category = report.scores_by_category()
        assert "finance" in by_category
        assert "tech" in by_category

    def test_format_summary(self):
        """Test summary formatting."""
        report = EvaluationReport(name="Test Report")
        tc = TestCase(test_id="tc_1", question="Q", category="general")
        result = EvaluationResult(
            test_case=tc,
            agent_answer="A",
            scores={MetricType.ACCURACY: 0.85},
            passed=True,
            latency_ms=100.0,
        )
        report.results.append(result)

        summary = report.format_summary()
        assert "Test Report" in summary
        assert "SUMMARY" in summary
        assert "SCORES BY METRIC" in summary


class TestLLMJudge:
    """Tests for LLMJudge class."""

    @pytest.mark.asyncio
    async def test_evaluate_accuracy(self):
        """Test accuracy evaluation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.9, "feedback": "Good match"}')

        judge = LLMJudge(ai_client=mock_ai)
        score, feedback = await judge.evaluate_accuracy(
            "What is 2+2?",
            "4",
            "4",
        )

        assert score == 0.9
        assert feedback == "Good match"

    @pytest.mark.asyncio
    async def test_evaluate_faithfulness(self):
        """Test faithfulness evaluation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.8, "feedback": "Supported by context"}')

        judge = LLMJudge(ai_client=mock_ai)
        score, feedback = await judge.evaluate_faithfulness(
            "What is the revenue?",
            "$10M",
            "The company reported $10M in revenue.",
        )

        assert score == 0.8

    @pytest.mark.asyncio
    async def test_evaluate_relevance(self):
        """Test relevance evaluation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.95, "feedback": "Directly addresses question"}')

        judge = LLMJudge(ai_client=mock_ai)
        score, feedback = await judge.evaluate_relevance(
            "What is the capital?",
            "Paris is the capital of France.",
        )

        assert score == 0.95

    @pytest.mark.asyncio
    async def test_evaluate_coherence(self):
        """Test coherence evaluation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.85, "feedback": "Well structured"}')

        judge = LLMJudge(ai_client=mock_ai)
        score, feedback = await judge.evaluate_coherence(
            "This is a well-organized answer with clear points."
        )

        assert score == 0.85

    @pytest.mark.asyncio
    async def test_evaluation_error_handling(self):
        """Test handling evaluation errors."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(side_effect=Exception("API error"))

        judge = LLMJudge(ai_client=mock_ai)
        score, feedback = await judge.evaluate_accuracy("Q", "A", "E")

        assert score == 0.0
        assert "API error" in feedback


class TestEvaluator:
    """Tests for Evaluator class."""

    @pytest.mark.asyncio
    async def test_evaluate_single(self):
        """Test evaluating a single test case."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.8, "feedback": "Good"}')

        evaluator = Evaluator(ai_client=mock_ai, pass_threshold=0.7)

        tc = TestCase(
            test_id="tc_1",
            question="Test question",
            expected_answer="Expected",
        )

        async def mock_agent(question):
            return "Agent response"

        result = await evaluator.evaluate_single(tc, mock_agent)

        assert result.agent_answer == "Agent response"
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_evaluate_single_pass(self):
        """Test passing evaluation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.9, "feedback": "Excellent"}')

        evaluator = Evaluator(ai_client=mock_ai, pass_threshold=0.7)

        tc = TestCase(test_id="tc_1", question="Q")

        async def mock_agent(question):
            return "Good answer"

        result = await evaluator.evaluate_single(tc, mock_agent)
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_evaluate_single_fail(self):
        """Test failing evaluation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.3, "feedback": "Poor"}')

        evaluator = Evaluator(ai_client=mock_ai, pass_threshold=0.7)

        tc = TestCase(test_id="tc_1", question="Q")

        async def mock_agent(question):
            return "Bad answer"

        result = await evaluator.evaluate_single(tc, mock_agent)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_run_evaluation(self):
        """Test running full evaluation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.8, "feedback": "Good"}')

        evaluator = Evaluator(ai_client=mock_ai)
        evaluator.add_test_case(TestCase(test_id="tc_1", question="Q1"))
        evaluator.add_test_case(TestCase(test_id="tc_2", question="Q2"))

        async def mock_agent(question):
            return f"Answer to {question}"

        report = await evaluator.run_evaluation(mock_agent, name="Test Suite")

        assert report.total_tests == 2
        assert report.name == "Test Suite"

    def test_add_test_cases(self):
        """Test adding multiple test cases."""
        evaluator = Evaluator()
        evaluator.add_test_cases([
            TestCase(test_id="tc_1", question="Q1"),
            TestCase(test_id="tc_2", question="Q2"),
        ])
        assert len(evaluator._test_cases) == 2

    def test_load_test_cases(self):
        """Test loading test cases from dicts."""
        evaluator = Evaluator()
        evaluator.load_test_cases([
            {"test_id": "tc_1", "question": "Q1"},
            {"test_id": "tc_2", "question": "Q2", "expected_answer": "A2"},
        ])
        assert len(evaluator._test_cases) == 2
        assert evaluator._test_cases[1].expected_answer == "A2"


class TestConvenienceFunction:
    """Tests for evaluate_agent convenience function."""

    @pytest.mark.asyncio
    async def test_evaluate_agent(self):
        """Test convenience function."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='{"score": 0.85, "feedback": "Good"}')

        async def mock_agent(question):
            return "Agent answer"

        test_cases = [
            {"test_id": "tc_1", "question": "Q1"},
            {"test_id": "tc_2", "question": "Q2"},
        ]

        with patch("src.core.evaluation.get_ai_manager", return_value=mock_ai):
            report = await evaluate_agent(mock_agent, test_cases)

        assert report.total_tests == 2


class TestMetricType:
    """Tests for MetricType enum."""

    def test_all_metrics_exist(self):
        """Test all expected metrics are defined."""
        expected = [
            "accuracy",
            "faithfulness",
            "relevance",
            "completeness",
            "coherence",
            "factuality",
            "custom",
        ]
        actual = [m.value for m in MetricType]
        assert set(actual) == set(expected)
