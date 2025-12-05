"""
Prompts module - All prompt-related content consolidated.

This module contains:
- management/: Python code for prompt management (former core/prompts/)
- templates/: Markdown template files (former templates/)
- examples/: Example prompt files in .txt and .md format

The prompts module consolidates what was previously fragmented across:
- src/prompts/ (.txt files)
- src/templates/ (.md files + Python code)
- src/core/prompts/ (Python management code)

Now everything related to prompts is in one place for easier management.
"""

__all__ = ["management", "templates", "examples"]
