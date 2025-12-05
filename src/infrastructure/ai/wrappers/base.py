"""
DelegatingAIClient - Base class for AI client wrappers.

Provides the Decorator pattern for AI clients, allowing
composition of multiple behaviors (caching, rate limiting,
cost tracking, etc.) without subclassing.

Usage:
    class MyWrapper(DelegatingAIClient):
        async def generate(self, prompt, **kwargs):
            # Pre-processing
            response = await super().generate(prompt, **kwargs)
            # Post-processing
            return response
"""

from typing import Optional

from src.infrastructure.ai.base import BaseAIClient


class DelegatingAIClient(BaseAIClient):
    """
    Base class for AI client wrappers using the Decorator pattern.

    All wrapper functionality should extend this class, which
    delegates to an underlying client while allowing pre/post
    processing of requests and responses.

    Example:
        >>> wrapped = RateLimitedClient(
        ...     CachedClient(
        ...         OpenAIClient(api_key)
        ...     )
        ... )
        >>> response = await wrapped.generate("Hello")
    """

    def __init__(self, client: BaseAIClient):
        """
        Initialize the wrapper with an underlying client.

        Args:
            client: The AI client to wrap (can be another wrapper)
        """
        self._client = client

    @property
    def client(self) -> BaseAIClient:
        """Get the underlying client."""
        return self._client

    @property
    def unwrapped(self) -> BaseAIClient:
        """
        Get the innermost unwrapped client.

        Useful for accessing the actual provider when multiple
        wrappers are stacked.
        """
        current = self._client
        while isinstance(current, DelegatingAIClient):
            current = current._client
        return current

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """
        Delegate generation to the wrapped client.

        Subclasses should call super().generate() and add their
        own pre/post processing.
        """
        return await self._client.generate(
            prompt, system, temperature, max_tokens, response_format
        )

    def get_provider_name(self) -> str:
        """
        Get the provider name with wrapper indication.

        Returns format: "WrapperName<InnerProvider>"
        """
        wrapper_name = self.__class__.__name__.replace("Client", "")
        inner_name = self._client.get_provider_name()
        return f"{wrapper_name}<{inner_name}>"

    def get_inner_provider_name(self) -> str:
        """Get the innermost provider name without wrapper prefixes."""
        return self.unwrapped.get_provider_name()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} wrapping {self._client}>"
