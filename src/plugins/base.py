"""
Base plugin interface for the Company Researcher system.

All plugins must inherit from BaseTool and implement the required interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel


class BaseTool(ABC):
    """
    Base class for all plugin tools.

    Plugins must inherit from this class and implement:
    - name: Unique identifier for the tool
    - description: Human-readable description
    - args_schema: Optional Pydantic model for argument validation
    - run: The main execution method
    """

    # Required class attributes
    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = None

    # Optional metadata
    version: str = "1.0.0"
    author: str = ""

    def __init__(self):
        """Initialize the tool."""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define a 'name' attribute")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__} must define a 'description' attribute")

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the given arguments.

        Args:
            **kwargs: Arguments for the tool, validated against args_schema if provided.

        Returns:
            The result of the tool execution.
        """
        pass

    def validate_args(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Validate arguments against the args_schema if defined.

        Args:
            **kwargs: Arguments to validate.

        Returns:
            Validated arguments as a dictionary.

        Raises:
            ValueError: If validation fails.
        """
        if self.args_schema is None:
            return kwargs

        try:
            validated = self.args_schema(**kwargs)
            return validated.model_dump()
        except Exception as e:
            raise ValueError(f"Argument validation failed for {self.name}: {e}")

    async def execute(self, **kwargs: Any) -> Any:
        """
        Validate arguments and execute the tool.

        This is the main entry point for tool execution.

        Args:
            **kwargs: Arguments for the tool.

        Returns:
            The result of the tool execution.
        """
        validated_args = self.validate_args(**kwargs)
        return await self.run(**validated_args)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tool metadata for registration and discovery.

        Returns:
            Dictionary containing tool metadata.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "args_schema": self.args_schema.model_json_schema() if self.args_schema else None,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r}, version={self.version!r})>"
