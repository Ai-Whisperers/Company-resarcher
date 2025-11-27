"""
Smart AI Router - Routes requests to appropriate models based on complexity.
Dramatic cost savings by using cheaper models for simple tasks.
"""

from .ai_client import BaseAIClient, OpenAIClient
from .logger import setup_logger

logger = setup_logger("smart_router")


class SmartAIRouter(BaseAIClient):
    """
    Intelligent model router that selects the best model for the task.

    Cost savings example:
    - GPT-4: $0.03/1K tokens
    - GPT-3.5-turbo: $0.001/1K tokens
    - Savings: ~97% for simple tasks!
    """

    def __init__(
        self,
        cheap_client: BaseAIClient = None,
        expensive_client: BaseAIClient = None,
        api_key: str = None,
    ):
        """
        Args:
            cheap_client: Fast, cheap model (e.g., GPT-3.5)
            expensive_client: Slow, expensive model (e.g., GPT-4)
            api_key: API key if clients not provided
        """
        if cheap_client and expensive_client:
            self.cheap = cheap_client
            self.expensive = expensive_client
        elif api_key:
            # Default: OpenAI models
            self.cheap = OpenAIClient(api_key, model="gpt-3.5-turbo")
            self.expensive = OpenAIClient(api_key, model="gpt-4-turbo-preview")
        else:
            raise ValueError("Must provide clients or API key")

        self.cheap_requests = 0
        self.expensive_requests = 0

    def _estimate_complexity(self, prompt: str, system: str = None) -> str:
        """
        Estimate task complexity from prompt keywords.

        Returns: "simple" or "complex"
        """
        prompt_lower = prompt.lower()
        system_lower = (system or "").lower()
        combined = f"{prompt_lower} {system_lower}"

        # Keywords that indicate complex reasoning needed
        complex_keywords = [
            "analyze",
            "critique",
            "evaluate",
            "compare",
            "synthesize",
            "strategic",
            "recommend",
            "assess",
            "judge",
            "critical",
            "complex",
            "detailed analysis",
            "in-depth",
        ]

        # Keywords that indicate simple tasks
        simple_keywords = [
            "summarize",
            "list",
            "extract",
            "find",
            "search",
            "fetch",
            "get",
            "retrieve",
            "simple",
            "basic",
        ]

        complex_score = sum(1 for kw in complex_keywords if kw in combined)
        simple_score = sum(1 for kw in simple_keywords if kw in combined)

        # If prompt is very long, consider it complex
        if len(prompt) > 3000:
            complex_score += 2

        if complex_score > simple_score:
            return "complex"
        return "simple"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
        force_model: str = None,  # "cheap", "expensive", or None for auto
    ) -> str:
        """
        Generate response using appropriate model.

        Args:
            force_model: Override auto-detection ("cheap" or "expensive")
        """
        if force_model == "cheap":
            complexity = "simple"
        elif force_model == "expensive":
            complexity = "complex"
        else:
            complexity = self._estimate_complexity(prompt, system)

        # Select client
        if complexity == "simple":
            client = self.cheap
            self.cheap_requests += 1
            logger.info(
                f"Routing to CHEAP model ({client.get_provider_name()}) "
                f"- Est. savings: 97%"
            )
        else:
            client = self.expensive
            self.expensive_requests += 1
            logger.info(
                f"Routing to EXPENSIVE model ({client.get_provider_name()}) "
                f"- Complex task detected"
            )

        return await client.generate(
            prompt, system, temperature, max_tokens, response_format
        )

    def get_provider_name(self) -> str:
        """Return router info."""
        return (
            f"SmartRouter("
            f"cheap={self.cheap.get_provider_name()}, "
            f"expensive={self.expensive.get_provider_name()})"
        )

    def get_stats(self) -> dict:
        """Get routing statistics."""
        total = self.cheap_requests + self.expensive_requests
        cheap_percent = (self.cheap_requests / total * 100) if total > 0 else 0

        # Estimate savings (assuming GPT-4 vs GPT-3.5 pricing)
        estimated_savings = cheap_percent * 0.97  # 97% cheaper

        return {
            "cheap_requests": self.cheap_requests,
            "expensive_requests": self.expensive_requests,
            "total_requests": total,
            "cheap_percentage": round(cheap_percent, 2),
            "estimated_cost_savings_percent": round(estimated_savings, 2),
        }
