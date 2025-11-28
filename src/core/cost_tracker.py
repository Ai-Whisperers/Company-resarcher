"""
Cost tracking for AI API usage.

Tracks token usage and estimates costs across different AI providers.
"""

import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .logger import setup_logger

logger = setup_logger("cost_tracker")


@dataclass
class ModelPricing:
    """Pricing for a specific model (per 1M tokens)."""

    input_price: float  # USD per 1M input tokens
    output_price: float  # USD per 1M output tokens


# Pricing per 1 million tokens (as of late 2024)
MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI
    "gpt-4-turbo-preview": ModelPricing(input_price=10.0, output_price=30.0),
    "gpt-4-turbo": ModelPricing(input_price=10.0, output_price=30.0),
    "gpt-4o": ModelPricing(input_price=2.50, output_price=10.0),
    "gpt-4o-mini": ModelPricing(input_price=0.15, output_price=0.60),
    "gpt-4": ModelPricing(input_price=30.0, output_price=60.0),
    "gpt-3.5-turbo": ModelPricing(input_price=0.50, output_price=1.50),
    # Anthropic
    "claude-3-opus-20240229": ModelPricing(input_price=15.0, output_price=75.0),
    "claude-3-sonnet-20240229": ModelPricing(input_price=3.0, output_price=15.0),
    "claude-3-haiku-20240307": ModelPricing(input_price=0.25, output_price=1.25),
    "claude-3-5-sonnet-20241022": ModelPricing(input_price=3.0, output_price=15.0),
    # Gemini
    "gemini-1.5-pro-latest": ModelPricing(input_price=3.50, output_price=10.50),
    "gemini-1.5-flash-latest": ModelPricing(input_price=0.35, output_price=1.05),
    "gemini-1.0-pro": ModelPricing(input_price=0.50, output_price=1.50),
    # Groq (very cheap due to inference optimization)
    "llama-3.1-8b-instant": ModelPricing(input_price=0.05, output_price=0.08),
    "llama-3.1-70b-versatile": ModelPricing(input_price=0.59, output_price=0.79),
    "mixtral-8x7b-32768": ModelPricing(input_price=0.24, output_price=0.24),
    # Ollama (free, local)
    "llama3": ModelPricing(input_price=0.0, output_price=0.0),
    "llama3.1:8b": ModelPricing(input_price=0.0, output_price=0.0),
    "mistral": ModelPricing(input_price=0.0, output_price=0.0),
}

# Default pricing for unknown models
DEFAULT_PRICING = ModelPricing(input_price=1.0, output_price=2.0)

# Budget limit from environment (USD)
DEFAULT_BUDGET_LIMIT = float(os.getenv("AI_BUDGET_LIMIT", "10.0"))


@dataclass
class TokenUsage:
    """Token usage for a single API call."""

    model: str
    input_tokens: int
    output_tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: Optional[str] = None


@dataclass
class CostSummary:
    """Summary of costs for a session or period."""

    total_cost: float
    total_input_tokens: int
    total_output_tokens: int
    calls_count: int
    by_model: Dict[str, Dict[str, float]]


