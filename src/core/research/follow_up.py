"""
Follow-up question generation for research refinement.

Generates clarifying questions before long research tasks to narrow scope.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from ..ai import BaseAIClient, get_ai_manager
from ..config import get_settings
from ..logging import setup_logger

logger = setup_logger("follow_up")


class QuestionType(str, Enum):
    """Types of clarifying questions."""

    SCOPE = "scope"  # Geographic, temporal, market scope
    FOCUS = "focus"  # What aspect to emphasize
    DEPTH = "depth"  # How detailed the research should be
    FORMAT = "format"  # Output format preferences
    COMPARISON = "comparison"  # Competitors or alternatives to include
    CUSTOM = "custom"  # Other clarifying questions


@dataclass
class ClarifyingQuestion:
    """A single clarifying question."""

    question: str
    question_type: QuestionType = QuestionType.CUSTOM
    options: Optional[List[str]] = None  # Suggested answers
    default: Optional[str] = None  # Default if user skips
    required: bool = False
    answer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "question_type": self.question_type.value,
            "options": self.options,
            "default": self.default,
            "required": self.required,
            "answer": self.answer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClarifyingQuestion":
        """Create from dictionary."""
        return cls(
            question=data["question"],
            question_type=QuestionType(data.get("question_type", "custom")),
            options=data.get("options"),
            default=data.get("default"),
            required=data.get("required", False),
            answer=data.get("answer"),
        )


@dataclass
class QuestionSet:
    """A set of clarifying questions for a research task."""

    original_query: str
    questions: List[ClarifyingQuestion] = field(default_factory=list)
    refined_query: Optional[str] = None

    def add_question(self, question: ClarifyingQuestion):
        """Add a question to the set."""
        self.questions.append(question)

    def set_answer(self, index: int, answer: str):
        """Set the answer for a question."""
        if 0 <= index < len(self.questions):
            self.questions[index].answer = answer

    def all_answered(self) -> bool:
        """Check if all required questions are answered."""
        return all(
            q.answer is not None or not q.required for q in self.questions
        )

    def get_context(self) -> str:
        """Get answered questions as context string."""
        context_parts = []
        for q in self.questions:
            if q.answer:
                context_parts.append(f"Q: {q.question}\nA: {q.answer}")
        return "\n\n".join(context_parts)

    def refine_query(self) -> str:
        """Get refined query with context from answers."""
        context = self.get_context()
        if context:
            self.refined_query = f"{self.original_query}\n\nContext from clarifications:\n{context}"
        else:
            self.refined_query = self.original_query
        return self.refined_query

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_query": self.original_query,
            "questions": [q.to_dict() for q in self.questions],
            "refined_query": self.refined_query,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionSet":
        """Create from dictionary."""
        qs = cls(original_query=data["original_query"])
        qs.questions = [
            ClarifyingQuestion.from_dict(q) for q in data.get("questions", [])
        ]
        qs.refined_query = data.get("refined_query")
        return qs


# Callback type for asking user questions
UserQuestionCallback = Callable[[ClarifyingQuestion], Awaitable[str]]


QUESTION_GENERATION_PROMPT = """You are a research assistant. Analyze the following research query and generate {n} clarifying questions that would help narrow down the scope and improve the research quality.

Query: {query}

Generate questions that clarify:
1. Geographic or temporal scope (e.g., which markets, time periods)
2. What aspects to focus on (e.g., financial, technical, competitive)
3. Level of depth required (e.g., overview vs detailed analysis)
4. Any specific comparisons or benchmarks needed

For each question, suggest 2-3 possible answer options when applicable.

