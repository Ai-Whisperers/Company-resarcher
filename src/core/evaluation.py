"""
Evaluation suite for agent performance benchmarking.

Provides automated testing and scoring of agent responses.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

from .ai_client import BaseAIClient, get_ai_manager
from .logger import setup_logger

logger = setup_logger("evaluation")


class MetricType(str, Enum):
    """Types of evaluation metrics."""

    ACCURACY = "accuracy"  # Exact match or close match
    FAITHFULNESS = "faithfulness"  # Does answer match context
    RELEVANCE = "relevance"  # Is answer relevant to question
    COMPLETENESS = "completeness"  # Does answer cover all aspects
    COHERENCE = "coherence"  # Is answer well-structured
    FACTUALITY = "factuality"  # Are facts correct
    CUSTOM = "custom"


@dataclass
class TestCase:
    """A single test case for evaluation."""

    test_id: str
    question: str
    expected_answer: Optional[str] = None  # Ground truth if available
    context: Optional[str] = None  # Retrieved context for faithfulness
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "context": self.context,
            "category": self.category,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        """Create from dictionary."""
        return cls(
            test_id=data["test_id"],
            question=data["question"],
            expected_answer=data.get("expected_answer"),
            context=data.get("context"),
            category=data.get("category", "general"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class EvaluationResult:
    """Result of evaluating a single test case."""

    test_case: TestCase
    agent_answer: str
    scores: Dict[MetricType, float] = field(default_factory=dict)
    feedback: Dict[MetricType, str] = field(default_factory=dict)
    passed: bool = False
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def overall_score(self) -> float:
        """Get overall score (average of all metrics)."""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_id": self.test_case.test_id,
            "question": self.test_case.question,
            "agent_answer": self.agent_answer,
            "scores": {k.value: v for k, v in self.scores.items()},
            "feedback": {k.value: v for k, v in self.feedback.items()},
            "overall_score": self.overall_score,
            "passed": self.passed,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


@dataclass
class EvaluationReport:
    """Complete evaluation report."""

    name: str
    results: List[EvaluationResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tests(self) -> int:
        """Get total number of tests."""
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        """Get number of passed tests."""
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        """Get pass rate."""
        if not self.results:
            return 0.0
        return self.passed_tests / self.total_tests

    @property
    def average_score(self) -> float:
        """Get average overall score."""
        if not self.results:
            return 0.0
        return sum(r.overall_score for r in self.results) / len(self.results)

    @property
    def average_latency(self) -> float:
        """Get average latency in ms."""
        if not self.results:
            return 0.0
        return sum(r.latency_ms for r in self.results) / len(self.results)

    def scores_by_metric(self) -> Dict[MetricType, float]:
        """Get average scores by metric."""
        metric_scores: Dict[MetricType, List[float]] = {}
        for result in self.results:
            for metric, score in result.scores.items():
                if metric not in metric_scores:
                    metric_scores[metric] = []
                metric_scores[metric].append(score)

        return {
            metric: sum(scores) / len(scores)
            for metric, scores in metric_scores.items()
        }

    def scores_by_category(self) -> Dict[str, float]:
        """Get average scores by category."""
        category_scores: Dict[str, List[float]] = {}
        for result in self.results:
            category = result.test_case.category
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(result.overall_score)

        return {
            category: sum(scores) / len(scores)
            for category, scores in category_scores.items()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "pass_rate": self.pass_rate,
            "average_score": self.average_score,
            "average_latency_ms": self.average_latency,
            "scores_by_metric": {k.value: v for k, v in self.scores_by_metric().items()},
            "scores_by_category": self.scores_by_category(),
            "results": [r.to_dict() for r in self.results],
            "config": self.config,
        }

    def format_summary(self) -> str:
        """Format a summary report."""
        lines = [
            "=" * 60,
            f"EVALUATION REPORT: {self.name}",
            "=" * 60,
            "",
            "SUMMARY",
            f"  Total Tests:    {self.total_tests}",
            f"  Passed:         {self.passed_tests}",
            f"  Pass Rate:      {self.pass_rate:.1%}",
            f"  Average Score:  {self.average_score:.2f}",
            f"  Avg Latency:    {self.average_latency:.0f}ms",
            "",
            "SCORES BY METRIC",
        ]

        for metric, score in self.scores_by_metric().items():
            lines.append(f"  {metric.value:15} {score:.2f}")

        lines.extend(["", "SCORES BY CATEGORY"])
        for category, score in self.scores_by_category().items():
            lines.append(f"  {category:15} {score:.2f}")

        lines.append("=" * 60)
        return "\n".join(lines)


# Agent callback type
AgentCallback = Callable[[str], Awaitable[str]]


class LLMJudge:
    """
    Uses an LLM to evaluate agent responses.

    Implements LLM-as-a-judge pattern for nuanced evaluation.
    """

    def __init__(self, ai_client: Optional[BaseAIClient] = None):
        """Initialize the LLM judge."""
        self.ai = ai_client or get_ai_manager()

    async def evaluate_accuracy(
        self,
        question: str,
        agent_answer: str,
        expected_answer: str,
    ) -> tuple:
        """
        Evaluate accuracy against expected answer.

        Returns (score, feedback).
        """
        prompt = f"""Evaluate how accurately the agent's answer matches the expected answer.

