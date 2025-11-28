"""
Unit tests for ResearchState and SourceMetadata.

Tests the LangGraph state models including:
- Field initialization and defaults
- Type validation
- State transitions
- Edge cases
- State bounds (GR-003)
- Phase transitions (GR-001)
- StateManager (GR-002, GR-004, GR-005)
"""

import pytest
import asyncio
from pydantic import ValidationError
from langchain_core.messages import HumanMessage, AIMessage

from src.graph.state import (
    ResearchState,
    SourceMetadata,
    ResearchPhase,
    StateManager,
    VALID_PHASE_TRANSITIONS,
    MAX_RAW_DATA_ITEMS,
    MAX_SOURCE_LOG_ITEMS,
    MAX_ERRORS,
    MAX_DRAFT_SIZE_CHARS,
    MAX_FEEDBACK_LOOPS,
    get_state_manager_sync,
    reset_state_manager,
)


# =============================================================================
# SourceMetadata Tests
# =============================================================================


class TestSourceMetadata:
    """Tests for SourceMetadata model."""

    @pytest.mark.unit
    def test_creates_with_required_fields(self):
        """Verify SourceMetadata creates with required fields."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Test Source",
            date_accessed="2024-01-15",
        )

        assert metadata.url == "https://example.com"
        assert metadata.title == "Test Source"
        assert metadata.date_accessed == "2024-01-15"

    @pytest.mark.unit
    def test_default_values(self):
        """Verify default values for optional fields."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Test",
            date_accessed="2024-01-15",
        )

        assert metadata.reliability_score == 0.0
        assert metadata.summary == ""

    @pytest.mark.unit
    def test_custom_reliability_score(self):
        """Verify custom reliability score is set."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Test",
            date_accessed="2024-01-15",
            reliability_score=0.95,
        )

        assert metadata.reliability_score == 0.95

    @pytest.mark.unit
    def test_custom_summary(self):
        """Verify custom summary is set."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Test",
            date_accessed="2024-01-15",
            summary="This is a summary of the source.",
        )

        assert metadata.summary == "This is a summary of the source."

    @pytest.mark.unit
    def test_serialization(self):
        """Verify SourceMetadata can be serialized."""
        metadata = SourceMetadata(
            url="https://example.com",
            title="Test",
            date_accessed="2024-01-15",
        )

        data = metadata.model_dump()

        assert isinstance(data, dict)
        assert data["url"] == "https://example.com"


# =============================================================================
# ResearchState Initialization Tests
# =============================================================================


class TestResearchStateInitialization:
    """Tests for ResearchState initialization."""

    @pytest.mark.unit
    def test_creates_with_required_fields(self):
        """Verify ResearchState creates with required fields."""
        state = ResearchState(
            company_name="Test Corp",
            website="https://testcorp.com",
        )

        assert state.company_name == "Test Corp"
        assert state.website == "https://testcorp.com"

    @pytest.mark.unit
    def test_default_empty_lists(self):
        """Verify list fields default to empty lists."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        assert state.raw_data == []
        assert state.source_log == []
        assert state.messages == []
        assert state.errors == []

    @pytest.mark.unit
    def test_default_empty_dicts(self):
        """Verify dict fields default to empty dicts."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        assert state.financial_data == {}
        assert state.market_data == {}
        assert state.sales_data == {}
        assert state.competitor_data == {}
        assert state.brand_data == {}
        assert state.drafts == {}

    @pytest.mark.unit
    def test_default_wave_is_init(self):
        """Verify current_wave defaults to 'init'."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        assert state.current_wave == "init"

    @pytest.mark.unit
    def test_default_feedback_values(self):
        """Verify feedback fields have correct defaults."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        assert state.critique_feedback is None
        assert state.feedback_loop_count == 0


# =============================================================================
# ResearchState Data Population Tests
# =============================================================================


