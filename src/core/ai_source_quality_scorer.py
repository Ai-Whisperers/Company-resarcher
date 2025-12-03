"""
AI Source Quality Scorer - Evaluates fetched source content quality using AI.

After fetching a source, this module uses AI to evaluate:
- Content quality and depth
- Credibility and bias indicators
- Alignment with research target
- Presence of specific, verifiable facts

Benefits:
- Better source selection for analysis
- Fewer false claims in final output
- Confidence scoring for extracted data
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json

from .logger import setup_logger
from .ai_client import get_ai_manager

logger = setup_logger("ai_source_quality")


class CredibilityLevel(Enum):
    """Source credibility levels."""
    HIGH = "high"  # Official sources, reputable publications
    MEDIUM = "medium"  # General news, industry publications
    LOW = "low"  # Blogs, forums, unverified sources
    UNKNOWN = "unknown"


class BiasIndicator(Enum):
    """Detected bias indicators."""
    PROMOTIONAL = "promotional"  # Marketing/sales content
    CRITICAL = "critical"  # Negative bias
    NEUTRAL = "neutral"  # Factual, balanced
    SPECULATIVE = "speculative"  # Contains unverified claims


@dataclass
class QualityScore:
    """Comprehensive quality assessment for a source."""
    # Overall scores (0-1)
    overall_quality: float
    content_depth: float
    credibility: float
    relevance_match: float

    # Categorical assessments
    credibility_level: CredibilityLevel = CredibilityLevel.UNKNOWN
    bias_indicator: BiasIndicator = BiasIndicator.NEUTRAL

    # Specific findings
    has_financial_data: bool = False
    has_market_data: bool = False
    has_executive_info: bool = False
    has_competitive_info: bool = False
    has_recent_news: bool = False

    # Confidence in the assessment itself
    assessment_confidence: float = 0.5

    # Key facts detected (for validation)
    detected_facts: List[str] = field(default_factory=list)

    # Warnings
    warnings: List[str] = field(default_factory=list)

    def is_high_quality(self, threshold: float = 0.6) -> bool:
        """Check if source meets quality threshold."""
        return self.overall_quality >= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_quality": self.overall_quality,
            "content_depth": self.content_depth,
            "credibility": self.credibility,
            "relevance_match": self.relevance_match,
            "credibility_level": self.credibility_level.value,
            "bias_indicator": self.bias_indicator.value,
            "has_financial_data": self.has_financial_data,
            "has_market_data": self.has_market_data,
            "has_executive_info": self.has_executive_info,
            "has_competitive_info": self.has_competitive_info,
            "has_recent_news": self.has_recent_news,
            "detected_facts": self.detected_facts,
            "warnings": self.warnings,
        }


class AISourceQualityScorer:
    """
    Uses AI to evaluate the quality of fetched source content.

    This runs AFTER fetching but BEFORE analysis, helping prioritize
    which sources to use for content generation.
    """

    # Content length limits for AI evaluation
    MAX_CONTENT_LENGTH = 4000
    MIN_CONTENT_LENGTH = 100

    def __init__(
        self,
        company: str,
        industry: str,
        country: str = "Global",
    ):
        self.company = company
        self.industry = industry
        self.country = country
        self._ai_client = None
        self._cache: Dict[str, QualityScore] = {}

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self._ai_client is None:
            self._ai_client = get_ai_manager()
        return self._ai_client

    async def score_source(
        self,
        url: str,
        title: str,
        content: str,
        target_section: str = "",
    ) -> QualityScore:
        """
        Score a single source for quality.

        Args:
            url: Source URL
            title: Source title
            content: Fetched content text
            target_section: What section this source is for (e.g., "data_room")

        Returns:
            QualityScore with comprehensive assessment
        """
        # Check cache
        cache_key = f"{url}:{target_section}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Validate content
        if not content or len(content) < self.MIN_CONTENT_LENGTH:
            return QualityScore(
                overall_quality=0.1,
                content_depth=0.0,
                credibility=0.3,
                relevance_match=0.0,
                warnings=["Content too short or empty"],
            )

        # Truncate for AI
        truncated_content = content[:self.MAX_CONTENT_LENGTH]

        # Build evaluation prompt
        prompt = f"""Evaluate this source for research quality about {self.company} ({self.industry}) in {self.country}.

