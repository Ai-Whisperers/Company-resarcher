"""
Centralized Constants and Defaults for the Company Researcher System.
"""

import os

# Default Values - configurable via environment variables
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.0"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "4000"))
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "USA")
UNKNOWN_VALUE = "Unknown"

# File Paths - configurable via environment variables
PROMPTS_DIR = os.getenv("PROMPTS_DIR", "src/prompts")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
DB_PATH = os.getenv("DB_PATH", "data/tasks.db")

# Task Statuses
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Research Phases
PHASE_INITIAL = "initial_research"
PHASE_DEEP_DIVE = "deep_dive"
PHASE_SYNTHESIS = "synthesis"
PHASE_REVIEW = "review"

# Agent Names
AGENT_FINANCIAL = "Financial Agent"
AGENT_MARKET = "Market Analyst"
AGENT_COMPETITOR = "Competitor Scout"
AGENT_BRAND = "Brand Auditor"
AGENT_SALES = "Sales Agent"
