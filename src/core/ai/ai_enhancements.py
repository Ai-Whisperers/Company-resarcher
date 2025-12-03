"""
AI Enhancements Orchestrator - Unified interface for all AI enhancement modules.

This module provides a single entry point for using all AI enhancements:
1. AIRelevanceScorer - Pre-fetch result filtering
2. AISourceQualityScorer - Post-fetch quality evaluation
3. AIGapAnalyzer - Intelligent gap detection
4. AIQueryRanker - Query optimization
5. AIEntityExtractor - Named entity recognition
6. AIContradictionResolver - Conflict resolution

Usage:
    from src.core.ai.ai_enhancements import AIEnhancementOrchestrator

    orchestrator = AIEnhancementOrchestrator(
        company="COPACO",
        industry="Telecommunications",
        country="Paraguay"
    )

    # Pre-fetch: Score search results
    scored_results = await orchestrator.score_search_results(query, results)

    # Post-fetch: Evaluate source quality
    quality_scores = await orchestrator.evaluate_sources(sources)

    # Extract entities from content
    entities = await orchestrator.extract_entities(sources)

    # Analyze gaps in research
    gaps = await orchestrator.analyze_gaps(research_data)

    # Detect contradictions
    contradictions = await orchestrator.detect_contradictions(claims)
"""

from typing import List, Dict, Any, Optional
import asyncio

from ..logging import setup_logger
from .features.relevance_scorer import (
    AIRelevanceScorer,
    get_relevance_scorer,
    ScoredResult,
    reset_relevance_scorers,
)
from .features.source_quality_scorer import (
    AISourceQualityScorer,
    get_source_quality_scorer,
    QualityScore,
    reset_source_quality_scorer,
)
from .features.gap_analyzer import (
    AIGapAnalyzer,
    get_gap_analyzer,
    GapAnalysisResult,
    Gap,
    reset_gap_analyzer,
)
from .features.query_ranker import (
    AIQueryRanker,
    get_query_ranker,
    QueryRankingResult,
    RankedQuery,
    reset_query_ranker,
)
from .features.entity_extractor import (
    AIEntityExtractor,
    get_entity_extractor,
    EntityExtractionResult,
    reset_entity_extractor,
)
from .features.contradiction_resolver import (
    AIContradictionResolver,
    get_contradiction_resolver,
    ContradictionAnalysisResult,
    Claim,
    reset_contradiction_resolver,
)

logger = setup_logger("ai_enhancements")


