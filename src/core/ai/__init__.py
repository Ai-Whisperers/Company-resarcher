"""
AI Client Module.

Provides a modular, extensible AI client system with:
- Multiple provider support (OpenAI, Anthropic, Gemini, Groq, Ollama)
- Automatic fallback chain
- Circuit breaker protection
- Rate limiting integration
- Caching support

Usage:
    from src.core.ai import get_ai_manager, AIClientManager

    # Simple usage
    manager = get_ai_manager()
    response = await manager.generate("Hello, world!")

    # With task-based routing
    response = await manager.generate("Analyze this data", task_type="smart")
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
]