Question: {question}

Expected Answer: {expected_answer}

Agent's Answer: {agent_answer}

Rate the accuracy from 0.0 to 1.0 where:
- 1.0: Perfect match or semantically equivalent
- 0.7-0.9: Mostly correct with minor differences
- 0.4-0.6: Partially correct
- 0.1-0.3: Mostly incorrect
- 0.0: Completely wrong

Respond in JSON format:
{{"score": <float>, "feedback": "<brief explanation>"}}"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            result = json.loads(response)
            return float(result.get("score", 0)), result.get("feedback", "")
        except Exception as e:
            logger.error(f"Accuracy evaluation failed: {e}")
            return 0.0, str(e)

    async def evaluate_faithfulness(
        self,
        question: str,
        agent_answer: str,
        context: str,
    ) -> tuple:
        """
        Evaluate if answer is faithful to the provided context.

        Returns (score, feedback).
        """
        prompt = f"""Evaluate if the agent's answer is faithful to (supported by) the provided context.

Question: {question}

Context:
{context}

Agent's Answer: {agent_answer}

Rate faithfulness from 0.0 to 1.0 where:
- 1.0: Fully supported by context, no hallucinations
- 0.7-0.9: Mostly supported, minor unsupported claims
- 0.4-0.6: Partially supported, some hallucinations
- 0.1-0.3: Mostly unsupported, significant hallucinations
- 0.0: Contradicts context or completely fabricated

Respond in JSON format:
{{"score": <float>, "feedback": "<brief explanation>"}}"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            result = json.loads(response)
            return float(result.get("score", 0)), result.get("feedback", "")
        except Exception as e:
            logger.error(f"Faithfulness evaluation failed: {e}")
            return 0.0, str(e)

    async def evaluate_relevance(
        self,
        question: str,
        agent_answer: str,
    ) -> tuple:
        """
        Evaluate if answer is relevant to the question.

        Returns (score, feedback).
        """
        prompt = f"""Evaluate if the agent's answer is relevant to the question asked.

Question: {question}

Agent's Answer: {agent_answer}

Rate relevance from 0.0 to 1.0 where:
- 1.0: Directly addresses the question
- 0.7-0.9: Mostly relevant with minor tangents
- 0.4-0.6: Somewhat relevant but misses key points
- 0.1-0.3: Barely relevant, off-topic
- 0.0: Completely irrelevant