class AIEnhancementOrchestrator:
    """
    Unified orchestrator for all AI enhancement modules.

    Provides a clean interface for the research pipeline to use
    AI-powered features without managing individual modules.
    """

    def __init__(
        self,
        company: str,
        industry: str,
        country: str = "Global",
        enable_relevance_scoring: bool = True,
        enable_quality_scoring: bool = True,
        enable_gap_analysis: bool = True,
        enable_query_ranking: bool = True,
        enable_entity_extraction: bool = True,
        enable_contradiction_detection: bool = True,
    ):
        self.company = company
        self.industry = industry
        self.country = country

        # Feature flags
        self._enable_relevance = enable_relevance_scoring
        self._enable_quality = enable_quality_scoring
        self._enable_gaps = enable_gap_analysis
        self._enable_ranking = enable_query_ranking
        self._enable_entities = enable_entity_extraction
        self._enable_contradictions = enable_contradiction_detection

        # Lazy-loaded modules
        self._relevance_scorer: Optional[AIRelevanceScorer] = None
        self._quality_scorer: Optional[AISourceQualityScorer] = None
        self._gap_analyzer: Optional[AIGapAnalyzer] = None
        self._query_ranker: Optional[AIQueryRanker] = None
        self._entity_extractor: Optional[AIEntityExtractor] = None
        self._contradiction_resolver: Optional[AIContradictionResolver] = None

        logger.info(
            f"AI Enhancement Orchestrator initialized for {company} "
            f"(relevance={enable_relevance_scoring}, quality={enable_quality_scoring}, "
            f"gaps={enable_gap_analysis}, ranking={enable_query_ranking}, "
            f"entities={enable_entity_extraction}, contradictions={enable_contradiction_detection})"
        )

    # =========================================================================
    # Module Accessors (Lazy Loading)
    # =========================================================================

    @property
    def relevance_scorer(self) -> AIRelevanceScorer:
        if self._relevance_scorer is None:
            self._relevance_scorer = get_relevance_scorer(
                self.company, self.industry, self.country
            )
        return self._relevance_scorer

    @property
    def quality_scorer(self) -> AISourceQualityScorer:
        if self._quality_scorer is None:
            self._quality_scorer = get_source_quality_scorer(
                self.company, self.industry, self.country
            )
        return self._quality_scorer

    @property
    def gap_analyzer(self) -> AIGapAnalyzer:
        if self._gap_analyzer is None:
            self._gap_analyzer = get_gap_analyzer(
                self.company, self.industry, self.country
            )
        return self._gap_analyzer

    @property
    def query_ranker(self) -> AIQueryRanker:
        if self._query_ranker is None:
            self._query_ranker = get_query_ranker(
                self.company, self.industry, self.country
            )
        return self._query_ranker

    @property
    def entity_extractor(self) -> AIEntityExtractor:
        if self._entity_extractor is None:
            self._entity_extractor = get_entity_extractor(
                self.company, self.industry, self.country
            )
        return self._entity_extractor

    @property
    def contradiction_resolver(self) -> AIContradictionResolver:
        if self._contradiction_resolver is None:
            self._contradiction_resolver = get_contradiction_resolver(
                self.company, self.industry
            )
        return self._contradiction_resolver

    # =========================================================================
    # Pre-Fetch: Search Result Scoring
    # =========================================================================

    async def score_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        target_data: str = "",
        threshold: float = 0.4,
    ) -> List[Dict[str, Any]]:
        """
        Score and filter search results before fetching.

        Args:
            query: The search query
            results: Raw search results
            target_data: What we're looking for
            threshold: Minimum relevance score

        Returns:
            Filtered list of results likely to be useful
        """
        if not self._enable_relevance or not results:
            return results

        try:
            scored = await self.relevance_scorer.score_results(
                query=query,
                results=results,
                target_data=target_data,
            )

            filtered = self.relevance_scorer.filter_by_threshold(
                scored, threshold
            )

            logger.debug(
                f"AI relevance: {len(filtered)}/{len(results)} results passed "
                f"(threshold={threshold})"
            )

            return filtered

        except Exception as e:
            logger.warning(f"Relevance scoring failed, returning all results: {e}")
            return results

    # =========================================================================
    # Post-Fetch: Source Quality Evaluation
    # =========================================================================

    async def evaluate_sources(
        self,
        sources: List[Dict[str, Any]],
        section: str = "",
        quality_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate fetched sources and return quality-sorted list.

        Args:
            sources: Fetched sources with content
            section: Target section for context
            quality_threshold: Minimum quality to keep

        Returns:
            Sources sorted by quality, filtered by threshold
        """
        if not self._enable_quality or not sources:
            return sources

        try:
            scores = await self.quality_scorer.score_sources_batch(
                sources=sources,
                target_section=section,
            )

            # Attach scores to sources
            for source, score in zip(sources, scores):
                source["_quality_score"] = score.overall_quality
                source["_has_financial"] = score.has_financial_data
                source["_has_market"] = score.has_market_data
                source["_credibility"] = score.credibility

            # Filter and sort
            filtered = [
                s for s, score in zip(sources, scores)
                if score.overall_quality >= quality_threshold
            ]
            filtered.sort(key=lambda s: s.get("_quality_score", 0), reverse=True)

            logger.debug(
                f"AI quality: {len(filtered)}/{len(sources)} sources passed "
                f"(threshold={quality_threshold})"
            )

            return filtered

        except Exception as e:
            logger.warning(f"Quality scoring failed: {e}")
            return sources

    # =========================================================================
    # Query Optimization
    # =========================================================================

    async def optimize_queries(
        self,
        queries: List[str],
        target_data: str = "",
        section: str = "",
        add_translations: bool = True,
        effectiveness_threshold: float = 0.4,
    ) -> List[str]:
        """
        Optimize queries by ranking, deduplicating, and adding variants.

        Args:
            queries: Original query list
            target_data: What we're searching for
            section: Target section
            add_translations: Add Spanish variants
            effectiveness_threshold: Minimum predicted effectiveness

        Returns:
            Optimized list of queries
        """
        if not self._enable_ranking or not queries:
            return queries

        try:
            result = await self.query_ranker.rank_queries(
                queries=queries,
                target_data=target_data,
                section=section,
                add_language_variants=add_translations,
            )

            optimized = result.get_queries_above_threshold(effectiveness_threshold)

            logger.debug(
                f"Query optimization: {len(queries)} -> {len(optimized)} "
                f"(removed {result.removed_duplicates} duplicates, "
                f"added {result.language_variants_added} variants)"
            )

            return optimized

        except Exception as e:
            logger.warning(f"Query optimization failed: {e}")
            return queries

    # =========================================================================
    # Entity Extraction
    # =========================================================================

    async def extract_entities(
        self,
        sources: List[Dict[str, Any]],
    ) -> EntityExtractionResult:
        """
        Extract structured entities from all sources.

        Args:
            sources: Sources with content

        Returns:
            Merged EntityExtractionResult
        """
        if not self._enable_entities or not sources:
            return EntityExtractionResult(source_url="", source_title="")

        try:
            extractions = await self.entity_extractor.extract_from_multiple(sources)
            merged = self.entity_extractor.merge_extractions(extractions)

            logger.debug(
                f"Entity extraction: {len(merged.people)} people, "
                f"{len(merged.companies)} companies, "
                f"{len(merged.financials)} financials"
            )

            return merged

        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return EntityExtractionResult(source_url="", source_title="")

    # =========================================================================
    # Gap Analysis
    # =========================================================================

    async def analyze_gaps(
        self,
        research_data: Dict[str, Any],
        existing_sources: int = 0,
    ) -> GapAnalysisResult:
        """
        Analyze research data for gaps and generate filling queries.

        Args:
            research_data: Current research output
            existing_sources: Number of sources collected

        Returns:
            GapAnalysisResult with prioritized gaps
        """
        if not self._enable_gaps:
            return GapAnalysisResult(company=self.company, total_gaps=0)

        try:
            result = await self.gap_analyzer.analyze_gaps(
                research_data=research_data,
                existing_sources=existing_sources,
            )

            logger.info(
                f"Gap analysis: {result.total_gaps} gaps found, "
                f"{len(result.critical_gaps)} critical, "
                f"{len(result.fillable_gaps)} fillable"
            )

            return result

        except Exception as e:
            logger.warning(f"Gap analysis failed: {e}")
            return GapAnalysisResult(company=self.company, total_gaps=0)

    async def get_gap_filling_queries(
        self,
        gaps: GapAnalysisResult,
        max_queries: int = 30,
    ) -> List[str]:
        """
        Generate queries to fill identified gaps.

        Args:
            gaps: Gap analysis result
            max_queries: Maximum queries to return

        Returns:
            List of targeted queries
        """
        queries = gaps.get_all_queries()[:max_queries]
        logger.debug(f"Generated {len(queries)} gap-filling queries")
        return queries

    # =========================================================================
    # Contradiction Detection
    # =========================================================================

    async def detect_contradictions(
        self,
        claims: List[Claim],
    ) -> ContradictionAnalysisResult:
        """
        Detect and resolve contradictions in claims.

        Args:
            claims: List of claims from sources

        Returns:
            ContradictionAnalysisResult
        """
        if not self._enable_contradictions or len(claims) < 2:
            return ContradictionAnalysisResult(
                total_claims_analyzed=len(claims),
                contradictions_found=[],
            )

        try:
            result = await self.contradiction_resolver.analyze_claims(claims)

            if result.contradictions_found:
                logger.info(
                    f"Contradiction detection: {len(result.contradictions_found)} found, "
                    f"{result.high_severity_count} high severity"
                )

            return result

        except Exception as e:
            logger.warning(f"Contradiction detection failed: {e}")
            return ContradictionAnalysisResult(
                total_claims_analyzed=len(claims),
                contradictions_found=[],
            )

    # =========================================================================
    # Combined Operations
    # =========================================================================

    async def process_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        section: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Complete pre-fetch processing: score and filter results.

        Args:
            query: Search query
            results: Raw search results
            section: Target section

        Returns:
            Filtered and scored results ready for fetching
        """
        return await self.score_search_results(
            query=query,
            results=results,
            target_data=section,
        )

    async def process_fetched_sources(
        self,
        sources: List[Dict[str, Any]],
        section: str = "",
        extract_entities: bool = True,
    ) -> Dict[str, Any]:
        """
        Complete post-fetch processing: quality score, extract entities.

        Args:
            sources: Fetched sources
            section: Target section
            extract_entities: Whether to extract entities

        Returns:
            Dict with filtered sources and extracted entities
        """
        # Quality scoring
        quality_sources = await self.evaluate_sources(
            sources=sources,
            section=section,
        )

        # Entity extraction
        entities = None
        if extract_entities:
            entities = await self.extract_entities(quality_sources)

        return {
            "sources": quality_sources,
            "entities": entities,
            "total_input": len(sources),
            "total_output": len(quality_sources),
        }


# =========================================================================
# Module Reset Functions
# =========================================================================

def reset_all_ai_enhancements():
    """Reset all AI enhancement module instances."""
    reset_relevance_scorers()
    reset_source_quality_scorer()
    reset_gap_analyzer()
    reset_query_ranker()
    reset_entity_extractor()
    reset_contradiction_resolver()
    logger.info("All AI enhancement modules reset")


# =========================================================================
# Factory Function
# =========================================================================

_orchestrator: Optional[AIEnhancementOrchestrator] = None


def get_ai_orchestrator(
    company: str,
    industry: str,
    country: str = "Global",
    **kwargs,
) -> AIEnhancementOrchestrator:
    """Get or create an AI enhancement orchestrator."""
    global _orchestrator
    if _orchestrator is None or _orchestrator.company != company:
        _orchestrator = AIEnhancementOrchestrator(
            company=company,
            industry=industry,
            country=country,
            **kwargs,
        )
    return _orchestrator


def reset_ai_orchestrator():
    """Reset the orchestrator instance."""
    global _orchestrator
    _orchestrator = None
    reset_all_ai_enhancements()


__all__ = [
    # Main orchestrator
    "AIEnhancementOrchestrator",
    "get_ai_orchestrator",
    "reset_ai_orchestrator",
    "reset_all_ai_enhancements",

    # Re-exported types
    "ScoredResult",
    "QualityScore",
    "GapAnalysisResult",
    "Gap",
    "QueryRankingResult",
    "RankedQuery",
    "EntityExtractionResult",
    "ContradictionAnalysisResult",
    "Claim",
]
