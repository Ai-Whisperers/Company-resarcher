"""
Pipeline Stages - Concrete implementations of the Stage protocol.

Each stage transforms typed input to typed output using RequestContext
for all dependencies.

Available Stages:
- SearchStage: Execute web searches
- FetchStage: Fetch content from URLs
- AnalyzeStage: Generate AI analysis
- Research Stages: Domain-specific research stages
"""

from .search import SearchStage, SearchInput, SearchOutput, FailedQuery
from .fetch import FetchStage, FetchInput, FetchOutput
from .analyze import AnalyzeStage, AnalyzeInput, AnalyzeOutput
from .research import (
    ResearchInput,
    ResearchOutput,
    QueryResult,
    SearchPhaseOutput,
    AnalysisOutput,
    QueryGenerationStage,
    SearchExecutionStage,
    AnalysisStage as ResearchAnalysisStage,
    ReportGenerationStage,
    ResearchPhaseStage,
)

__all__ = [
    # Search
    "SearchStage",
    "SearchInput",
    "SearchOutput",
    "FailedQuery",
    # Fetch
    "FetchStage",
    "FetchInput",
    "FetchOutput",
    # Analyze
    "AnalyzeStage",
    "AnalyzeInput",
    "AnalyzeOutput",
    # Research
    "ResearchInput",
    "ResearchOutput",
    "QueryResult",
    "SearchPhaseOutput",
    "AnalysisOutput",
    "QueryGenerationStage",
    "SearchExecutionStage",
    "ResearchAnalysisStage",
    "ReportGenerationStage",
    "ResearchPhaseStage",
]
