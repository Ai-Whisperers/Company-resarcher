"""
Smart AI Router - Multi-tier model routing with cost optimization.

Routes requests to appropriate models based on task complexity, balancing
cost and quality. Supports 4 tiers from ultra-fast/cheap to premium/expensive.

Cost Tiers (approximate):
- ULTRA_FAST: Groq Llama (~$0.0001/1K) - Simple extraction, formatting
- FAST: GPT-3.5/Gemini Flash (~$0.001/1K) - Summarization, basic queries
- BALANCED: Claude Sonnet/GPT-4o (~$0.01/1K) - Analysis, research
- PREMIUM: GPT-4/Claude Opus (~$0.03/1K) - Complex reasoning, synthesis
"""

import os
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..ai import BaseAIClient, OpenAIClient
from ...logger import setup_logger

logger = setup_logger("smart_router")

# Counter reset interval in seconds (default: 1 hour)
COUNTER_RESET_INTERVAL = int(os.getenv("ROUTER_COUNTER_RESET_SECONDS", "3600"))


class ModelTier(Enum):
    """Model tiers ordered by cost/capability."""

    ULTRA_FAST = "ultra_fast"  # Groq, local models - near instant, very cheap
    FAST = "fast"  # GPT-3.5, Gemini Flash - fast, cheap
    BALANCED = "balanced"  # GPT-4o, Claude Sonnet - good balance
    PREMIUM = "premium"  # GPT-4 Turbo, Claude Opus - best quality


@dataclass
class ModelConfig:
    """Configuration for a model in a tier."""

    provider: str  # "openai", "anthropic", "gemini", "groq", "ollama"
    model: str
    cost_per_1k_input: float  # Cost per 1000 input tokens
    cost_per_1k_output: float  # Cost per 1000 output tokens
    avg_latency_ms: int = 1000  # Average latency in milliseconds
    max_context: int = 8192  # Maximum context window


# Default model configurations per tier
DEFAULT_TIER_CONFIGS: dict[ModelTier, list[ModelConfig]] = {
    ModelTier.ULTRA_FAST: [
        ModelConfig("groq", "llama-3.1-8b-instant", 0.00005, 0.00008, 200, 8192),
        ModelConfig("ollama", "llama3.1:8b", 0.0, 0.0, 500, 8192),
    ],
    ModelTier.FAST: [
        ModelConfig("openai", "gpt-3.5-turbo", 0.0005, 0.0015, 500, 16385),
        ModelConfig("gemini", "gemini-1.5-flash", 0.000075, 0.0003, 400, 1000000),
    ],
    ModelTier.BALANCED: [
        ModelConfig("openai", "gpt-4o", 0.005, 0.015, 1000, 128000),
        ModelConfig("anthropic", "claude-sonnet-4-20250514", 0.003, 0.015, 1200, 200000),
    ],
    ModelTier.PREMIUM: [
        ModelConfig("openai", "gpt-4-turbo", 0.01, 0.03, 2000, 128000),
        ModelConfig("anthropic", "claude-opus-4-20250514", 0.015, 0.075, 2500, 200000),
    ],
}


@dataclass
class TaskComplexity:
    """Result of task complexity analysis."""

    tier: ModelTier
    score: float  # 0.0 to 1.0
    reasons: list[str]
    estimated_tokens: int
    requires_reasoning: bool = False
    requires_creativity: bool = False


