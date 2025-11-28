"""Tests for the research progress tracking system."""

import pytest
from datetime import datetime

from src.core.progress import (
    ResearchProgress,
    ResearchStage,
    ProgressTracker,
    ProgressEvent,
    get_progress_tracker,
    reset_progress_tracker,
)


class TestResearchProgress:
    """Tests for ResearchProgress class."""

    def test_create_progress(self):
        """Test creating a progress instance."""
        progress = ResearchProgress(
            task_id="test-123",
            company_name="Test Corp",
            total_depth=3,
            total_queries=10,
        )
        assert progress.task_id == "test-123"
        assert progress.company_name == "Test Corp"
        assert progress.current_stage == ResearchStage.INITIALIZING

    def test_start(self):
        """Test starting progress tracking."""
        progress = ResearchProgress()
        progress.start()
        assert progress.started_at is not None
        assert len(progress.events) == 1
        assert progress.events[0].stage == ResearchStage.INITIALIZING

    def test_set_stage(self):
        """Test setting stage."""
        progress = ResearchProgress()
        progress.set_stage(ResearchStage.SEARCHING, "Looking for sources")

        assert progress.current_stage == ResearchStage.SEARCHING
        assert progress.current_activity == "Looking for sources"

    def test_set_query(self):
        """Test setting current query."""
        progress = ResearchProgress(total_queries=5)
        progress.set_query("test query", index=2, total=5)

        assert progress.current_query == "test query"
        assert progress.current_breadth == 2
        assert progress.total_breadth == 5

    def test_complete_query(self):
        """Test completing a query."""
        progress = ResearchProgress(total_queries=5)
        progress.complete_query()
        progress.complete_query()

        assert progress.completed_queries == 2
        assert progress.current_breadth == 2

    def test_increment_depth(self):
        """Test incrementing depth."""
        progress = ResearchProgress(total_depth=3)
        progress.increment_depth()

        assert progress.current_depth == 1
        assert progress.current_breadth == 0

    def test_add_sources(self):
        """Test adding sources."""
        progress = ResearchProgress()
        progress.add_sources(5)
        progress.add_sources(3)

        assert progress.total_sources == 8

    def test_process_source(self):
        """Test processing sources."""
        progress = ResearchProgress()
        progress.add_sources(3)
        progress.process_source()
        progress.process_source()

        assert progress.processed_sources == 2

    def test_add_error(self):
        """Test adding errors."""
        progress = ResearchProgress()
        progress.add_error("Something went wrong")

        assert len(progress.errors) == 1
        assert "Something went wrong" in progress.errors

    def test_complete(self):
        """Test completing research."""
        progress = ResearchProgress()
        progress.start()
        progress.complete()

        assert progress.current_stage == ResearchStage.COMPLETE

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        progress = ResearchProgress()
        progress.start()
        # Just check it returns a number >= 0
        assert progress.elapsed_time >= 0

    def test_query_progress(self):
        """Test query progress calculation."""
        progress = ResearchProgress(total_queries=4)
        progress.complete_query()
        progress.complete_query()

        assert progress.query_progress == 0.5

    def test_query_progress_zero_total(self):
        """Test query progress with zero total."""
        progress = ResearchProgress(total_queries=0)
        assert progress.query_progress == 0.0

    def test_source_progress(self):
        """Test source progress calculation."""
        progress = ResearchProgress()
        progress.add_sources(10)
        progress.process_source()
        progress.process_source()
        progress.process_source()

        assert progress.source_progress == 0.3

    def test_depth_progress(self):
        """Test depth progress calculation."""
        progress = ResearchProgress(total_depth=4)
        progress.increment_depth()
        progress.increment_depth()

        assert progress.depth_progress == 0.5

    def test_overall_progress_complete(self):
        """Test overall progress when complete."""
        progress = ResearchProgress()
        progress.complete()
        assert progress.overall_progress == 1.0

    def test_overall_progress_initializing(self):
        """Test overall progress when initializing."""
        progress = ResearchProgress()
        assert progress.overall_progress == 0.0

    def test_to_dict(self):
        """Test serialization."""
        progress = ResearchProgress(
            task_id="test-123",
            company_name="Test Corp",
            total_queries=5,
        )
        progress.start()
        progress.set_stage(ResearchStage.SEARCHING, "Active")

        data = progress.to_dict()

        assert data["task_id"] == "test-123"
        assert data["company_name"] == "Test Corp"
        assert data["current_stage"] == "searching"
        assert "progress" in data

    def test_format_status(self):
        """Test status formatting."""
        progress = ResearchProgress(total_queries=10)
        progress.set_stage(ResearchStage.SEARCHING, "Looking for data")

        status = progress.format_status()

        assert "SEARCHING" in status
        assert "Looking for data" in status

    def test_events_bounded(self):
        """Test that events list is bounded."""
        progress = ResearchProgress()
        for i in range(150):
            progress.set_stage(ResearchStage.SEARCHING, f"Event {i}")

        assert len(progress.events) <= 100


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    def setup_method(self):
        """Reset tracker before each test."""
        reset_progress_tracker()

    def test_create_progress(self):
        """Test creating progress via tracker."""
        tracker = ProgressTracker()
        progress = tracker.create_progress(
            task_id="test-1",
            company_name="Test",
            total_depth=2,
        )

        assert progress.task_id == "test-1"
        assert progress.started_at is not None

    def test_get_progress(self):
        """Test getting current progress."""
        tracker = ProgressTracker()
        tracker.create_progress(task_id="test-1")

        progress = tracker.get_progress()
        assert progress is not None
        assert progress.task_id == "test-1"

    def test_update(self):
        """Test updating progress."""
        tracker = ProgressTracker()
        tracker.create_progress()
        tracker.update(current_query="new query", completed_queries=5)

        progress = tracker.get_progress()
        assert progress.current_query == "new query"
        assert progress.completed_queries == 5

    def test_set_stage(self):
        """Test setting stage via tracker."""
        tracker = ProgressTracker()
        tracker.create_progress()
        tracker.set_stage(ResearchStage.ANALYZING, "Analyzing data")

        progress = tracker.get_progress()
        assert progress.current_stage == ResearchStage.ANALYZING

    def test_set_activity(self):
        """Test setting activity via tracker."""
        tracker = ProgressTracker()
        tracker.create_progress()
        tracker.set_activity("Processing documents")

        progress = tracker.get_progress()
        assert progress.current_activity == "Processing documents"

    def test_callback(self):
        """Test callback invocation."""
        tracker = ProgressTracker()
        callback_calls = []

        def on_progress(p):
            callback_calls.append(p.current_activity)

        tracker.register_callback(on_progress)
        tracker.create_progress()
        tracker.set_activity("Step 1")
        tracker.set_activity("Step 2")

        assert len(callback_calls) >= 2

    def test_unregister_callback(self):
        """Test unregistering callback."""
        tracker = ProgressTracker()
        callback_calls = []

        def on_progress(p):
            callback_calls.append(1)

        tracker.register_callback(on_progress)
        tracker.create_progress()

        tracker.unregister_callback(on_progress)
        tracker.set_activity("After unregister")

        # Should only have calls from before unregister
        initial_count = len(callback_calls)
        tracker.set_activity("Another update")
        assert len(callback_calls) == initial_count

    def test_reset(self):
        """Test resetting tracker."""
        tracker = ProgressTracker()
        tracker.create_progress()
        tracker.reset()

        assert tracker.get_progress() is None


class TestGlobalProgressTracker:
    """Tests for global progress tracker functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_progress_tracker()

    def test_get_progress_tracker_singleton(self):
        """Test singleton behavior."""
        tracker1 = get_progress_tracker()
        tracker2 = get_progress_tracker()
        assert tracker1 is tracker2

    def test_reset_progress_tracker(self):
        """Test reset clears singleton."""
        tracker1 = get_progress_tracker()
        tracker1.create_progress(task_id="test")
        reset_progress_tracker()
        tracker2 = get_progress_tracker()
        assert tracker2.get_progress() is None