Return ONLY a JSON array of objects with this structure:
[
  {{
    "question": "The clarifying question",
    "type": "scope|focus|depth|format|comparison|custom",
    "options": ["option1", "option2", "option3"],
    "default": "option1"
  }}
]"""


class FollowUpGenerator:
    """
    Generates clarifying questions for research tasks.

    Helps narrow scope before starting long research processes.
    """

    def __init__(
        self,
        ai_client: Optional[BaseAIClient] = None,
        default_question_count: int = 3,
    ):
        """
        Initialize the follow-up generator.

        Args:
            ai_client: AI client for question generation.
            default_question_count: Default number of questions to generate.
        """
        self.ai = ai_client or get_ai_manager()
        self.default_question_count = default_question_count

    async def generate_questions(
        self,
        query: str,
        n: Optional[int] = None,
        context: Optional[str] = None,
    ) -> QuestionSet:
        """
        Generate clarifying questions for a research query.

        Args:
            query: The original research query.
            n: Number of questions to generate.
            context: Additional context about the research.

        Returns:
            QuestionSet with generated questions.
        """
        n = n or self.default_question_count
        question_set = QuestionSet(original_query=query)

        prompt = QUESTION_GENERATION_PROMPT.format(query=query, n=n)
        if context:
            prompt += f"\n\nAdditional context: {context}"

        try:
            response = await self.ai.generate(prompt, response_format="json")
            questions = self._parse_questions(response)

            for q_data in questions[:n]:
                question = ClarifyingQuestion(
                    question=q_data.get("question", ""),
                    question_type=self._parse_question_type(q_data.get("type", "custom")),
                    options=q_data.get("options"),
                    default=q_data.get("default"),
                )
                question_set.add_question(question)

            logger.info(f"Generated {len(question_set.questions)} clarifying questions")
            return question_set

        except Exception as e:
            logger.error(f"Failed to generate clarifying questions: {e}")
            # Return empty question set - research can proceed without clarification
            return question_set

    async def ask_questions(
        self,
        question_set: QuestionSet,
        ask_callback: UserQuestionCallback,
    ) -> QuestionSet:
        """
        Ask user the clarifying questions.

        Args:
            question_set: Set of questions to ask.
            ask_callback: Async callback to get user answers.

        Returns:
            QuestionSet with answers populated.
        """
        for i, question in enumerate(question_set.questions):
            try:
                answer = await ask_callback(question)
                if answer:
                    question_set.set_answer(i, answer)
                elif question.default:
                    question_set.set_answer(i, question.default)
            except Exception as e:
                logger.warning(f"Failed to get answer for question {i}: {e}")
                if question.default:
                    question_set.set_answer(i, question.default)

        return question_set

    async def generate_and_ask(
        self,
        query: str,
        ask_callback: UserQuestionCallback,
        n: Optional[int] = None,
    ) -> str:
        """
        Generate questions, ask user, and return refined query.

        Args:
            query: Original research query.
            ask_callback: Callback to ask user questions.
            n: Number of questions to generate.

        Returns:
            Refined query with user context.
        """
        # Check if in headless mode - skip questions
        settings = get_settings()
        if settings.is_headless or not settings.is_interactive:
            logger.info("Skipping clarifying questions (non-interactive mode)")
            return query

        question_set = await self.generate_questions(query, n)

        if not question_set.questions:
            return query

        question_set = await self.ask_questions(question_set, ask_callback)
        return question_set.refine_query()

    def _parse_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract questions."""
        try:
            questions = json.loads(response)
            if isinstance(questions, list):
                return questions
        except json.JSONDecodeError:
            pass

        # Try to extract JSON array from response
        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if match:
            try:
                questions = json.loads(match.group())
                if isinstance(questions, list):
                    return questions
            except json.JSONDecodeError:
                pass

        return []

    def _parse_question_type(self, type_str: str) -> QuestionType:
        """Parse question type string."""
        type_str = type_str.lower().strip()
        for qt in QuestionType:
            if qt.value == type_str:
                return qt
        return QuestionType.CUSTOM


# Convenience functions for CLI usage
def format_question_for_cli(question: ClarifyingQuestion, index: int) -> str:
    """Format a question for CLI display."""
    lines = [f"\n{index + 1}. {question.question}"]

    if question.options:
        for i, opt in enumerate(question.options, 1):
            default_marker = " (default)" if opt == question.default else ""
            lines.append(f"   {i}) {opt}{default_marker}")

    if question.default and not question.options:
        lines.append(f"   [Default: {question.default}]")

    return "\n".join(lines)


async def cli_question_callback(question: ClarifyingQuestion) -> str:
    """Default CLI callback for asking questions."""
    import sys

    print(format_question_for_cli(question, 0))

    if question.options:
        print("   Enter number or custom answer: ", end="")
    else:
        print("   Your answer: ", end="")

    sys.stdout.flush()

    try:
        # Read from stdin
        answer = input().strip()

        if not answer and question.default:
            return question.default

        # Check if it's a number selecting an option
        if question.options and answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(question.options):
                return question.options[idx]

        return answer

    except (EOFError, KeyboardInterrupt):
        return question.default or ""


# Global generator instance
_follow_up_generator: Optional[FollowUpGenerator] = None


def get_follow_up_generator(
    ai_client: Optional[BaseAIClient] = None,
) -> FollowUpGenerator:
    """Get or create the global follow-up generator."""
    global _follow_up_generator
    if _follow_up_generator is None:
        _follow_up_generator = FollowUpGenerator(ai_client)
    return _follow_up_generator


def reset_follow_up_generator():
    """Reset the global follow-up generator."""
    global _follow_up_generator
    _follow_up_generator = None