class CostTracker:
    """
    Tracks token usage and estimates costs for AI API calls.

    Thread-safe singleton that can be used across the application.
    """

    def __init__(self, budget_limit: Optional[float] = None):
        """
        Initialize the cost tracker.

        Args:
            budget_limit: Maximum allowed budget in USD. Defaults to AI_BUDGET_LIMIT env var.
        """
        self.budget_limit = budget_limit if budget_limit is not None else DEFAULT_BUDGET_LIMIT
        self._usage_log: List[TokenUsage] = []
        self._lock = threading.Lock()
        self._total_cost: float = 0.0
        self._budget_exceeded_callback = None

    def get_pricing(self, model: str) -> ModelPricing:
        """
        Get pricing for a model.

        Args:
            model: Model name/ID.

        Returns:
            ModelPricing for the model (defaults to DEFAULT_PRICING if unknown).
        """
        return MODEL_PRICING.get(model, DEFAULT_PRICING)

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Calculate cost for a single API call.

        Args:
            model: Model name/ID.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        pricing = self.get_pricing(model)
        input_cost = (input_tokens / 1_000_000) * pricing.input_price
        output_cost = (output_tokens / 1_000_000) * pricing.output_price
        return input_cost + output_cost

    def add(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_id: Optional[str] = None,
    ) -> float:
        """
        Record token usage from an API call.

        Args:
            model: Model name/ID.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            task_id: Optional task identifier for tracking.

        Returns:
            Cost of this API call in USD.
        """
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        usage = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            task_id=task_id,
        )

        with self._lock:
            self._usage_log.append(usage)
            self._total_cost += cost

            # Check budget
            if self._total_cost > self.budget_limit:
                logger.warning(
                    f"Budget exceeded! Total: ${self._total_cost:.4f} > Limit: ${self.budget_limit:.2f}"
                )
                if self._budget_exceeded_callback:
                    self._budget_exceeded_callback(self._total_cost, self.budget_limit)

        logger.debug(
            f"Cost tracked: {model} - {input_tokens} in / {output_tokens} out = ${cost:.6f} "
            f"(Total: ${self._total_cost:.4f})"
        )

        return cost

    def set_budget_callback(self, callback):
        """
        Set a callback to be called when budget is exceeded.

        Args:
            callback: Function with signature (total_cost: float, limit: float) -> None
        """
        self._budget_exceeded_callback = callback

    @property
    def total_cost(self) -> float:
        """Get total accumulated cost."""
        with self._lock:
            return self._total_cost

    @property
    def remaining_budget(self) -> float:
        """Get remaining budget."""
        with self._lock:
            return max(0, self.budget_limit - self._total_cost)

    @property
    def budget_exceeded(self) -> bool:
        """Check if budget has been exceeded."""
        with self._lock:
            return self._total_cost > self.budget_limit

    def get_summary(self) -> CostSummary:
        """
        Get a summary of all tracked costs.

        Returns:
            CostSummary with aggregated statistics.
        """
        with self._lock:
            by_model: Dict[str, Dict[str, float]] = {}

            for usage in self._usage_log:
                if usage.model not in by_model:
                    by_model[usage.model] = {
                        "cost": 0.0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "calls": 0,
                    }

                cost = self.calculate_cost(
                    usage.model, usage.input_tokens, usage.output_tokens
                )
                by_model[usage.model]["cost"] += cost
                by_model[usage.model]["input_tokens"] += usage.input_tokens
                by_model[usage.model]["output_tokens"] += usage.output_tokens
                by_model[usage.model]["calls"] += 1

            total_input = sum(u.input_tokens for u in self._usage_log)
            total_output = sum(u.output_tokens for u in self._usage_log)

            return CostSummary(
                total_cost=self._total_cost,
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                calls_count=len(self._usage_log),
                by_model=by_model,
            )

    def get_usage_log(self) -> List[TokenUsage]:
        """Get a copy of the usage log."""
        with self._lock:
            return list(self._usage_log)

    def reset(self):
        """Reset all tracked usage and costs."""
        with self._lock:
            self._usage_log.clear()
            self._total_cost = 0.0
        logger.info("Cost tracker reset")

    def format_summary(self) -> str:
        """
        Format the cost summary as a human-readable string.

        Returns:
            Formatted summary string.
        """
        summary = self.get_summary()

        lines = [
            "=" * 50,
            "COST SUMMARY",
            "=" * 50,
            f"Total Cost: ${summary.total_cost:.4f}",
            f"Budget Limit: ${self.budget_limit:.2f}",
            f"Remaining: ${self.remaining_budget:.4f}",
            f"Total Calls: {summary.calls_count}",
            f"Total Tokens: {summary.total_input_tokens:,} in / {summary.total_output_tokens:,} out",
            "",
            "By Model:",
        ]

        for model, stats in summary.by_model.items():
            lines.append(
                f"  {model}: ${stats['cost']:.4f} "
                f"({stats['calls']} calls, {int(stats['input_tokens']):,} in / {int(stats['output_tokens']):,} out)"
            )

        lines.append("=" * 50)
        return "\n".join(lines)


# Global singleton
_cost_tracker: Optional[CostTracker] = None
_cost_tracker_lock = threading.Lock()


def get_cost_tracker(budget_limit: Optional[float] = None) -> CostTracker:
    """
    Get or create the global cost tracker instance.

    Args:
        budget_limit: Optional budget limit (only used if creating new instance).

    Returns:
        The global CostTracker instance.
    """
    global _cost_tracker
    if _cost_tracker is None:
        with _cost_tracker_lock:
            if _cost_tracker is None:
                _cost_tracker = CostTracker(budget_limit)
    return _cost_tracker


def reset_cost_tracker():
    """Reset the global cost tracker."""
    global _cost_tracker
    with _cost_tracker_lock:
        if _cost_tracker:
            _cost_tracker.reset()
        _cost_tracker = None