Source URL: {url}
Title: {title}
Target Section: {target_section or "general research"}

Content:
{truncated_content}

Evaluate and return JSON:
{{
    "overall_quality": 0.0-1.0,  // Overall usefulness for research
    "content_depth": 0.0-1.0,   // Depth of information (specific vs vague)
    "credibility": 0.0-1.0,     // Source reliability
    "relevance_match": 0.0-1.0, // Match to {self.company} specifically

    "credibility_level": "high|medium|low|unknown",
    "bias_indicator": "promotional|critical|neutral|speculative",

    "has_financial_data": true/false,   // Revenue, profit, growth numbers
    "has_market_data": true/false,      // Market size, share, trends
    "has_executive_info": true/false,   // CEO, leadership, org info
    "has_competitive_info": true/false, // Competitor mentions, comparisons
    "has_recent_news": true/false,      // Recent events, announcements

    "detected_facts": [
        "Specific fact 1 with numbers/dates",
        "Specific fact 2..."
    ],

    "warnings": [
        "Any concerns about the source..."
    ],

    "assessment_confidence": 0.0-1.0  // How confident is this assessment
}}

Quality guidelines:
- High quality (0.8-1.0): Primary sources, specific data, recent, credible
- Medium quality (0.5-0.8): Relevant info but less specific or older
- Low quality (0.2-0.5): Tangential or vague information
- Poor quality (0.0-0.2): Wrong company, outdated, or unreliable"""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a research source quality evaluator. Be objective and thorough. Return valid JSON only.",
                max_tokens=1000,
                temperature=0.1,
            )

            score = self._parse_quality_score(response)
            self._cache[cache_key] = score
            return score

        except Exception as e:
            logger.warning(f"AI source quality scoring failed: {e}")
            return QualityScore(
                overall_quality=0.5,
                content_depth=0.5,
                credibility=0.5,
                relevance_match=0.5,
                warnings=[f"AI scoring failed: {str(e)}"],
            )

    async def score_sources_batch(
        self,
        sources: List[Dict[str, Any]],
        target_section: str = "",
        max_concurrent: int = 5,
    ) -> List[QualityScore]:
        """
        Score multiple sources concurrently.

        Args:
            sources: List of source dicts with url, title, content
            target_section: Target section for all sources
            max_concurrent: Max concurrent AI calls

        Returns:
            List of QualityScore in same order as input
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def score_with_semaphore(source: Dict[str, Any]) -> QualityScore:
            async with semaphore:
                return await self.score_source(
                    url=source.get("url", ""),
                    title=source.get("title", ""),
                    content=source.get("content", ""),
                    target_section=target_section,
                )

        scores = await asyncio.gather(
            *[score_with_semaphore(s) for s in sources],
            return_exceptions=True,
        )

        # Handle exceptions
        return [
            s if isinstance(s, QualityScore)
            else QualityScore(
                overall_quality=0.3,
                content_depth=0.3,
                credibility=0.3,
                relevance_match=0.3,
                warnings=[f"Scoring error: {str(s)}"],
            )
            for s in scores
        ]

    def _parse_quality_score(self, response: str) -> QualityScore:
        """Parse AI response into QualityScore."""
        try:
            # Extract JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON object found")

            # Parse credibility level
            cred_level = data.get("credibility_level", "unknown").lower()
            try:
                credibility_level = CredibilityLevel(cred_level)
            except ValueError:
                credibility_level = CredibilityLevel.UNKNOWN

            # Parse bias indicator
            bias = data.get("bias_indicator", "neutral").lower()
            try:
                bias_indicator = BiasIndicator(bias)
            except ValueError:
                bias_indicator = BiasIndicator.NEUTRAL

            return QualityScore(
                overall_quality=min(1.0, max(0.0, float(data.get("overall_quality", 0.5)))),
                content_depth=min(1.0, max(0.0, float(data.get("content_depth", 0.5)))),
                credibility=min(1.0, max(0.0, float(data.get("credibility", 0.5)))),
                relevance_match=min(1.0, max(0.0, float(data.get("relevance_match", 0.5)))),
                credibility_level=credibility_level,
                bias_indicator=bias_indicator,
                has_financial_data=bool(data.get("has_financial_data", False)),
                has_market_data=bool(data.get("has_market_data", False)),
                has_executive_info=bool(data.get("has_executive_info", False)),
                has_competitive_info=bool(data.get("has_competitive_info", False)),
                has_recent_news=bool(data.get("has_recent_news", False)),
                detected_facts=data.get("detected_facts", [])[:10],  # Limit facts
                warnings=data.get("warnings", [])[:5],  # Limit warnings
                assessment_confidence=min(1.0, max(0.0, float(data.get("assessment_confidence", 0.5)))),
            )

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse quality score: {e}")
            return QualityScore(
                overall_quality=0.5,
                content_depth=0.5,
                credibility=0.5,
                relevance_match=0.5,
                warnings=["Failed to parse AI response"],
            )

    def filter_high_quality(
        self,
        sources: List[Dict[str, Any]],
        scores: List[QualityScore],
        threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Filter sources to only high-quality ones.

        Args:
            sources: Original source list
            scores: Quality scores for each source
            threshold: Minimum quality threshold

        Returns:
            Filtered list of high-quality sources
        """
        return [
            source
            for source, score in zip(sources, scores)
            if score.is_high_quality(threshold)
        ]

    def prioritize_sources(
        self,
        sources: List[Dict[str, Any]],
        scores: List[QualityScore],
    ) -> List[Dict[str, Any]]:
        """
        Sort sources by quality score.

        Returns sources sorted by overall_quality descending.
        """
        pairs = list(zip(sources, scores))
        pairs.sort(key=lambda x: x[1].overall_quality, reverse=True)
        return [source for source, _ in pairs]

    def get_section_best_sources(
        self,
        sources: List[Dict[str, Any]],
        scores: List[QualityScore],
        section: str,
        max_sources: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get best sources for a specific section type.

        Prioritizes sources that have relevant data for the section.
        """
        # Score adjustments based on section
        section_weights = {
            "data_room": lambda s: s.has_financial_data * 0.3,
            "competitive_landscape": lambda s: s.has_competitive_info * 0.3,
            "market_intelligence": lambda s: s.has_market_data * 0.3,
            "strategic_context": lambda s: s.has_executive_info * 0.2 + s.has_recent_news * 0.2,
        }

        weight_fn = section_weights.get(section, lambda s: 0)

        # Calculate adjusted scores
        adjusted = [
            (source, score.overall_quality + weight_fn(score))
            for source, score in zip(sources, scores)
        ]

        # Sort by adjusted score
        adjusted.sort(key=lambda x: x[1], reverse=True)

        return [source for source, _ in adjusted[:max_sources]]


# Module-level instance
_scorer: Optional[AISourceQualityScorer] = None


def get_source_quality_scorer(
    company: str,
    industry: str,
    country: str = "Global",
) -> AISourceQualityScorer:
    """Get or create a source quality scorer."""
    global _scorer
    if _scorer is None or _scorer.company != company:
        _scorer = AISourceQualityScorer(
            company=company,
            industry=industry,
            country=country,
        )
    return _scorer


def reset_source_quality_scorer():
    """Reset the scorer (for new research session)."""
    global _scorer
    _scorer = None


__all__ = [
    "AISourceQualityScorer",
    "QualityScore",
    "CredibilityLevel",
    "BiasIndicator",
    "get_source_quality_scorer",
    "reset_source_quality_scorer",
]
