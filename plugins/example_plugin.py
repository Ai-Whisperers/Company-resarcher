"""
Example plugin demonstrating the plugin system.

This plugin can be used as a template for creating new plugins.
"""

from pydantic import BaseModel
from src.plugins import BaseTool


class EchoArgs(BaseModel):
    """Arguments for the echo plugin."""

    message: str
    uppercase: bool = False


class EchoPlugin(BaseTool):
    """
    A simple echo plugin that returns the input message.

    This serves as an example of how to create a plugin.
    """

    name = "echo"
    description = "Echoes back the input message, optionally in uppercase"
    version = "1.0.0"
    author = "Company Researcher Team"
    args_schema = EchoArgs

    async def run(self, message: str, uppercase: bool = False) -> str:
        """
        Echo the message back.

        Args:
            message: The message to echo.
            uppercase: If True, convert to uppercase.

        Returns:
            The echoed message.
        """
        result = message
        if uppercase:
            result = result.upper()
        return result
