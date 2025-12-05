"""
Type definitions for the Company Researcher.

Re-exports all types from base module for backward compatibility.
"""

from .base import *
from .research_brief import (
    PriorityQuery,
    EntityIdentifier,
    ExclusionPattern,
    AlternativeSource,
    ResearchGap,
    CompanyHypothesis,
    ResearchIntelligenceBrief,
    create_empty_brief,
)

# Re-export everything from base for backward compatibility