Respond in JSON format:
{{"score": <float>, "feedback": "<brief explanation>"}}"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            result = json.loads(response)
            return float(result.get("score", 0)), result.get("feedback", "")
        except Exception as e:
            logger.error(f"Relevance evaluation failed: {e}")
            return 0.0, str(e)

    async def evaluate_coherence(
        self,
        agent_answer: str,
    ) -> tuple:
        """
        Evaluate answer coherence and structure.

        Returns (score, feedback).
        """
        prompt = f"""Evaluate the coherence and structure of this answer.

Answer: {agent_answer}

Rate coherence from 0.0 to 1.0 where:
- 1.0: Clear, well-organized, logical flow
- 0.7-0.9: Mostly coherent with minor issues
- 0.4-0.6: Somewhat coherent but disorganized
- 0.1-0.3: Confusing and hard to follow
- 0.0: Incoherent

Respond in JSON format:
{{"score": <float>, "feedback": "<brief explanation>"}}"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            result = json.loads(response)
            return float(result.get("score", 0)), result.get("feedback", "")
        except Exception as e:
            logger.error(f"Coherence evaluation failed: {e}")
            return 0.0, str(e)


class Evaluator:
    """
    Main evaluation orchestrator.

    Runs test suites and generates reports.
    """

    def __init__(
        self,
        ai_client: Optional[BaseAIClient] = None,
        pass_threshold: float = 0.7,
    ):
        """
        Initialize the evaluator.

        Args:
            ai_client: AI client for LLM judge.
            pass_threshold: Score threshold for passing.
        """
        self.judge = LLMJudge(ai_client)
        self.pass_threshold = pass_threshold
        self._test_cases: List[TestCase] = []

    def add_test_case(self, test_case: TestCase):
        """Add a test case."""
        self._test_cases.append(test_case)

    def add_test_cases(self, test_cases: List[TestCase]):
        """Add multiple test cases."""
        self._test_cases.extend(test_cases)

    def load_test_cases(self, data: List[Dict[str, Any]]):
        """Load test cases from dictionaries."""
        for item in data:
            self._test_cases.append(TestCase.from_dict(item))

    async def evaluate_single(
        self,
        test_case: TestCase,
        agent_callback: AgentCallback,
        metrics: Optional[List[MetricType]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a single test case.

        Args:
            test_case: Test case to evaluate.
            agent_callback: Async function to get agent response.
            metrics: Metrics to evaluate (defaults to all applicable).

        Returns:
            Evaluation result.
        """
        import time
        start_time = time.time()

        result = EvaluationResult(
            test_case=test_case,
            agent_answer="",
        )

        try:
            # Get agent response
            agent_answer = await agent_callback(test_case.question)
            result.agent_answer = agent_answer
            result.latency_ms = (time.time() - start_time) * 1000

            # Determine metrics to evaluate
            if metrics is None:
                metrics = [MetricType.RELEVANCE, MetricType.COHERENCE]
                if test_case.expected_answer:
                    metrics.append(MetricType.ACCURACY)
                if test_case.context:
                    metrics.append(MetricType.FAITHFULNESS)

            # Evaluate each metric
            for metric in metrics:
                score, feedback = await self._evaluate_metric(
                    metric, test_case, agent_answer
                )
                result.scores[metric] = score
                result.feedback[metric] = feedback

            # Determine pass/fail
            result.passed = result.overall_score >= self.pass_threshold

        except Exception as e:
            result.error = str(e)
            result.passed = False
            logger.error(f"Evaluation error for {test_case.test_id}: {e}")

        return result

    async def _evaluate_metric(
        self,
        metric: MetricType,
        test_case: TestCase,
        agent_answer: str,
    ) -> tuple:
        """Evaluate a specific metric."""
        if metric == MetricType.ACCURACY and test_case.expected_answer:
            return await self.judge.evaluate_accuracy(
                test_case.question, agent_answer, test_case.expected_answer
            )
        elif metric == MetricType.FAITHFULNESS and test_case.context:
            return await self.judge.evaluate_faithfulness(
                test_case.question, agent_answer, test_case.context
            )
        elif metric == MetricType.RELEVANCE:
            return await self.judge.evaluate_relevance(
                test_case.question, agent_answer
            )
        elif metric == MetricType.COHERENCE:
            return await self.judge.evaluate_coherence(agent_answer)
        else:
            return 0.5, "Metric not evaluated"

    async def run_evaluation(
        self,
        agent_callback: AgentCallback,
        name: str = "Evaluation",
        metrics: Optional[List[MetricType]] = None,
    ) -> EvaluationReport:
        """
        Run full evaluation suite.

        Args:
            agent_callback: Agent function to test.
            name: Name for the evaluation report.
            metrics: Metrics to evaluate.

        Returns:
            Complete evaluation report.
        """
        report = EvaluationReport(
            name=name,
            config={
                "pass_threshold": self.pass_threshold,
                "metrics": [m.value for m in metrics] if metrics else "auto",
            },
        )

        for test_case in self._test_cases:
            result = await self.evaluate_single(test_case, agent_callback, metrics)
            report.results.append(result)
            logger.info(
                f"Test {test_case.test_id}: {result.overall_score:.2f} "
                f"({'PASS' if result.passed else 'FAIL'})"
            )

        logger.info(f"Evaluation complete: {report.pass_rate:.1%} pass rate")
        return report


# Convenience function
async def evaluate_agent(
    agent_callback: AgentCallback,
    test_cases: List[Dict[str, Any]],
    name: str = "Agent Evaluation",
) -> EvaluationReport:
    """
    Quick evaluation of an agent.

    Args:
        agent_callback: Agent function to test.
        test_cases: List of test case dictionaries.
        name: Evaluation name.

    Returns:
        Evaluation report.
    """
    evaluator = Evaluator()
    evaluator.load_test_cases(test_cases)
    return await evaluator.run_evaluation(agent_callback, name)
