"""
Cost-tracking AI client wrapper.

Wraps any BaseAIClient to automatically track token usage and costs.
"""

import tiktoken
from typing import Optional

from ..ai import BaseAIClient
from ...cost_tracker import get_cost_tracker, CostTracker
from ...logger import setup_logger

logger = setup_logger("cost_tracked_client")


class CostTrackedAIClient(BaseAIClient):
    """
    Wrapper that tracks costs for all AI API calls.

    Uses tiktoken for token estimation (exact for OpenAI, approximate for others).
    """

    def __init__(
        self,
        wrapped_client: BaseAIClient,
        cost_tracker: Optional[CostTracker] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize the cost-tracking wrapper.

        Args:
            wrapped_client: The AI client to wrap.
            cost_tracker: Optional CostTracker instance. Uses global if not provided.
            model_name: Optional model name override for cost calculation.
        """
        self.wrapped_client = wrapped_client
        self.cost_tracker = cost_tracker or get_cost_tracker()
        self._model_name = model_name
        self._tokenizer = None

        # Try to initialize tiktoken for accurate token counting
        try:
            # Use cl100k_base encoding which is used by GPT-4, Claude, etc.
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not initialize tiktoken: {e}. Using estimation.")

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for.

        Returns:
            Token count (estimated if tiktoken unavailable).
        """
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        # Rough estimation: ~4 characters per token on average
        return len(text) // 4

    def _get_model_name(self) -> str:
        """Get the model name for cost tracking."""
        if self._model_name:
            return self._model_name

        # Try to get model from wrapped client
        if hasattr(self.wrapped_client, "model"):
            return self.wrapped_client.model

        # Infer from provider name
        provider = self.wrapped_client.get_provider_name().lower()
        if "openai" in provider:
            return "gpt-4-turbo-preview"
        elif "anthropic" in provider:
            return "claude-3-opus-20240229"
        elif "gemini" in provider:
            return "gemini-1.5-pro-latest"
        elif "groq" in provider:
            return "llama-3.1-8b-instant"
        elif "ollama" in provider:
            return "llama3.1:8b"

        return "unknown"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """
        Generate a response and track the cost.

        Args:
            prompt: User prompt.
            system: Optional system prompt.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.
            response_format: Response format ("text" or "json").

        Returns:
            Generated response text.
        """
        # Count input tokens
        input_text = prompt
        if system:
            input_text = f"{system}\n\n{prompt}"
        input_tokens = self._count_tokens(input_text)

        # Generate response
        response = await self.wrapped_client.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        # Count output tokens
        output_tokens = self._count_tokens(response)

        # Track cost
        model_name = self._get_model_name()
        cost = self.cost_tracker.add(
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        logger.debug(
            f"API call: {model_name} - {input_tokens} in / {output_tokens} out - ${cost:.6f}"
        )

        return response

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return f"CostTracked<{self.wrapped_client.get_provider_name()}>"

    def get_total_cost(self) -> float:
        """Get total cost tracked so far."""
        return self.cost_tracker.total_cost

    def get_remaining_budget(self) -> float:
        """Get remaining budget."""
        return self.cost_tracker.remaining_budget

    def is_budget_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return self.cost_tracker.budget_exceeded

    def print_cost_summary(self):
        """Print the cost summary."""
        print(self.cost_tracker.format_summary())
