"""
Smart context trimming for managing LLM context size.

Intelligently trims accumulated context to fit within token limits while
preserving the most relevant and recent information.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.core.logging import setup_logger

logger = setup_logger("context_trimmer")

# Default context limits (configurable via environment)
DEFAULT_MAX_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "100000"))
RESPONSE_BUFFER_TOKENS = int(os.getenv("RESPONSE_BUFFER_TOKENS", "4000"))
CHARS_PER_TOKEN = float(os.getenv("CHARS_PER_TOKEN", "4.0"))


class ContentPriority(str, Enum):
    """Priority levels for context content."""
    CRITICAL = "critical"  # System prompt, current query - never trim
    HIGH = "high"         # Recent results, key findings
    MEDIUM = "medium"     # Supporting data, older results
    LOW = "low"          # Background info, can be summarized


@dataclass
class ContextItem:
    """A single item in the context."""
    content: str
    priority: ContentPriority
    timestamp: float = 0.0  # Unix timestamp for ordering
    category: str = "general"
    can_summarize: bool = True

    @property
    def token_count(self) -> int:
        """Estimate token count."""
        return estimate_tokens(self.content)

    @property
    def word_count(self) -> int:
        """Count words."""
        return len(self.content.split())


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses character-based estimation: 1 token ≈ 4 characters on average.

    Args:
        text: Text to estimate.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def estimate_tokens_from_words(word_count: int) -> int:
    """
    Estimate tokens from word count.

    Approximately 1 token = 0.75 words for English text.

    Args:
        word_count: Number of words.

    Returns:
        Estimated token count.
    """
    return int(word_count / 0.75)


class ContextTrimmer:
    """
    Intelligently trims context to fit within LLM token limits.

    Strategies:
    1. Prioritize by content priority (critical > high > medium > low)
    2. Keep most recent content within each priority
    3. Optionally summarize older content instead of dropping
    4. Always maintain a response buffer
    """

    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_buffer: int = RESPONSE_BUFFER_TOKENS,
        summarizer=None,
    ):
        """
        Initialize the context trimmer.

        Args:
            max_tokens: Maximum total tokens allowed.
            response_buffer: Tokens to reserve for response.
            summarizer: Optional async function to summarize content.
        """
        self.max_tokens = max_tokens
        self.response_buffer = response_buffer
        self.available_tokens = max_tokens - response_buffer
        self.summarizer = summarizer

    def trim_context(
        self,
        items: List[ContextItem],
    ) -> Tuple[List[ContextItem], int]:
        """
        Trim context items to fit within token limit.

        Args:
            items: List of context items to trim.

        Returns:
            Tuple of (trimmed items, total tokens used).
        """
        if not items:
            return [], 0

        # Sort by priority (critical first) then by timestamp (newest first)
        priority_order = {
            ContentPriority.CRITICAL: 0,
            ContentPriority.HIGH: 1,
            ContentPriority.MEDIUM: 2,
            ContentPriority.LOW: 3,
        }

        sorted_items = sorted(
            items,
            key=lambda x: (priority_order.get(x.priority, 4), -x.timestamp),
        )

        result = []
        total_tokens = 0

        for item in sorted_items:
            tokens = item.token_count
            if total_tokens + tokens <= self.available_tokens:
                result.append(item)
                total_tokens += tokens
            elif item.priority == ContentPriority.CRITICAL:
                # Always include critical items
                result.append(item)
                total_tokens += tokens
                logger.warning(
                    f"Including critical item despite exceeding limit: {tokens} tokens"
                )
            else:
                # Skip lower priority items when limit reached
                logger.debug(
                    f"Trimmed {item.priority.value} item: {tokens} tokens"
                )

        # Restore original order (by timestamp)
        result.sort(key=lambda x: x.timestamp)

        logger.info(
            f"Trimmed context: {len(items)} -> {len(result)} items, "
            f"{total_tokens}/{self.available_tokens} tokens"
        )

        return result, total_tokens

    def trim_text_list(
        self,
        texts: List[str],
        keep_recent: bool = True,
    ) -> List[str]:
        """
        Simple trimming of a text list.

        Args:
            texts: List of text strings to trim.
            keep_recent: If True, keeps most recent (end of list).

        Returns:
            Trimmed list of texts.
        """
        if not texts:
            return []

        # Process in order of preference
        if keep_recent:
            texts = list(reversed(texts))

        result = []
        total_tokens = 0

        for text in texts:
            tokens = estimate_tokens(text)
            if total_tokens + tokens <= self.available_tokens:
                result.append(text)
                total_tokens += tokens
            else:
                break

        # Restore order if we reversed
        if keep_recent:
            result = list(reversed(result))

        logger.info(
            f"Trimmed text list: {len(texts)} -> {len(result)} items, "
            f"{total_tokens} tokens"
        )

        return result

    def trim_dict_context(
        self,
        context: Dict[str, Any],
        priority_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Trim a dictionary context.

        Args:
            context: Dictionary to trim.
            priority_keys: Keys to prioritize (won't be trimmed).

        Returns:
            Trimmed dictionary.
        """
        priority_keys = priority_keys or []
        result = {}
        total_tokens = 0

        # First, add priority keys
        for key in priority_keys:
            if key in context:
                value = context[key]
                tokens = estimate_tokens(str(value))
                result[key] = value
                total_tokens += tokens

        # Then add other keys if there's room
        for key, value in context.items():
            if key in priority_keys:
                continue

            tokens = estimate_tokens(str(value))
            if total_tokens + tokens <= self.available_tokens:
                result[key] = value
                total_tokens += tokens

        return result

    async def trim_with_summarization(
        self,
        items: List[ContextItem],
    ) -> Tuple[List[ContextItem], int]:
        """
        Trim context with summarization of older content.

        Requires a summarizer function to be provided.

        Args:
            items: List of context items.

        Returns:
            Tuple of (trimmed items with summaries, total tokens).
        """
        if self.summarizer is None:
            return self.trim_context(items)

        # First pass: separate by priority
        critical = [i for i in items if i.priority == ContentPriority.CRITICAL]
        high = [i for i in items if i.priority == ContentPriority.HIGH]
        medium = [i for i in items if i.priority == ContentPriority.MEDIUM]
        low = [i for i in items if i.priority == ContentPriority.LOW]

        result = list(critical)  # Always keep critical
        total_tokens = sum(i.token_count for i in result)

        # Add high priority items
        for item in sorted(high, key=lambda x: -x.timestamp):
            if total_tokens + item.token_count <= self.available_tokens:
                result.append(item)
                total_tokens += item.token_count

        # Summarize medium/low priority if needed
        remaining_tokens = self.available_tokens - total_tokens

        if remaining_tokens > 1000 and (medium or low):
            # Combine and summarize older content
            to_summarize = medium + low
            combined_text = "\n\n".join(i.content for i in to_summarize)

            try:
                summary = await self.summarizer(
                    combined_text,
                    max_length=remaining_tokens * 3,  # Rough char limit
                )

                summary_item = ContextItem(
                    content=summary,
                    priority=ContentPriority.MEDIUM,
                    timestamp=max(i.timestamp for i in to_summarize),
                    category="summary",
                    can_summarize=False,
                )
                result.append(summary_item)
                total_tokens += summary_item.token_count

                logger.info(
                    f"Summarized {len(to_summarize)} items into {summary_item.token_count} tokens"
                )

            except Exception as e:
                logger.error(f"Summarization failed: {e}")

        return result, total_tokens