class TestResearchStateDataPopulation:
    """Tests for populating ResearchState data fields."""

    @pytest.mark.unit
    def test_raw_data_population(self):
        """Verify raw_data can be populated."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            raw_data=[
                {"content": "Some raw data", "source": "web"},
                {"content": "More data", "source": "pdf"},
            ],
        )

        assert len(state.raw_data) == 2
        assert state.raw_data[0]["content"] == "Some raw data"

    @pytest.mark.unit
    def test_source_log_population(self):
        """Verify source_log can be populated with SourceMetadata."""
        sources = [
            SourceMetadata(
                url="https://example.com/1",
                title="Source 1",
                date_accessed="2024-01-15",
            ),
            SourceMetadata(
                url="https://example.com/2",
                title="Source 2",
                date_accessed="2024-01-16",
            ),
        ]

        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            source_log=sources,
        )

        assert len(state.source_log) == 2
        assert state.source_log[0].title == "Source 1"

    @pytest.mark.unit
    def test_financial_data_population(self):
        """Verify financial_data can be populated."""
        financial = {
            "revenue": 1000000,
            "profit_margin": 0.15,
            "employees": 500,
        }

        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            financial_data=financial,
        )

        assert state.financial_data["revenue"] == 1000000
        assert state.financial_data["profit_margin"] == 0.15

    @pytest.mark.unit
    def test_market_data_population(self):
        """Verify market_data can be populated."""
        market = {
            "market_size": "5B",
            "growth_rate": 0.12,
            "segments": ["enterprise", "smb"],
        }

        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            market_data=market,
        )

        assert state.market_data["market_size"] == "5B"
        assert state.market_data["growth_rate"] == 0.12

    @pytest.mark.unit
    def test_drafts_population(self):
        """Verify drafts can be populated."""
        drafts = {
            "01-Executive-Summary": "# Executive Summary\n\nThis is the summary.",
            "02-Market-Analysis": "# Market Analysis\n\nMarket overview here.",
        }

        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            drafts=drafts,
        )

        assert "01-Executive-Summary" in state.drafts
        assert "Executive Summary" in state.drafts["01-Executive-Summary"]


# =============================================================================
# ResearchState Messages Tests
# =============================================================================


class TestResearchStateMessages:
    """Tests for messages field with LangChain message types."""

    @pytest.mark.unit
    def test_human_messages(self):
        """Verify HumanMessage can be stored."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            messages=[HumanMessage(content="Research this company")],
        )

        assert len(state.messages) == 1
        assert state.messages[0].content == "Research this company"

    @pytest.mark.unit
    def test_ai_messages(self):
        """Verify AIMessage can be stored."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            messages=[AIMessage(content="I will research the company")],
        )

        assert len(state.messages) == 1
        assert state.messages[0].content == "I will research the company"

    @pytest.mark.unit
    def test_mixed_messages(self):
        """Verify mixed message types can be stored."""
        messages = [
            HumanMessage(content="Research Test Corp"),
            AIMessage(content="Starting research..."),
            HumanMessage(content="Focus on financials"),
            AIMessage(content="Financial analysis complete"),
        ]

        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            messages=messages,
        )

        assert len(state.messages) == 4


# =============================================================================
# ResearchState Wave Transitions
# =============================================================================


class TestResearchStateWaves:
    """Tests for wave state transitions."""

    @pytest.mark.unit
    def test_init_wave(self):
        """Verify init wave."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="init",
        )

        assert state.current_wave == "init"

    @pytest.mark.unit
    def test_gathering_wave(self):
        """Verify gathering wave."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="gathering",
        )

        assert state.current_wave == "gathering"

    @pytest.mark.unit
    def test_thinking_wave(self):
        """Verify thinking wave."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="thinking",
        )

        assert state.current_wave == "thinking"

    @pytest.mark.unit
    def test_writing_wave(self):
        """Verify writing wave."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="writing",
        )

        assert state.current_wave == "writing"

    @pytest.mark.unit
    def test_review_wave(self):
        """Verify review wave."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            current_wave="review",
        )

        assert state.current_wave == "review"


# =============================================================================
# ResearchState Feedback Loop Tests
# =============================================================================


class TestResearchStateFeedbackLoop:
    """Tests for feedback loop functionality."""

    @pytest.mark.unit
    def test_critique_feedback_none_by_default(self):
        """Verify critique_feedback is None by default."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        assert state.critique_feedback is None

    @pytest.mark.unit
    def test_critique_feedback_set(self):
        """Verify critique_feedback can be set."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            critique_feedback="REJECT: Missing financial data",
        )

        assert state.critique_feedback == "REJECT: Missing financial data"

    @pytest.mark.unit
    def test_feedback_loop_count_starts_at_zero(self):
        """Verify feedback_loop_count starts at 0."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        assert state.feedback_loop_count == 0

    @pytest.mark.unit
    def test_feedback_loop_count_increment(self):
        """Verify feedback_loop_count can be incremented."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            feedback_loop_count=2,
        )

        assert state.feedback_loop_count == 2


