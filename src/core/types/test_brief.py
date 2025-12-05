"""
Research Intelligence Brief - AI-generated research planning document.

This module defines the data model for the AI-first research planning approach.
The ResearchIntelligenceBrief is generated BEFORE any web scraping to guide:
- Query generation (more targeted queries)
- Source filtering (knowing what's relevant)
- Content prioritization (knowing what matters)
- Gap analysis (knowing what's missing)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Priority Query Model
# =============================================================================


class PriorityQuery(BaseModel):
    """A search query with priority and rationale."""

    query: str = Field(..., description="The search query text")
    priority: int = Field(default=1, ge=1, le=5, description="Priority 1-5 (1=highest)")
    rationale: str = Field(default="", description="Why this query is important")
    language: str = Field(default="en", description="Language code for the query")
    target_sources: List[str] = Field(
        default_factory=list, description="Specific domains or source types to target"
    )


class EntityIdentifier(BaseModel):
    """Key identifiers to disambiguate the target company."""

    identifier_type: str = Field(
        ..., description="Type: headquarters, founding_year, industry, etc."
    )
    value: str = Field(..., description="The identifier value")
    confidence: str = Field(default="medium", description="high/medium/low confidence")


class ExclusionPattern(BaseModel):
    """Pattern to identify wrong entities to exclude."""

    pattern: str = Field(..., description="Text pattern or entity name to exclude")
    reason: str = Field(default="", description="Why this should be excluded")


class AlternativeSource(BaseModel):
    """Fallback strategy for hard-to-find information."""

    information_type: str = Field(..., description="What information is needed")
    primary_sources: List[str] = Field(
        default_factory=list, description="Primary sources to try"
    )
    fallback_strategy: str = Field(
        default="", description="What to do if primary fails"
    )


class ResearchGap(BaseModel):
    """Predicted gap in available information."""

    topic: str = Field(..., description="What information is likely missing")
    importance: str = Field(default="medium", description="high/medium/low importance")
    mitigation: str = Field(default="", description="How to work around this gap")


# =============================================================================
# Company Hypothesis Model
# =============================================================================


class CompanyHypothesis(BaseModel):
    """AI's hypothesis about what the company is and does."""

    business_description: str = Field(
        default="", description="What the company does based on name/URL/industry"
    )
    company_type: str = Field(
        default="private", description="public/private/government/subsidiary/nonprofit"
    )
    ownership_hypothesis: str = Field(
        default="", description="Likely parent company or ownership structure"
    )
    key_products_services: List[str] = Field(
        default_factory=list, description="Likely main products or services"
    )
    target_markets: List[str] = Field(
        default_factory=list, description="Likely target customer segments"
    )
    geographic_focus: str = Field(default="", description="Primary geographic markets")
    industry_position: str = Field(
        default="", description="Likely market position (leader/challenger/niche/etc.)"
    )
    notable_characteristics: List[str] = Field(
        default_factory=list,
        description="Key characteristics that make this company unique",
    )


# =============================================================================
# Research Intelligence Brief - Main Model
# =============================================================================


