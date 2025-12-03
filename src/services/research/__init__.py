"""
Research-related services.

Provides:
- DeepResearchService: Deep research orchestration
- IncrementalResearchService: Incremental research updates
- IterativeResearchService: Iterative research refinement
- GapAnalyzer: Research gap identification
- FollowupGenerator: Follow-up question generation
- ExistingDataAnalyzer: Analyze existing research data
"""

from .deep_research import DeepResearchService, EXTRACTION_PROMPTS
from .incremental import IncrementalResearchService, IncrementalResearchResult
from .iterative import IterativeResearchService, IterativeResearchResult, fill_market_gaps
from .gap_analyzer import GapAnalyzer, GapAnalysisResult, DataGap, generate_gap_report
from .followup_generator import FollowupGenerator, FollowupResult, FollowupQuestion, get_followup_generator
from .existing_data_analyzer import ExistingDataAnalyzer, CompanyDataAnalysis, get_data_analyzer

__all__ = [
    # Classes
    "DeepResearchService",
    "IncrementalResearchService",
    "IncrementalResearchResult",
    "IterativeResearchService",
    "IterativeResearchResult",
    "GapAnalyzer",
    "GapAnalysisResult",
    "DataGap",
    "FollowupGenerator",
    "FollowupResult",
    "FollowupQuestion",
    "ExistingDataAnalyzer",
    "CompanyDataAnalysis",
    # Constants
    "EXTRACTION_PROMPTS",
    # Functions
    "fill_market_gaps",
    "generate_gap_report",
    "get_followup_generator",
    "get_data_analyzer",
]
