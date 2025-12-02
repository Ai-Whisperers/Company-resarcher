"""
LiteLLM Multi-Provider Support (INT-004).

Unified interface for multiple LLM providers using LiteLLM.
Supports: OpenAI, Anthropic, Gemini, Groq, Ollama, and more.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from ..core.logger import setup_logger
from ..core.config import get_settings

logger = setup_logger("llm_service")


class LLMService:
    """
    Unified LLM interface using LiteLLM.

    Provides a single API for multiple LLM providers.
    Switch between providers by simply changing the model string.

    Model format: "provider/model-name"
    Examples:
    - "openai/gpt-4-turbo"
    - "anthropic/claude-3-sonnet-20240229"
    - "gemini/gemini-pro"
    - "groq/llama-3.1-8b-instant"
    - "ollama/llama3.1"
    """

    def __init__(self, default_model: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            default_model: Default model to use (e.g., "openai/gpt-4-turbo")
        """
        self.default_model = default_model or self._get_default_model()
        self._setup_api_keys()

    def _get_default_model(self) -> str:
        """Get default model from settings."""
        settings = get_settings()
        primary = settings.ai.primary

        model_map = {
            "openai": f"openai/{settings.ai.openai.model}",
            "anthropic": f"anthropic/{settings.ai.anthropic.model}",
            "gemini": f"gemini/{settings.ai.gemini.model}",
            "groq": f"groq/{settings.ai.groq.model}",
            "ollama": f"ollama/{settings.ai.ollama.model}",
        }

        return model_map.get(primary, "openai/gpt-4-turbo")

    def _setup_api_keys(self):
        """Setup API keys for LiteLLM from settings."""
        import os
        settings = get_settings()

        # LiteLLM reads from environment variables
        if settings.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY.get_secret_value()
        if settings.ANTHROPIC_API_KEY:
            os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY.get_secret_value()
        if settings.GEMINI_API_KEY:
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY.get_secret_value()
        if settings.GROQ_API_KEY:
            os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY.get_secret_value()

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs,
    ) -> Union[str, Any]:
        """
        Generate completion using LiteLLM.

        Args:
            prompt: User prompt
            model: Model to use (default: self.default_model)
            system: System prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: If True, return async generator for streaming
            **kwargs: Additional arguments passed to LiteLLM

        Returns:
            Generated text or async generator if streaming
        """
        try:
            from litellm import acompletion
        except ImportError:
            raise ImportError(
                "litellm not installed. Install with: pip install litellm"
            )

        model = model or self.default_model

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            if stream:
                return self._stream_completion(
                    model, messages, temperature, max_tokens, **kwargs
                )
            else:
                response = await acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LiteLLM completion failed: {str(e)}")
            raise

    async def _stream_completion(
        self,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        **kwargs,
    ):
        """Stream completion responses."""
        from litellm import acompletion

        response = await acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def complete_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        """
        Generate completion for a conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional arguments

        Returns:
            Generated response text
        """
        try:
            from litellm import acompletion
        except ImportError:
            raise ImportError("litellm not installed")

        model = model or self.default_model

        response = await acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return response.choices[0].message.content

    async def complete_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """
        Generate JSON output.

        Args:
            prompt: User prompt (should request JSON output)
            model: Model to use
            system: System prompt
            **kwargs: Additional arguments

        Returns:
            Parsed JSON dict
        """
        import json

        # Add JSON instruction to system prompt
        json_system = (system or "") + "\nRespond with valid JSON only."

        response = await self.complete(
            prompt=prompt,
            model=model,
            system=json_system.strip(),
            **kwargs,
        )

        # Parse JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "Invalid JSON", "raw_response": response}

    def get_available_models(self) -> List[str]:
        """Get list of supported model prefixes."""
        return [
            "openai/gpt-4-turbo",
            "openai/gpt-4o",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-opus-20240229",
            "anthropic/claude-3-sonnet-20240229",
            "anthropic/claude-3-haiku-20240307",
            "gemini/gemini-pro",
            "gemini/gemini-1.5-pro",
            "groq/llama-3.1-8b-instant",
            "groq/llama-3.1-70b-versatile",
            "groq/mixtral-8x7b-32768",
            "ollama/llama3.1",
            "ollama/mistral",
        ]

    def is_available(self) -> bool:
        """Check if LiteLLM is available."""
        try:
            import litellm
            return True
        except ImportError:
            return False


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service(default_model: Optional[str] = None) -> LLMService:
    """Get or create the singleton LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(default_model)
    return _llm_service
