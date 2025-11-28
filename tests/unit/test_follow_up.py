"""Tests for the follow-up question generation system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.follow_up import (
    ClarifyingQuestion,
    FollowUpGenerator,
    QuestionSet,
    QuestionType,
    format_question_for_cli,
    get_follow_up_generator,
    reset_follow_up_generator,
)


class TestClarifyingQuestion:
    """Tests for ClarifyingQuestion class."""

    def test_create_basic_question(self):
        """Test creating a basic question."""
        q = ClarifyingQuestion(question="What market are you interested in?")
        assert q.question == "What market are you interested in?"
        assert q.question_type == QuestionType.CUSTOM
        assert q.options is None
        assert q.answer is None

    def test_create_question_with_options(self):
        """Test creating question with options."""
        q = ClarifyingQuestion(
            question="Which market?",
            question_type=QuestionType.SCOPE,
            options=["US", "Europe", "Global"],
            default="US",
        )
        assert q.options == ["US", "Europe", "Global"]
        assert q.default == "US"

    def test_to_dict(self):
        """Test serialization to dict."""
        q = ClarifyingQuestion(
            question="Test question?",
            question_type=QuestionType.FOCUS,
            options=["A", "B"],
            default="A",
            required=True,
            answer="B",
        )
        data = q.to_dict()
        assert data["question"] == "Test question?"
        assert data["question_type"] == "focus"
        assert data["options"] == ["A", "B"]
        assert data["required"] is True
        assert data["answer"] == "B"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "question": "What scope?",
            "question_type": "scope",
            "options": ["Small", "Large"],
            "default": "Small",
            "required": False,
            "answer": "Large",
        }
        q = ClarifyingQuestion.from_dict(data)
        assert q.question == "What scope?"
        assert q.question_type == QuestionType.SCOPE
        assert q.answer == "Large"


class TestQuestionSet:
    """Tests for QuestionSet class."""

    def test_create_question_set(self):
        """Test creating a question set."""
        qs = QuestionSet(original_query="Research Apple Inc")
        assert qs.original_query == "Research Apple Inc"
        assert len(qs.questions) == 0

    def test_add_question(self):
        """Test adding questions."""
        qs = QuestionSet(original_query="Test")
        q1 = ClarifyingQuestion(question="Q1?")
        q2 = ClarifyingQuestion(question="Q2?")
        qs.add_question(q1)
        qs.add_question(q2)
        assert len(qs.questions) == 2

    def test_set_answer(self):
        """Test setting answers."""
        qs = QuestionSet(original_query="Test")
        qs.add_question(ClarifyingQuestion(question="Q1?"))
        qs.set_answer(0, "Answer 1")
        assert qs.questions[0].answer == "Answer 1"

    def test_set_answer_invalid_index(self):
        """Test setting answer with invalid index."""
        qs = QuestionSet(original_query="Test")
        qs.set_answer(99, "Answer")  # Should not raise

    def test_all_answered_empty(self):
        """Test all_answered with no questions."""
        qs = QuestionSet(original_query="Test")
        assert qs.all_answered() is True

    def test_all_answered_required(self):
        """Test all_answered with required questions."""
        qs = QuestionSet(original_query="Test")
        qs.add_question(ClarifyingQuestion(question="Q1?", required=True))
        assert qs.all_answered() is False

        qs.set_answer(0, "Answer")
        assert qs.all_answered() is True

    def test_all_answered_optional(self):
        """Test all_answered with optional questions."""
        qs = QuestionSet(original_query="Test")
        qs.add_question(ClarifyingQuestion(question="Q1?", required=False))
        assert qs.all_answered() is True

    def test_get_context(self):
        """Test getting context from answers."""
        qs = QuestionSet(original_query="Test")
        qs.add_question(ClarifyingQuestion(question="Q1?"))
        qs.add_question(ClarifyingQuestion(question="Q2?"))
        qs.set_answer(0, "A1")
        # Q2 unanswered

        context = qs.get_context()
        assert "Q1?" in context
        assert "A1" in context
        assert "Q2?" not in context

    def test_refine_query(self):
        """Test refining query with answers."""
        qs = QuestionSet(original_query="Research Apple")
        qs.add_question(ClarifyingQuestion(question="Which market?"))
        qs.set_answer(0, "US market")

        refined = qs.refine_query()
        assert "Research Apple" in refined
        assert "US market" in refined
        assert qs.refined_query == refined

    def test_refine_query_no_answers(self):
        """Test refining without answers returns original."""
        qs = QuestionSet(original_query="Research Apple")
        refined = qs.refine_query()
        assert refined == "Research Apple"

    def test_to_dict(self):
        """Test serialization."""
        qs = QuestionSet(original_query="Test")
        qs.add_question(ClarifyingQuestion(question="Q1?"))
        qs.refined_query = "Refined test"

        data = qs.to_dict()
        assert data["original_query"] == "Test"
        assert len(data["questions"]) == 1
        assert data["refined_query"] == "Refined test"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "original_query": "Original",
            "questions": [{"question": "Q1?", "question_type": "scope"}],
            "refined_query": "Refined",
        }
        qs = QuestionSet.from_dict(data)
        assert qs.original_query == "Original"
        assert len(qs.questions) == 1
        assert qs.refined_query == "Refined"


class TestFollowUpGenerator:
    """Tests for FollowUpGenerator class."""

    def setup_method(self):
        """Reset generator before each test."""
        reset_follow_up_generator()

    @pytest.mark.asyncio
    async def test_generate_questions_success(self):
        """Test successful question generation."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(
            return_value='[{"question": "Which market?", "type": "scope", "options": ["US", "EU"]}]'
        )

        generator = FollowUpGenerator(ai_client=mock_ai)
        question_set = await generator.generate_questions("Research Apple Inc", n=3)

        assert question_set.original_query == "Research Apple Inc"
        assert len(question_set.questions) >= 1
        assert "market" in question_set.questions[0].question.lower()

    @pytest.mark.asyncio
    async def test_generate_questions_failure(self):
        """Test question generation failure returns empty set."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(side_effect=Exception("API error"))

        generator = FollowUpGenerator(ai_client=mock_ai)
        question_set = await generator.generate_questions("Test query")

        assert len(question_set.questions) == 0
        assert question_set.original_query == "Test query"

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_json(self):
        """Test handling invalid JSON response."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value="not valid json")

        generator = FollowUpGenerator(ai_client=mock_ai)
        question_set = await generator.generate_questions("Test")

        assert len(question_set.questions) == 0

    @pytest.mark.asyncio
    async def test_ask_questions(self):
        """Test asking questions with callback."""
        generator = FollowUpGenerator()

        question_set = QuestionSet(original_query="Test")
        question_set.add_question(ClarifyingQuestion(question="Q1?"))
        question_set.add_question(ClarifyingQuestion(question="Q2?"))

        async def mock_callback(q):
            return f"Answer to {q.question}"

        result = await generator.ask_questions(question_set, mock_callback)

        assert result.questions[0].answer == "Answer to Q1?"
        assert result.questions[1].answer == "Answer to Q2?"

    @pytest.mark.asyncio
    async def test_ask_questions_uses_default(self):
        """Test asking questions uses default on empty answer."""
        generator = FollowUpGenerator()

        question_set = QuestionSet(original_query="Test")
        question_set.add_question(
            ClarifyingQuestion(question="Q1?", default="Default answer")
        )

        async def mock_callback(q):
            return ""  # Empty answer

        result = await generator.ask_questions(question_set, mock_callback)
        assert result.questions[0].answer == "Default answer"

    @pytest.mark.asyncio
    async def test_generate_and_ask(self):
        """Test full generate and ask flow."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(
            return_value='[{"question": "Focus area?", "type": "focus", "options": ["Finance", "Tech"]}]'
        )

        generator = FollowUpGenerator(ai_client=mock_ai)

        async def mock_callback(q):
            return "Finance"

        with patch("src.core.follow_up.get_settings") as mock_settings:
            mock_settings.return_value.is_headless = False
            mock_settings.return_value.is_interactive = True

            result = await generator.generate_and_ask(
                "Research Apple", mock_callback, n=1
            )

        assert "Research Apple" in result
        assert "Finance" in result

    @pytest.mark.asyncio
    async def test_generate_and_ask_headless_mode(self):
        """Test generate_and_ask skips in headless mode."""
        mock_ai = AsyncMock()
        generator = FollowUpGenerator(ai_client=mock_ai)

        async def mock_callback(q):
            raise AssertionError("Should not be called")

        with patch("src.core.follow_up.get_settings") as mock_settings:
            mock_settings.return_value.is_headless = True
            mock_settings.return_value.is_interactive = False

            result = await generator.generate_and_ask(
                "Research Apple", mock_callback
            )

        assert result == "Research Apple"
        mock_ai.generate.assert_not_called()


class TestQuestionType:
    """Tests for QuestionType enum."""

    def test_all_types_exist(self):
        """Test all expected types are defined."""
        expected = ["scope", "focus", "depth", "format", "comparison", "custom"]
        actual = [t.value for t in QuestionType]
        assert set(actual) == set(expected)

    def test_type_is_string(self):
        """Test QuestionType inherits from str."""
        assert isinstance(QuestionType.SCOPE, str)
        assert QuestionType.SCOPE == "scope"


class TestCLIFormatting:
    """Tests for CLI formatting functions."""

    def test_format_basic_question(self):
        """Test formatting basic question."""
        q = ClarifyingQuestion(question="What market?")
        formatted = format_question_for_cli(q, 0)
        assert "1." in formatted
        assert "What market?" in formatted

    def test_format_question_with_options(self):
        """Test formatting question with options."""
        q = ClarifyingQuestion(
            question="Which market?",
            options=["US", "Europe", "Asia"],
            default="US",
        )
        formatted = format_question_for_cli(q, 1)
        assert "2." in formatted
        assert "US" in formatted
        assert "Europe" in formatted
        assert "(default)" in formatted

    def test_format_question_with_default_only(self):
        """Test formatting question with default but no options."""
        q = ClarifyingQuestion(
            question="Timeframe?",
            default="Last 5 years",
        )
        formatted = format_question_for_cli(q, 0)
        assert "Last 5 years" in formatted
        assert "Default" in formatted


class TestGlobalGenerator:
    """Tests for global generator functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_follow_up_generator()

    def test_get_follow_up_generator_singleton(self):
        """Test singleton behavior."""
        gen1 = get_follow_up_generator()
        gen2 = get_follow_up_generator()
        assert gen1 is gen2

    def test_reset_follow_up_generator(self):
        """Test resetting the singleton."""
        gen1 = get_follow_up_generator()
        reset_follow_up_generator()
        gen2 = get_follow_up_generator()
        assert gen1 is not gen2
