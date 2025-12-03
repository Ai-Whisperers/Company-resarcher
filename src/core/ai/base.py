"""
Base AI Client abstract class.

Defines the interface that all AI clients must implement.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from ..result import Result, Ok, Err, AIError
from ..exceptions import AIRateLimitError, AIProviderError


class BaseAIClient(ABC):
    """
    Abstract base class for AI clients.

    All AI provider clients (OpenAI, Anthropic, Gemini, etc.) must
    inherit from this class and implement the generate() method.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """
        Generate a response from the AI model.

        Args:
            prompt: The user prompt to send
            system: Optional system prompt
            temperature: Response temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            response_format: "text" or "json"

        Returns:
            Generated text response

        Raises:
            AIProviderError: On provider-specific errors
            AIRateLimitError: When rate limit is exceeded
        """
        pass

    async def generate_safe(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> Result[str, AIError]:
        """
        Generate response with explicit error handling via Result type.

        Returns Ok(response) on success, Err(AIError) on failure.
        This is the recommended method for new code.

        Example:
            result = await client.generate_safe("Hello")
            if result.is_ok:
                print(result.unwrap())
            else:
                print(f"Error: {result.unwrap_err()}")
        """
        try:
            response = await self.generate(
                prompt, system, temperature, max_tokens, response_format
            )
            return Ok(response)
        except AIRateLimitError:
            return Err(
                AIError.rate_limited(
                    f"Rate limit exceeded for {self.get_provider_name()}"
                )
            )
        except AIProviderError as e:
            return Err(
                AIError(
                    code=AIError.MODEL_ERROR,
                    message=str(e),
                    details={"provider": self.get_provider_name()},
                    recoverable=True,
                )
            )
        except asyncio.TimeoutError:
            return Err(
                AIError.timeout(f"Request to {self.get_provider_name()} timed out")
            )
        except Exception as e:
            return Err(
                AIError.connection_error(f"{self.get_provider_name()}: {str(e)}")
            )

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the AI provider (e.g., 'openai', 'anthropic')."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider={self.get_provider_name()}>"