def create_context_item(
    content: str,
    priority: str = "medium",
    timestamp: float = 0.0,
    category: str = "general",
) -> ContextItem:
    """
    Create a context item with string priority.

    Args:
        content: The content text.
        priority: Priority level ("critical", "high", "medium", "low").
        timestamp: Unix timestamp.
        category: Content category.

    Returns:
        ContextItem instance.
    """
    priority_map = {
        "critical": ContentPriority.CRITICAL,
        "high": ContentPriority.HIGH,
        "medium": ContentPriority.MEDIUM,
        "low": ContentPriority.LOW,
    }
    return ContextItem(
        content=content,
        priority=priority_map.get(priority.lower(), ContentPriority.MEDIUM),
        timestamp=timestamp,
        category=category,
    )


# Convenience function for simple list trimming
def trim_to_token_limit(
    texts: List[str],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    keep_recent: bool = True,
) -> List[str]:
    """
    Trim a list of texts to fit within a token limit.

    Args:
        texts: List of text strings.
        max_tokens: Maximum tokens allowed.
        keep_recent: Keep most recent (end of list) items.

    Returns:
        Trimmed list of texts.
    """
    trimmer = ContextTrimmer(max_tokens=max_tokens, response_buffer=0)
    return trimmer.trim_text_list(texts, keep_recent=keep_recent)
