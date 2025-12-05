"""
AI Client Module.

Provides a modular, extensible AI client system with:
- Multiple provider support (OpenAI, Anthropic, Gemini, Groq, Ollama)
- Automatic fallback chain
- Circuit breaker protection
- Rate limiting integration
- Caching support
- LangChain integration

Usage:
    # Legacy usage (still supported)
    from src.infrastructure.ai import get_ai_manager, AIClientManager
    manager = get_ai_manager()
    response = await manager.generate("Hello, world!")

    # NEW: LangChain-based usage (recommended)
    from src.infrastructure.ai import get_chat_model, get_model_factory
    model = get_chat_model()
    response = await model.ainvoke([HumanMessage(content="Hello")])

    # Task-optimized model selection
    model = get_chat_model(task_type="fast")  # Low latency
    model = get_chat_model(task_type="smart")  # Best quality
"""

from .base import BaseAIClient
from .manager import AIClientManager, get_ai_manager
from .clients import (
    OpenAIClient,
    AnthropicClient,
    GeminiClient,
    GroqClient,
    OllamaClient,
    MockAIClient,
)
from .ai_client import *
from .ai_enhancements import *
from .llm_service import *
from .fine_tuning import *
from .token_counter import *

# LangChain integration (NEW)
from .langchain_models import (
    ModelFactory,
    get_model_factory,
    get_chat_model,
    reset_model_factory,
)
from .resilience_wrappers import (
    CircuitBreakerRunnable,
    RateLimitedRunnable,
    TimeoutRunnable,
    RetryRunnable,
    wrap_with_resilience,
)
from .langsmith_setup import (
    configure_langsmith,
    disable_langsmith,
    is_langsmith_configured,
)

__all__ = [
    # Base
    "BaseAIClient",
    # Manager
    "AIClientManager",
    "get_ai_manager",
    # Clients
    "OpenAIClient",
    "AnthropicClient",
    "GeminiClient",
    "GroqClient",
    "OllamaClient",
    "MockAIClient",
    # Legacy AI client
    "AIClient",
    # Enhancements
    "AIEnhancements",
    # LLM Service
    "LLMService",
    # Fine tuning
    "FineTuning",
    # Token counter
    "TokenCounter",
    # LangChain integration (NEW)
    "ModelFactory",
    "get_model_factory",
    "get_chat_model",
    "reset_model_factory",
    # Resilience wrappers
    "CircuitBreakerRunnable",
    "RateLimitedRunnable",
    "TimeoutRunnable",
    "RetryRunnable",
    "wrap_with_resilience",
    # LangSmith
    "configure_langsmith",
    "disable_langsmith",
    "is_langsmith_configured",
]
