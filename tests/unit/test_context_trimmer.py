"""Tests for the smart context trimming system."""

import pytest
import time

from src.core.content.context_trimmer import (
    ContextTrimmer,
    ContextItem,
    ContentPriority,
    estimate_tokens,
    estimate_tokens_from_words,
    create_context_item,
    trim_to_token_limit,
)


class TestTokenEstimation:
    """Tests for token estimation functions."""

    def test_estimate_tokens_empty(self):
        """Test empty string returns 0."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_short(self):
        """Test short text estimation."""
        # 4 chars ≈ 1 token
        assert estimate_tokens("test") == 1

    def test_estimate_tokens_longer(self):
        """Test longer text estimation."""
        # 100 chars ≈ 25 tokens
        text = "a" * 100
        tokens = estimate_tokens(text)
        assert 20 <= tokens <= 30

    def test_estimate_tokens_from_words(self):
        """Test word-based estimation."""
        # 100 words ≈ 133 tokens (1/0.75)
        tokens = estimate_tokens_from_words(100)
        assert 130 <= tokens <= 140


class TestContextItem:
    """Tests for ContextItem class."""

    def test_create_item(self):
        """Test creating a context item."""
        item = ContextItem(
            content="Test content",
            priority=ContentPriority.HIGH,
            timestamp=1000.0,
        )
        assert item.content == "Test content"
        assert item.priority == ContentPriority.HIGH

    def test_token_count(self):
        """Test token count property."""
        item = ContextItem(content="test " * 100, priority=ContentPriority.MEDIUM)
        assert item.token_count > 0

    def test_word_count(self):
        """Test word count property."""
        item = ContextItem(content="one two three four five", priority=ContentPriority.LOW)
        assert item.word_count == 5


class TestContextTrimmer:
    """Tests for ContextTrimmer class."""

    def test_trim_empty_list(self):
        """Test trimming empty list."""
        trimmer = ContextTrimmer(max_tokens=1000)
        result, tokens = trimmer.trim_context([])
        assert result == []
        assert tokens == 0

    def test_trim_under_limit(self):
        """Test when content is under limit."""
        trimmer = ContextTrimmer(max_tokens=10000)
        items = [
            ContextItem("Short content", ContentPriority.MEDIUM),
            ContextItem("Another item", ContentPriority.LOW),
        ]

        result, tokens = trimmer.trim_context(items)
        assert len(result) == 2

    def test_trim_exceeds_limit(self):
        """Test when content exceeds limit."""
        trimmer = ContextTrimmer(max_tokens=100, response_buffer=10)
        items = [
            ContextItem("x" * 200, ContentPriority.LOW, timestamp=1),
            ContextItem("y" * 200, ContentPriority.LOW, timestamp=2),
            ContextItem("z" * 200, ContentPriority.LOW, timestamp=3),
        ]

        result, tokens = trimmer.trim_context(items)
        # Should only fit some items
        assert len(result) < 3

    def test_priority_order(self):
        """Test that higher priority items are kept."""
        trimmer = ContextTrimmer(max_tokens=100, response_buffer=0)
        items = [
            ContextItem("low content " * 20, ContentPriority.LOW, timestamp=1),
            ContextItem("high content", ContentPriority.HIGH, timestamp=2),
            ContextItem("critical", ContentPriority.CRITICAL, timestamp=3),
        ]

        result, tokens = trimmer.trim_context(items)

        # Critical and high should be included
        priorities = [i.priority for i in result]
        assert ContentPriority.CRITICAL in priorities
        assert ContentPriority.HIGH in priorities

    def test_critical_always_included(self):
        """Test that critical items are always included."""
        trimmer = ContextTrimmer(max_tokens=50, response_buffer=0)
        items = [
            ContextItem("critical content " * 10, ContentPriority.CRITICAL),
        ]

        result, tokens = trimmer.trim_context(items)
        assert len(result) == 1

    def test_recency_preserved(self):
        """Test that recency ordering is preserved."""
        trimmer = ContextTrimmer(max_tokens=10000)
        now = time.time()
        items = [
            ContextItem("first", ContentPriority.MEDIUM, timestamp=now - 100),
            ContextItem("second", ContentPriority.MEDIUM, timestamp=now - 50),
            ContextItem("third", ContentPriority.MEDIUM, timestamp=now),
        ]

        result, _ = trimmer.trim_context(items)
        # Original order should be restored
        assert result[0].content == "first"
        assert result[-1].content == "third"

    def test_trim_text_list_keep_recent(self):
        """Test simple text list trimming keeping recent."""
        trimmer = ContextTrimmer(max_tokens=100, response_buffer=0)
        texts = [
            "old content " * 50,
            "newer content",
            "newest content",
        ]

        result = trimmer.trim_text_list(texts, keep_recent=True)

        # Should keep the recent (short) ones
        assert "newest content" in result
        assert "newer content" in result

    def test_trim_text_list_keep_oldest(self):
        """Test text list trimming keeping oldest."""
        trimmer = ContextTrimmer(max_tokens=100, response_buffer=0)
        texts = [
            "oldest content",
            "older content",
            "new content " * 50,
        ]

        result = trimmer.trim_text_list(texts, keep_recent=False)
        assert "oldest content" in result

    def test_trim_dict_context(self):
        """Test dictionary context trimming."""
        trimmer = ContextTrimmer(max_tokens=100, response_buffer=0)
        context = {
            "query": "important query",
            "results": "x" * 500,
            "metadata": "y" * 500,
        }

        result = trimmer.trim_dict_context(context, priority_keys=["query"])

        assert "query" in result
        # May not include others due to size

    def test_response_buffer(self):
        """Test that response buffer is reserved."""
        trimmer = ContextTrimmer(max_tokens=1000, response_buffer=500)
        assert trimmer.available_tokens == 500


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_context_item(self):
        """Test create_context_item helper."""
        item = create_context_item(
            content="test",
            priority="high",
            timestamp=100.0,
            category="test",
        )
        assert item.priority == ContentPriority.HIGH
        assert item.category == "test"

    def test_create_context_item_invalid_priority(self):
        """Test create_context_item with invalid priority."""
        item = create_context_item(content="test", priority="invalid")
        assert item.priority == ContentPriority.MEDIUM  # Default

    def test_trim_to_token_limit(self):
        """Test trim_to_token_limit function."""
        texts = ["short", "another short", "very long " * 1000]
        result = trim_to_token_limit(texts, max_tokens=100)

        # Should not include the very long one
        assert len(result) < 3
