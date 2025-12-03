"""
AI-powered feature modules.

Provides intelligent analysis capabilities:
- QueryPlanner: Plan optimal search queries
- GapAnalyzer: Identify missing information
- RelevanceScorer: Score content relevance
- EntityExtractor: Extract entities from text
- ContradictionResolver: Resolve conflicting information
- QueryRanker: Rank search queries
- SourceQualityScorer: Score source quality
"""

from .query_planner import AIQueryPlanner, QueryPlan, get_query_planner, reset_query_planner
from .gap_analyzer import AIGapAnalyzer, get_gap_analyzer, GapAnalysisResult, Gap, reset_gap_analyzer
from .relevance_scorer import AIRelevanceScorer, get_relevance_scorer, ScoredResult, reset_relevance_scorers
from .entity_extractor import AIEntityExtractor, get_entity_extractor, EntityExtractionResult, reset_entity_extractor
from .contradiction_resolver import AIContradictionResolver, get_contradiction_resolver, ContradictionAnalysisResult, Claim, reset_contradiction_resolver
from .query_ranker import AIQueryRanker, get_query_ranker, QueryRankingResult, RankedQuery, reset_query_ranker
from .source_quality_scorer import AISourceQualityScorer, get_source_quality_scorer, QualityScore, reset_source_quality_scorer

__all__ = [
    # Classes
    "AIQueryPlanner",
    "AIGapAnalyzer",
    "AIRelevanceScorer",
    "AIEntityExtractor",
    "AIContradictionResolver",
    "AIQueryRanker",
    "AISourceQualityScorer",
    # Data classes
    "QueryPlan",
    "GapAnalysisResult",
    "Gap",
    "ScoredResult",
    "EntityExtractionResult",
    "ContradictionAnalysisResult",
    "Claim",
    "QueryRankingResult",
    "RankedQuery",
    "QualityScore",
    # Factory functions
    "get_query_planner",
    "get_gap_analyzer",
    "get_relevance_scorer",
    "get_entity_extractor",
    "get_contradiction_resolver",
    "get_query_ranker",
    "get_source_quality_scorer",
    # Reset functions
    "reset_query_planner",
    "reset_gap_analyzer",
    "reset_relevance_scorers",
    "reset_entity_extractor",
    "reset_contradiction_resolver",
    "reset_query_ranker",
    "reset_source_quality_scorer",
]
