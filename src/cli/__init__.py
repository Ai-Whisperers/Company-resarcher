"""
CLI module for Company Researcher.

Provides command-line interface functionality including:
- Command handlers for various research modes
- Progress tracking and logging
- Profile loading utilities
- Output formatting

Usage:
    python main.py --help
    python main.py --batch data/research_targets/paraguay_telecom/
    python main.py --profile data/research_targets/paraguay_telecom/personal.yaml
"""

from src.cli.app import main

__all__ = ["main"]
