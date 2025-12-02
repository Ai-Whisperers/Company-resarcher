"""
MCP (Model Context Protocol) Server for Company Researcher.

This module provides a stateful MCP server that allows AI tools to share
research data without explicit argument passing, reducing token usage
and improving efficiency.

Usage:
    from src.mcp import get_mcp_server, get_project_state

    # Get the MCP server instance
    server = get_mcp_server()

    # Access shared project state
    state = get_project_state()
"""

from .state import (
    ProjectState,
    get_project_state,
    set_project_state,
    reset_project_state,
    update_project_state,
)
from .server import get_mcp_server, create_mcp_server

__all__ = [
    # State management
    "ProjectState",
    "get_project_state",
    "set_project_state",
    "reset_project_state",
    "update_project_state",
    # Server
    "get_mcp_server",
    "create_mcp_server",
]