class ResearchIntelligenceBrief(BaseModel):
    """
    AI-generated research planning document.

    This brief is created BEFORE any web scraping to guide the entire
    research process with company-specific intelligence.

    Usage:
        1. AI generates this brief from company name/URL/industry
        2. QueryGenerationStage uses priority_queries for targeted search
        3. ComprehensiveFilter uses entity_identifiers and exclusion_patterns
        4. AnalysisStage uses predicted_gaps for gap-aware synthesis
    """

    # === Company Understanding ===
    company_hypothesis: CompanyHypothesis = Field(
        default_factory=CompanyHypothesis,
        description="AI's hypothesis about what this company is",
    )

    # === Search Intelligence ===
    priority_queries: Dict[str, List[PriorityQuery]] = Field(
        default_factory=dict,
        description="Priority queries by research type (market, financial, etc.)",
    )
    target_domains: List[str] = Field(
        default_factory=list,
        description="High-value domains to prioritize in search results",
    )
    language_hints: List[str] = Field(
        default_factory=list,
        description="Languages to search in (e.g., ['es', 'en'] for Paraguay)",
    )

    # === Filtering Intelligence ===
    entity_identifiers: List[EntityIdentifier] = Field(
        default_factory=list,
        description="Key identifiers that must match for entity validation",
    )
    exclusion_patterns: List[ExclusionPattern] = Field(
        default_factory=list,
        description="Patterns indicating wrong entity (to filter out)",
    )
    relevance_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that strongly indicate relevant content",
    )
    irrelevance_keywords: List[str] = Field(
        default_factory=list, description="Keywords that indicate irrelevant content"
    )
    recency_importance: str = Field(
        default="medium", description="How important is data recency: high/medium/low"
    )
    min_date_preference: Optional[str] = Field(
        default=None, description="Prefer sources after this date (YYYY-MM-DD)"
    )

    # === Gap Awareness ===
    predicted_gaps: List[ResearchGap] = Field(
        default_factory=list, description="Information that will likely be hard to find"
    )
    alternative_sources: List[AlternativeSource] = Field(
        default_factory=list, description="Fallback strategies for missing information"
    )

    # === Research Focus ===
    key_questions: List[str] = Field(
        default_factory=list,
        description="Most important questions to answer about this company",
    )
    research_priorities: Dict[str, int] = Field(
        default_factory=dict,
        description="Priority ranking for research types (1=highest)",
    )

    # === Metadata ===
    confidence_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="AI's confidence in this brief (0-1)"
    )
    reasoning: str = Field(
        default="", description="AI's reasoning for the hypotheses and priorities"
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchIntelligenceBrief":
        """Create from potentially incomplete dict with defaults."""
        # Handle nested models
        if "company_hypothesis" in data and isinstance(
            data["company_hypothesis"], dict
        ):
            data["company_hypothesis"] = CompanyHypothesis(**data["company_hypothesis"])

        # Handle priority queries
        if "priority_queries" in data:
            for key, queries in data["priority_queries"].items():
                data["priority_queries"][key] = [
                    PriorityQuery(**q) if isinstance(q, dict) else q for q in queries
                ]

        # Handle entity identifiers
        if "entity_identifiers" in data:
            data["entity_identifiers"] = [
                EntityIdentifier(**e) if isinstance(e, dict) else e
                for e in data["entity_identifiers"]
            ]

        # Handle exclusion patterns
        if "exclusion_patterns" in data:
            data["exclusion_patterns"] = [
                ExclusionPattern(**e) if isinstance(e, dict) else e
                for e in data["exclusion_patterns"]
            ]

        # Handle predicted gaps
        if "predicted_gaps" in data:
            data["predicted_gaps"] = [
                ResearchGap(**g) if isinstance(g, dict) else g
                for g in data["predicted_gaps"]
            ]

        # Handle alternative sources
        if "alternative_sources" in data:
            data["alternative_sources"] = [
                AlternativeSource(**s) if isinstance(s, dict) else s
                for s in data["alternative_sources"]
            ]

        return cls(**data)

    def get_queries_for_type(self, research_type: str) -> List[PriorityQuery]:
        """Get priority queries for a specific research type."""
        return self.priority_queries.get(research_type, [])

    def get_query_strings_for_type(self, research_type: str) -> List[str]:
        """Get just the query strings for a research type, sorted by priority."""
        queries = self.get_queries_for_type(research_type)
        sorted_queries = sorted(queries, key=lambda q: q.priority)
        return [q.query for q in sorted_queries]

    def should_exclude_source(self, title: str, url: str, content: str = "") -> bool:
        """Check if a source should be excluded based on exclusion patterns."""
        text = f"{title} {url} {content[:500]}".lower()

        for pattern in self.exclusion_patterns:
            if pattern.pattern.lower() in text:
                return True

        return False

    def calculate_relevance_score(self, title: str, content: str) -> float:
        """Calculate relevance score based on keyword presence."""
        text = f"{title} {content}".lower()

        # Count relevance keywords
        relevance_count = sum(1 for kw in self.relevance_keywords if kw.lower() in text)

        # Count irrelevance keywords
        irrelevance_count = sum(
            1 for kw in self.irrelevance_keywords if kw.lower() in text
        )

        # Calculate score (0-1)
        if relevance_count == 0 and irrelevance_count == 0:
            return 0.5  # Neutral

        total = relevance_count + irrelevance_count
        return relevance_count / total if total > 0 else 0.5

    def is_entity_match(self, content: str) -> bool:
        """Check if content matches expected entity identifiers."""
        if not self.entity_identifiers:
            return True  # No identifiers to check

        content_lower = content.lower()

        # Count how many high-confidence identifiers match
        high_conf_matches = 0
        high_conf_total = 0

        for identifier in self.entity_identifiers:
            if identifier.confidence == "high":
                high_conf_total += 1
                if identifier.value.lower() in content_lower:
                    high_conf_matches += 1

        # Require at least one high-confidence match if we have high-confidence identifiers
        if high_conf_total > 0:
            return high_conf_matches > 0

        # For medium/low confidence, be more lenient
        return True


# =============================================================================
# Empty Brief Factory
# =============================================================================


def create_empty_brief() -> ResearchIntelligenceBrief:
    """Create an empty brief for cases where AI planning fails."""
    return ResearchIntelligenceBrief(
        confidence_score=0.0,
        reasoning="Empty brief - AI planning was not performed or failed",
    )