@dataclass
class CostMetrics:
    """Cost tracking metrics."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    requests_per_tier: dict[str, int] = field(default_factory=dict)
    cost_per_tier: dict[str, float] = field(default_factory=dict)
    savings_vs_premium: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "requests_per_tier": self.requests_per_tier,
            "cost_per_tier": {k: round(v, 4) for k, v in self.cost_per_tier.items()},
            "savings_vs_premium_usd": round(self.savings_vs_premium, 4),
        }


class ComplexityAnalyzer:
    """
    Analyzes task complexity to determine appropriate model tier.

    Uses multiple signals:
    - Keyword analysis (reasoning, analysis, creativity markers)
    - Prompt length and structure
    - Response format requirements
    - Domain-specific indicators

    Performance: Uses precompiled patterns and set operations for O(1) lookups.
    """

    # Single-word keywords for O(1) set lookup
    PREMIUM_SINGLE = frozenset([
        "synthesize", "critique", "evaluate", "strategic", "recommend",
        "comprehensive", "nuanced", "implications", "trade-offs", "multi-faceted",
    ])

    BALANCED_SINGLE = frozenset([
        "analyze", "assess", "explain", "research", "investigate",
        "correlate", "interpret", "classify", "determine", "review",
    ])

    FAST_SINGLE = frozenset([
        "summarize", "list", "extract", "find", "format",
        "convert", "translate", "rewrite", "simplify",
        "shorten", "expand", "paraphrase",
    ])

    ULTRA_FAST_SINGLE = frozenset([
        "json", "parse", "validate", "check", "count",
        "clean", "normalize",
    ])

    # Domain single words
    COMPLEX_DOMAIN_SINGLE = frozenset([
        "financial", "legal", "medical", "scientific",
    ])

    def __init__(self):
        # Compile regex patterns for efficiency (PERF-002)
        self._question_pattern = re.compile(r'\?')
        self._list_pattern = re.compile(r'(list|enumerate|bullet|numbered)', re.I)
        self._json_pattern = re.compile(r'(json|structured|schema)', re.I)

        # Precompile multi-word phrase patterns for O(1) regex matching
        self._premium_phrases = re.compile(
            r'(compare and contrast|in-depth analysis|critical analysis|deep dive|thorough examination)',
            re.I
        )
        self._balanced_phrases = re.compile(
            r'(identify patterns|evaluate options)',
            re.I
        )
        self._fast_phrases = re.compile(
            r'(format as|extract field)',
            re.I
        )
        self._domain_phrases = re.compile(
            r'(technical architecture|security analysis|competitive intelligence|market analysis)',
            re.I
        )

    def _tokenize_to_set(self, text: str) -> frozenset[str]:
        """
        Tokenize text into a set of lowercase words for O(1) lookup.
        Uses simple word boundary splitting for speed.
        """
        # Split on non-alphanumeric, filter empty, convert to set
        return frozenset(word for word in re.split(r'\W+', text.lower()) if word)

    def _count_phrase_matches(self, pattern: re.Pattern, text: str) -> int:
        """Count matches of a precompiled phrase pattern."""
        return len(pattern.findall(text))

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token for English)."""
        return len(text) // 4

    def analyze(
        self,
        prompt: str,
        system: str | None = None,
        response_format: str = "text",
        max_tokens: int = 4096,
    ) -> TaskComplexity:
        """
        Analyze prompt to determine complexity tier.

        Returns TaskComplexity with tier recommendation and reasons.

        Performance: O(n) where n is text length, using set intersection
        for keyword matching instead of O(n*m) substring searches.
        """
        combined = f"{prompt} {system or ''}"
        combined_lower = combined.lower()
        reasons = []
        score = 0.0

        # Tokenize once for O(1) set lookups
        words = self._tokenize_to_set(combined)

        # Token estimation
        estimated_input_tokens = self.estimate_tokens(combined)
        estimated_output_tokens = min(max_tokens, 2000)  # Conservative estimate

        # Check for premium indicators using set intersection O(min(n,m))
        premium_single = len(words & self.PREMIUM_SINGLE)
        premium_phrases = self._count_phrase_matches(self._premium_phrases, combined_lower)
        premium_matches = premium_single + premium_phrases
        if premium_matches >= 2:
            score += 0.4
            reasons.append(f"Premium keywords found ({premium_matches})")

        # Check for balanced indicators
        balanced_single = len(words & self.BALANCED_SINGLE)
        balanced_phrases = self._count_phrase_matches(self._balanced_phrases, combined_lower)
        balanced_matches = balanced_single + balanced_phrases
        if balanced_matches >= 2:
            score += 0.25
            reasons.append(f"Analysis keywords found ({balanced_matches})")

        # Check for domain complexity
        domain_single = len(words & self.COMPLEX_DOMAIN_SINGLE)
        domain_phrases = self._count_phrase_matches(self._domain_phrases, combined_lower)
        domain_matches = domain_single + domain_phrases
        if domain_matches > 0:
            score += 0.15 * domain_matches
            reasons.append(f"Complex domain detected ({domain_matches})")

        # Prompt length factor
        if estimated_input_tokens > 4000:
            score += 0.2
            reasons.append("Long prompt (>4000 tokens)")
        elif estimated_input_tokens > 2000:
            score += 0.1
            reasons.append("Medium prompt (>2000 tokens)")

        # Multiple questions indicate complexity
        question_count = len(self._question_pattern.findall(prompt))
        if question_count > 3:
            score += 0.15
            reasons.append(f"Multiple questions ({question_count})")

        # JSON output usually simpler
        if response_format == "json" or self._json_pattern.search(combined_lower):
            score -= 0.1
            reasons.append("Structured output requested")

        # Simple task indicators reduce score using set intersection
        fast_single = len(words & self.FAST_SINGLE)
        fast_phrases = self._count_phrase_matches(self._fast_phrases, combined_lower)
        fast_matches = fast_single + fast_phrases
        if fast_matches >= 2:
            score -= 0.2
            reasons.append(f"Simple task keywords ({fast_matches})")

        ultra_fast_matches = len(words & self.ULTRA_FAST_SINGLE)
        if ultra_fast_matches >= 2:
            score -= 0.3
            reasons.append(f"Ultra-simple task keywords ({ultra_fast_matches})")

        # Clamp score
        score = max(0.0, min(1.0, score))

        # Determine tier based on score
        if score >= 0.6:
            tier = ModelTier.PREMIUM
        elif score >= 0.35:
            tier = ModelTier.BALANCED
        elif score >= 0.15:
            tier = ModelTier.FAST
        else:
            tier = ModelTier.ULTRA_FAST

        # Override for very long prompts (need larger context)
        if estimated_input_tokens > 8000:
            if tier == ModelTier.ULTRA_FAST:
                tier = ModelTier.FAST
                reasons.append("Upgraded for context length")

        return TaskComplexity(
            tier=tier,
            score=score,
            reasons=reasons or ["Default complexity"],
            estimated_tokens=estimated_input_tokens + estimated_output_tokens,
            requires_reasoning=premium_matches > 0 or balanced_matches > 1,
            requires_creativity="creative" in combined or "brainstorm" in combined,
        )


