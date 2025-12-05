"""
Token counting utility for LLM prompt management.
"""

import tiktoken
from src.core.logging import setup_logger

logger = setup_logger("token_counter")


class TokenCounter:
    """
    Utility to count tokens for OpenAI models.
    Helps prevent context window overflows and manage costs.
    """

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Model {model} not found, using cl100k_base")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def truncate(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within max_tokens."""
        if self.count_tokens(text) <= max_tokens:
            return text

        tokens = self.encoding.encode(text)
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)

    def check_limit(self, text: str, limit: int = 128000) -> bool:
        """Check if text exceeds token limit."""
        count = self.count_tokens(text)
        if count > limit:
            logger.warning(f"Token limit exceeded: {count} > {limit}")
            return False
        return True


# Global instance
_counter = TokenCounter()


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Helper function to count tokens."""
    return _counter.count_tokens(text)