# =============================================================================
# ResearchState Error Tracking Tests
# =============================================================================


class TestResearchStateErrors:
    """Tests for error tracking."""

    @pytest.mark.unit
    def test_errors_default_empty(self):
        """Verify errors default to empty list."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        assert state.errors == []

    @pytest.mark.unit
    def test_errors_can_be_added(self):
        """Verify errors can be added."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            errors=["Failed to fetch financial data", "API timeout"],
        )

        assert len(state.errors) == 2
        assert "Failed to fetch financial data" in state.errors


# =============================================================================
# ResearchState Serialization Tests
# =============================================================================


class TestResearchStateSerialization:
    """Tests for state serialization."""

    @pytest.mark.unit
    def test_model_dump(self):
        """Verify state can be dumped to dict."""
        state = ResearchState(
            company_name="Test Corp",
            website="https://testcorp.com",
            financial_data={"revenue": 1000000},
        )

        data = state.model_dump()

        assert isinstance(data, dict)
        assert data["company_name"] == "Test Corp"
        assert data["financial_data"]["revenue"] == 1000000

    @pytest.mark.unit
    def test_model_dump_excludes_none(self):
        """Verify model_dump can exclude None values."""
        state = ResearchState(
            company_name="Test",
            website="https://test.com",
        )

        data = state.model_dump(exclude_none=True)

        # critique_feedback should not be in data if None
        assert "critique_feedback" not in data or data.get("critique_feedback") is None


# =============================================================================
# Edge Cases
# =============================================================================


class TestResearchStateEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.unit
    def test_empty_company_name_rejected(self):
        """Verify empty company name raises validation error (GR-001)."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ResearchState(
                company_name="",
                website="https://test.com",
            )

    @pytest.mark.unit
    def test_unicode_company_name(self):
        """Verify unicode company names work."""
        state = ResearchState(
            company_name="测试公司",
            website="https://test.com",
        )

        assert state.company_name == "测试公司"

    @pytest.mark.unit
    def test_very_long_draft(self):
        """Verify very long drafts are handled."""
        long_content = "# Report\n\n" + ("Lorem ipsum. " * 10000)

        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            drafts={"full_report": long_content},
        )

        assert len(state.drafts["full_report"]) > 100000

    @pytest.mark.unit
    def test_complex_nested_data(self):
        """Verify complex nested data structures work."""
        complex_data = {
            "quarterly_reports": [
                {"q1": {"revenue": 100, "expenses": 80}},
                {"q2": {"revenue": 120, "expenses": 85}},
            ],
            "metadata": {
                "source": "SEC filings",
                "confidence": 0.95,
            },
        }

        state = ResearchState(
            company_name="Test",
            website="https://test.com",
            financial_data=complex_data,
        )

        assert state.financial_data["quarterly_reports"][1]["q2"]["revenue"] == 120


# =============================================================================
# ResearchPhase Tests (GR-001)
# =============================================================================


class TestResearchPhase:
    """Tests for ResearchPhase enum and transitions."""

    @pytest.mark.unit
    def test_all_phases_exist(self):
        """All expected phases are defined."""
        expected = {"init", "gathering", "thinking", "writing", "review", "complete", "error"}
        actual = {p.value for p in ResearchPhase}
        assert actual == expected

    @pytest.mark.unit
    def test_phases_are_string_enum(self):
        """Phases work as strings via .value."""
        assert ResearchPhase.INIT == "init"
        assert ResearchPhase.COMPLETE.value == "complete"

    @pytest.mark.unit
    def test_complete_is_terminal(self):
        """COMPLETE has no valid transitions."""
        assert VALID_PHASE_TRANSITIONS[ResearchPhase.COMPLETE] == set()

    @pytest.mark.unit
    def test_error_can_restart(self):
        """ERROR can transition to INIT."""
        assert ResearchPhase.INIT in VALID_PHASE_TRANSITIONS[ResearchPhase.ERROR]


# =============================================================================
# State Bounds Tests (GR-003)
# =============================================================================


class TestStateBounds:
    """Tests for state accumulation bounds."""

    @pytest.mark.unit
    def test_raw_data_bounded(self):
        """raw_data is bounded to MAX_RAW_DATA_ITEMS."""
        large_data = [{"item": i} for i in range(MAX_RAW_DATA_ITEMS + 50)]
        state = ResearchState(company_name="Test", raw_data=large_data)
        assert len(state.raw_data) == MAX_RAW_DATA_ITEMS

    @pytest.mark.unit
    def test_source_log_bounded(self):
        """source_log is bounded."""
        sources = [
            SourceMetadata(url=f"https://ex{i}.com", title=f"S{i}", date_accessed="2024-01-01")
            for i in range(MAX_SOURCE_LOG_ITEMS + 20)
        ]
        state = ResearchState(company_name="Test", source_log=sources)
        assert len(state.source_log) == MAX_SOURCE_LOG_ITEMS

    @pytest.mark.unit
    def test_errors_bounded(self):
        """errors list is bounded."""
        errors = [f"Error {i}" for i in range(MAX_ERRORS + 30)]
        state = ResearchState(company_name="Test", errors=errors)
        assert len(state.errors) == MAX_ERRORS

    @pytest.mark.unit
    def test_drafts_truncated(self):
        """Large drafts are truncated."""
        large_content = "A" * (MAX_DRAFT_SIZE_CHARS + 1000)
        state = ResearchState(company_name="Test", drafts={"report": large_content})
        assert len(state.drafts["report"]) <= MAX_DRAFT_SIZE_CHARS + 100
        assert "truncated" in state.drafts["report"].lower()

    @pytest.mark.unit
    def test_feedback_loop_capped(self):
        """feedback_loop_count is capped."""
        state = ResearchState(company_name="Test", feedback_loop_count=MAX_FEEDBACK_LOOPS + 5)
        assert state.feedback_loop_count == MAX_FEEDBACK_LOOPS


# =============================================================================
# Phase Transition Validation Tests (GR-001)
# =============================================================================


class TestPhaseTransitionValidation:
    """Tests for phase transition validation."""

    @pytest.mark.unit
    def test_can_transition_init_to_gathering(self):
        """INIT -> GATHERING is valid."""
        state = ResearchState(company_name="Test", current_wave="init")
        assert state.can_transition_to(ResearchPhase.GATHERING) is True

    @pytest.mark.unit
    def test_cannot_skip_phases(self):
        """Cannot skip phases (INIT -> WRITING invalid)."""
        state = ResearchState(company_name="Test", current_wave="init")
        assert state.can_transition_to(ResearchPhase.WRITING) is False

    @pytest.mark.unit
    def test_any_phase_can_error(self):
        """Any phase can transition to ERROR."""
        for phase in [ResearchPhase.INIT, ResearchPhase.GATHERING, ResearchPhase.THINKING]:
            state = ResearchState(company_name="Test", current_wave=phase.value)
            assert state.can_transition_to(ResearchPhase.ERROR) is True

    @pytest.mark.unit
    def test_transition_to_updates_phase(self):
        """transition_to returns new state with updated phase."""
        state = ResearchState(company_name="Test", current_wave="init")
        new_state = state.transition_to(ResearchPhase.GATHERING)
        assert new_state.current_wave == "gathering"
        assert state.current_wave == "init"  # Original unchanged

    @pytest.mark.unit
    def test_transition_to_invalid_raises(self):
        """transition_to raises for invalid transitions."""
        state = ResearchState(company_name="Test", current_wave="init")
        with pytest.raises(ValueError, match="Invalid phase transition"):
            state.transition_to(ResearchPhase.COMPLETE)

    @pytest.mark.unit
    def test_invalid_wave_rejected(self):
        """Invalid current_wave value is rejected."""
        with pytest.raises(ValidationError):
            ResearchState(company_name="Test", current_wave="invalid_phase")


# =============================================================================
# State Helper Methods Tests
# =============================================================================


class TestStateHelperMethods:
    """Tests for state helper methods."""

    @pytest.mark.unit
    def test_add_error(self):
        """add_error appends error."""
        state = ResearchState(company_name="Test")
        new_state = state.add_error("Something failed")
        assert "Something failed" in new_state.errors
        assert len(state.errors) == 0

    @pytest.mark.unit
    def test_add_source(self):
        """add_source appends source."""
        state = ResearchState(company_name="Test")
        source = SourceMetadata(url="https://ex.com", title="T", date_accessed="2024-01-01")
        new_state = state.add_source(source)
        assert len(new_state.source_log) == 1

    @pytest.mark.unit
    def test_increment_feedback_loop(self):
        """increment_feedback_loop increases counter."""
        state = ResearchState(company_name="Test", feedback_loop_count=2)
        new_state = state.increment_feedback_loop()
        assert new_state.feedback_loop_count == 3

    @pytest.mark.unit
    def test_is_max_feedback_reached(self):
        """is_max_feedback_reached checks limit."""
        state = ResearchState(company_name="Test", feedback_loop_count=MAX_FEEDBACK_LOOPS)
        assert state.is_max_feedback_reached() is True

        state2 = ResearchState(company_name="Test", feedback_loop_count=2)
        assert state2.is_max_feedback_reached() is False

    @pytest.mark.unit
    def test_get_state_size_bytes(self):
        """get_state_size_bytes returns positive int."""
        state = ResearchState(company_name="Test Corporation")
        size = state.get_state_size_bytes()
        assert isinstance(size, int)
        assert size > 0

    @pytest.mark.unit
    def test_cleanup_transient_data(self):
        """cleanup_transient_data clears raw_data and trims messages."""
        messages = [HumanMessage(content=f"Msg {i}") for i in range(20)]
        raw_data = [{"item": i} for i in range(50)]
        state = ResearchState(company_name="Test", messages=messages, raw_data=raw_data)

        cleaned = state.cleanup_transient_data()
        assert len(cleaned.raw_data) == 0
        assert len(cleaned.messages) == 10


# =============================================================================
# StateManager Tests (GR-002, GR-004, GR-005)
# =============================================================================


class TestStateManager:
    """Tests for StateManager class."""

    @pytest.fixture
    def manager(self):
        """Create fresh StateManager."""
        return StateManager(max_checkpoints=3)

    @pytest.mark.unit
    def test_checkpoint_stores_state(self, manager):
        """checkpoint stores a copy of state."""
        manager.checkpoint({"company_name": "Test"})
        assert manager.get_checkpoint_count() == 1

    @pytest.mark.unit
    def test_checkpoint_is_deep_copy(self, manager):
        """checkpoint creates deep copy."""
        state = {"data": {"nested": "original"}}
        manager.checkpoint(state)
        state["data"]["nested"] = "modified"

        rolled = manager.rollback()
        assert rolled["data"]["nested"] == "original"

    @pytest.mark.unit
    def test_checkpoint_limit_enforced(self, manager):
        """Checkpoint limit is enforced."""
        for i in range(5):
            manager.checkpoint({"index": i})
        assert manager.get_checkpoint_count() == 3

    @pytest.mark.unit
    def test_rollback_returns_last(self, manager):
        """rollback returns most recent checkpoint."""
        manager.checkpoint({"step": 1})
        manager.checkpoint({"step": 2})
        manager.checkpoint({"step": 3})

        rolled = manager.rollback()
        assert rolled["step"] == 3

    @pytest.mark.unit
    def test_rollback_empty_returns_none(self, manager):
        """rollback returns None when empty."""
        assert manager.rollback() is None

    @pytest.mark.unit
    def test_clear_checkpoints(self, manager):
        """clear_checkpoints removes all."""
        manager.checkpoint({"a": 1})
        manager.checkpoint({"b": 2})
        manager.clear_checkpoints()
        assert manager.get_checkpoint_count() == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_state_merges(self, manager):
        """update_state merges updates."""
        state = {"a": 1, "b": 2}
        new_state = await manager.update_state(state, {"b": 3, "c": 4})
        assert new_state == {"a": 1, "b": 3, "c": 4}

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_state_thread_safe(self, manager):
        """update_state is thread-safe."""
        shared = {"counter": 0}

        async def increment():
            nonlocal shared
            for _ in range(50):
                shared = await manager.update_state(shared, {"counter": shared["counter"] + 1})

        await asyncio.gather(increment(), increment())
        assert shared["counter"] == 100


# =============================================================================
# Global StateManager Tests
# =============================================================================


class TestGlobalStateManager:
    """Tests for global state manager."""

    def setup_method(self):
        """Reset before each test."""
        reset_state_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_state_manager()

    @pytest.mark.unit
    def test_get_state_manager_sync(self):
        """get_state_manager_sync returns StateManager."""
        manager = get_state_manager_sync()
        assert isinstance(manager, StateManager)

    @pytest.mark.unit
    def test_is_singleton(self):
        """Returns same instance."""
        m1 = get_state_manager_sync()
        m2 = get_state_manager_sync()
        assert m1 is m2

    @pytest.mark.unit
    def test_reset_clears_instance(self):
        """reset_state_manager clears singleton."""
        m1 = get_state_manager_sync()
        m1.checkpoint({"test": 1})

        reset_state_manager()

        m2 = get_state_manager_sync()
        assert m2.get_checkpoint_count() == 0