class SmartAIRouter(BaseAIClient):
    """
    Multi-tier intelligent model router with cost optimization.

    Supports 4 tiers of models and automatically routes based on task
    complexity. Tracks costs and provides detailed statistics.

    Thread-safety: All counter operations are protected by locks.

    Example:
        router = SmartAIRouter(clients={
            ModelTier.FAST: gpt35_client,
            ModelTier.BALANCED: gpt4o_client,
            ModelTier.PREMIUM: gpt4_client,
        })

        # Auto-routing based on complexity
        response = await router.generate("Summarize this text...")

        # Force specific tier
        response = await router.generate("...", force_tier=ModelTier.PREMIUM)
    """

    def __init__(
        self,
        clients: dict[ModelTier, BaseAIClient] | None = None,
        cheap_client: BaseAIClient | None = None,
        expensive_client: BaseAIClient | None = None,
        api_key: str | None = None,
        use_ollama: bool = False,
    ):
        """
        Initialize router with model clients.

        Args:
            clients: Dict mapping ModelTier to BaseAIClient
            cheap_client: Legacy support - maps to FAST tier
            expensive_client: Legacy support - maps to BALANCED tier
            api_key: API key for auto-creating OpenAI clients
            use_ollama: Use Ollama for ULTRA_FAST tier
        """
        self._clients: dict[ModelTier, BaseAIClient] = {}
        self._model_configs: dict[ModelTier, ModelConfig] = {}
        self._analyzer = ComplexityAnalyzer()
        self._lock = threading.Lock()
        self._cost_metrics = CostMetrics()
        self._counter_reset_time = time.time()

        # Legacy counters for backwards compatibility
        self._cheap_requests = 0
        self._expensive_requests = 0

        # Initialize clients
        if clients:
            self._clients = clients
        elif cheap_client and expensive_client:
            # Legacy 2-tier support
            self._clients[ModelTier.FAST] = cheap_client
            self._clients[ModelTier.BALANCED] = expensive_client
        elif api_key:
            self._initialize_openai_clients(api_key, use_ollama)
        else:
            raise ValueError("Must provide clients, cheap/expensive clients, or API key")

        # Set default configs for known clients
        self._initialize_model_configs()

        logger.info(f"SmartRouter initialized with tiers: {list(self._clients.keys())}")

    def _initialize_openai_clients(self, api_key: str, use_ollama: bool) -> None:
        """Initialize default OpenAI-based clients."""
        cheap_model = os.getenv("ROUTER_CHEAP_MODEL", "gpt-3.5-turbo")
        expensive_model = os.getenv("ROUTER_EXPENSIVE_MODEL", "gpt-4-turbo-preview")

        if use_ollama:
            from ..ai import OllamaClient
            self._clients[ModelTier.ULTRA_FAST] = OllamaClient(model="llama3.1:8b")

        self._clients[ModelTier.FAST] = OpenAIClient(api_key, model=cheap_model)
        self._clients[ModelTier.BALANCED] = OpenAIClient(api_key, model=expensive_model)

    def _initialize_model_configs(self) -> None:
        """Set up model configs based on initialized clients."""
        for tier, configs in DEFAULT_TIER_CONFIGS.items():
            if tier in self._clients:
                client = self._clients[tier]
                provider = client.get_provider_name()
                # Find matching config or use first as default
                for config in configs:
                    if config.provider == provider:
                        self._model_configs[tier] = config
                        break
                else:
                    # Use first config as fallback
                    self._model_configs[tier] = configs[0]

    def _get_best_available_tier(self, requested: ModelTier) -> ModelTier:
        """Get the best available tier at or above requested level."""
        tiers = list(ModelTier)
        requested_idx = tiers.index(requested)

        # Try requested tier first
        if requested in self._clients:
            return requested

        # Try higher tiers
        for tier in tiers[requested_idx:]:
            if tier in self._clients:
                return tier

        # Fall back to lower tiers
        for tier in reversed(tiers[:requested_idx]):
            if tier in self._clients:
                return tier

        raise ValueError(f"No clients available for any tier")

    def _record_request(
        self,
        tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record request metrics (thread-safe)."""
        with self._lock:
            # Update tier counts
            tier_name = tier.value
            self._cost_metrics.requests_per_tier[tier_name] = (
                self._cost_metrics.requests_per_tier.get(tier_name, 0) + 1
            )

            # Calculate cost
            config = self._model_configs.get(tier)
            if config:
                cost = (
                    (input_tokens / 1000) * config.cost_per_1k_input +
                    (output_tokens / 1000) * config.cost_per_1k_output
                )
                self._cost_metrics.total_cost_usd += cost
                self._cost_metrics.cost_per_tier[tier_name] = (
                    self._cost_metrics.cost_per_tier.get(tier_name, 0.0) + cost
                )

                # Calculate savings vs always using premium
                premium_config = self._model_configs.get(ModelTier.PREMIUM)
                if premium_config and tier != ModelTier.PREMIUM:
                    premium_cost = (
                        (input_tokens / 1000) * premium_config.cost_per_1k_input +
                        (output_tokens / 1000) * premium_config.cost_per_1k_output
                    )
                    self._cost_metrics.savings_vs_premium += (premium_cost - cost)

            # Update token counts
            self._cost_metrics.total_input_tokens += input_tokens
            self._cost_metrics.total_output_tokens += output_tokens

            # Legacy counter updates
            if tier in (ModelTier.ULTRA_FAST, ModelTier.FAST):
                self._cheap_requests += 1
            else:
                self._expensive_requests += 1

    def _maybe_reset_counters(self) -> None:
        """Reset counters periodically (thread-safe)."""
        now = time.time()
        with self._lock:
            if now - self._counter_reset_time >= COUNTER_RESET_INTERVAL:
                logger.info(f"Resetting router counters: {self._cost_metrics.to_dict()}")
                self._cost_metrics = CostMetrics()
                self._cheap_requests = 0
                self._expensive_requests = 0
                self._counter_reset_time = now

    @property
    def cheap_requests(self) -> int:
        """Legacy: Thread-safe access to cheap request counter."""
        with self._lock:
            return self._cheap_requests

    @property
    def expensive_requests(self) -> int:
        """Legacy: Thread-safe access to expensive request counter."""
        with self._lock:
            return self._expensive_requests

    # Legacy methods for backwards compatibility
    def _increment_cheap(self) -> None:
        with self._lock:
            self._cheap_requests += 1

    def _increment_expensive(self) -> None:
        with self._lock:
            self._expensive_requests += 1

    def _estimate_complexity(self, prompt: str, system: str = None) -> str:
        """Legacy: Simple complexity estimation."""
        complexity = self._analyzer.analyze(prompt, system)
        if complexity.tier in (ModelTier.ULTRA_FAST, ModelTier.FAST):
            return "simple"
        return "complex"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
        force_model: str | None = None,  # Legacy: "cheap" or "expensive"
        force_tier: ModelTier | None = None,
    ) -> str:
        """
        Generate response using appropriate model tier.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            response_format: "text" or "json"
            force_model: Legacy - "cheap" or "expensive"
            force_tier: Force specific ModelTier

        Returns:
            Generated response string
        """
        self._maybe_reset_counters()

        # Determine tier
        if force_tier:
            target_tier = force_tier
            reasons = ["Forced tier"]
        elif force_model == "cheap":
            target_tier = ModelTier.FAST
            reasons = ["Forced cheap (legacy)"]
        elif force_model == "expensive":
            target_tier = ModelTier.BALANCED
            reasons = ["Forced expensive (legacy)"]
        else:
            complexity = self._analyzer.analyze(prompt, system, response_format, max_tokens)
            target_tier = complexity.tier
            reasons = complexity.reasons

        # Get best available tier
        actual_tier = self._get_best_available_tier(target_tier)
        client = self._clients[actual_tier]

        if actual_tier != target_tier:
            logger.debug(f"Requested {target_tier.value} but using {actual_tier.value}")

        # Log routing decision
        config = self._model_configs.get(actual_tier)
        cost_info = f"~${config.cost_per_1k_input}/1K" if config else "unknown"
        logger.info(
            f"Routing to {actual_tier.value.upper()} ({client.get_provider_name()}) "
            f"[{cost_info}] - {', '.join(reasons[:2])}"
        )

        # Generate response
        response = await client.generate(
            prompt, system, temperature, max_tokens, response_format
        )

        # Record metrics
        input_tokens = self._analyzer.estimate_tokens(f"{prompt} {system or ''}")
        output_tokens = self._analyzer.estimate_tokens(response)
        self._record_request(actual_tier, input_tokens, output_tokens)

        return response

    def get_provider_name(self) -> str:
        """Return router info."""
        tier_info = ", ".join(
            f"{t.value}={c.get_provider_name()}"
            for t, c in self._clients.items()
        )
        return f"SmartRouter({tier_info})"

    def get_stats(self) -> dict[str, Any]:
        """Get routing and cost statistics."""
        with self._lock:
            total = self._cheap_requests + self._expensive_requests
            cheap_percent = (self._cheap_requests / total * 100) if total > 0 else 0

            return {
                # Legacy stats
                "cheap_requests": self._cheap_requests,
                "expensive_requests": self._expensive_requests,
                "total_requests": total,
                "cheap_percentage": round(cheap_percent, 2),
                "estimated_cost_savings_percent": round(cheap_percent * 0.97, 2),
                # New detailed stats
                "cost_metrics": self._cost_metrics.to_dict(),
                "available_tiers": [t.value for t in self._clients.keys()],
            }

    def get_cost_metrics(self) -> CostMetrics:
        """Get detailed cost metrics."""
        with self._lock:
            return self._cost_metrics


# Backwards compatibility aliases
CHEAP_MODEL = os.getenv("ROUTER_CHEAP_MODEL", "gpt-3.5-turbo")
EXPENSIVE_MODEL = os.getenv("ROUTER_EXPENSIVE_MODEL", "gpt-4-turbo-preview")


__all__ = [
    "SmartAIRouter",
    "ModelTier",
    "ModelConfig",
    "TaskComplexity",
    "CostMetrics",
    "ComplexityAnalyzer",
    "DEFAULT_TIER_CONFIGS",
]
