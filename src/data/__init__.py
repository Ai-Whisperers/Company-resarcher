"""
Data layer for Company Researcher.

This module provides SQLAlchemy models and database utilities for
persisting research data to PostgreSQL.
"""

from .models import (
    Base,
    Company,
    ResearchRun,
    Source,
    Insight,
    ResearchRunStatus,
    InsightCategory,
    SourceType,
)
from .repository import (
    CompanyRepository,
    ResearchRunRepository,
    SourceRepository,
    InsightRepository,
)

__all__ = [
    # Models
    "Base",
    "Company",
    "ResearchRun",
    "Source",
    "Insight",
    # Enums
    "ResearchRunStatus",
    "InsightCategory",
    "SourceType",
    # Repositories
    "CompanyRepository",
    "ResearchRunRepository",
    "SourceRepository",
    "InsightRepository",
]
