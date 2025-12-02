"""
Report Scorer - Multi-dimensional scoring system for research reports.

Scores reports across multiple quality dimensions:
- Completeness: Expected sections present
- Source Quality: Authoritative sources used
- Depth: Specific data vs generic content
- Actionability: Useful recommendations
- Freshness: Recent sources used
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..templates.report_schema import (
    ResearchReport,
    ContentQuality,
    ReportSection,
    create_report_from_drafts,
    detect_boilerplate,
)


# =============================================================================
# Score Configuration
# =============================================================================


class ScoreThreshold(Enum):
    """Score thresholds for quality levels."""
    EXCELLENT = 0.85
    GOOD = 0.70
    ADEQUATE = 0.55
    MINIMUM = 0.40


DIMENSION_WEIGHTS = {
    "completeness": 0.20,
    "source_quality": 0.20,
    "depth": 0.25,
    "actionability": 0.15,
    "freshness": 0.10,
    "consistency": 0.10,
}


# Required sections and their minimum word counts
SECTION_REQUIREMENTS = {
    ReportSection.CONTEXT: {"min_words": 300, "weight": 0.15},
    ReportSection.MARKET: {"min_words": 400, "weight": 0.25},
    ReportSection.COMPETITORS: {"min_words": 350, "weight": 0.20},
    ReportSection.FINANCIALS: {"min_words": 300, "weight": 0.20},
    ReportSection.SALES: {"min_words": 350, "weight": 0.20},
}


# =============================================================================
# Score Results
# =============================================================================


@dataclass
class DimensionScore:
    """Score for a single dimension."""
    dimension: str
    score: float
    weight: float
    weighted_score: float
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class SectionScore:
    """Score for a single section."""
    section: ReportSection
    score: float
    word_count: int
    has_data: bool
    has_citations: bool
    depth_indicators: List[str]
    issues: List[str] = field(default_factory=list)


@dataclass
class ReportScore:
    """Complete report scoring result."""
    overall_score: float
    quality_level: ContentQuality
    dimension_scores: Dict[str, DimensionScore]
    section_scores: Dict[ReportSection, SectionScore]
    passes_threshold: bool
    threshold: float
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    scored_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": round(self.overall_score, 2),
            "quality_level": self.quality_level.value,
            "passes_threshold": self.passes_threshold,
            "threshold": self.threshold,
            "dimensions": {
                name: {
                    "score": round(dim.score, 2),
                    "weighted_score": round(dim.weighted_score, 2),
                    "suggestions": dim.suggestions
                }
                for name, dim in self.dimension_scores.items()
            },
            "sections": {
                section.value: {
                    "score": round(score.score, 2),
                    "word_count": score.word_count,
                    "issues": score.issues
                }
                for section, score in self.section_scores.items()
            },
            "issues": self.issues,
            "suggestions": self.suggestions,
            "scored_at": self.scored_at.isoformat(),
        }


# =============================================================================
# Report Scorer
# =============================================================================


class ReportScorer:
    """
    Multi-dimensional report scoring system.

    Evaluates research reports across multiple quality dimensions
    and provides actionable feedback for improvement.
    """

    def __init__(
        self,
        threshold: float = 0.60,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize scorer.

        Args:
            threshold: Minimum score to pass quality check
            weights: Custom dimension weights (must sum to 1.0)
        """
        self.threshold = threshold
        self.weights = weights or DIMENSION_WEIGHTS

        # Validate weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    def score_report(
        self,
        report: ResearchReport,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> ReportScore:
        """
        Score a research report.

        Args:
            report: The research report to score
            sources: Optional list of sources used

        Returns:
            ReportScore with detailed breakdown
        """
        # Score each dimension
        dimension_scores = {}

        dimension_scores["completeness"] = self._score_completeness(report)
        dimension_scores["source_quality"] = self._score_source_quality(report, sources)
        dimension_scores["depth"] = self._score_depth(report)
        dimension_scores["actionability"] = self._score_actionability(report)
        dimension_scores["freshness"] = self._score_freshness(report, sources)
        dimension_scores["consistency"] = self._score_consistency(report)

        # Score each section
        section_scores = self._score_sections(report)

        # Calculate overall score
        overall_score = sum(d.weighted_score for d in dimension_scores.values())

        # Determine quality level
        if overall_score >= ScoreThreshold.EXCELLENT.value:
            quality_level = ContentQuality.EXCELLENT
        elif overall_score >= ScoreThreshold.GOOD.value:
            quality_level = ContentQuality.GOOD
        elif overall_score >= ScoreThreshold.ADEQUATE.value:
            quality_level = ContentQuality.ADEQUATE
        else:
            quality_level = ContentQuality.POOR

        # Collect all issues and suggestions
        all_issues = []
        all_suggestions = []

        for dim_score in dimension_scores.values():
            all_suggestions.extend(dim_score.suggestions)

        for sec_score in section_scores.values():
            all_issues.extend(sec_score.issues)

        return ReportScore(
            overall_score=overall_score,
            quality_level=quality_level,
            dimension_scores=dimension_scores,
            section_scores=section_scores,
            passes_threshold=overall_score >= self.threshold,
            threshold=self.threshold,
            issues=all_issues,
            suggestions=all_suggestions,
        )

    def score_from_drafts(
        self,
        company_name: str,
        drafts: Dict[str, str],
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> ReportScore:
        """
        Score a report from raw drafts.

        Args:
            company_name: Name of the company
            drafts: Dictionary of file_path -> content
            sources: Optional list of sources used

        Returns:
            ReportScore with detailed breakdown
        """
        report = create_report_from_drafts(company_name, drafts, sources)
        return self.score_report(report, sources)

    # =========================================================================
    # Dimension Scoring Methods
    # =========================================================================

    def _score_completeness(self, report: ResearchReport) -> DimensionScore:
        """Score completeness dimension."""
        weight = self.weights["completeness"]
        suggestions = []

        # Check required sections
        required = set(SECTION_REQUIREMENTS.keys())
        present = set(report.sections.keys())
        missing = required - present

        # Calculate score
        score = len(present.intersection(required)) / len(required)

        # Check section lengths
        for section_type, section in report.sections.items():
            if section_type in SECTION_REQUIREMENTS:
                min_words = SECTION_REQUIREMENTS[section_type]["min_words"]
                if section.content.word_count < min_words:
                    score -= 0.1
                    suggestions.append(
                        f"Expand {section_type.value} section "
                        f"(current: {section.content.word_count} words, minimum: {min_words})"
                    )

        score = max(0.0, min(1.0, score))

        if missing:
            suggestions.append(f"Add missing sections: {', '.join(s.value for s in missing)}")

        return DimensionScore(
            dimension="completeness",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details={"missing_sections": [s.value for s in missing]},
            suggestions=suggestions,
        )

    def _score_source_quality(
        self,
        report: ResearchReport,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> DimensionScore:
        """Score source quality dimension."""
        weight = self.weights["source_quality"]
        suggestions = []

        if not report.bibliography.sources and not sources:
            return DimensionScore(
                dimension="source_quality",
                score=0.3,  # Default for no sources
                weight=weight,
                weighted_score=0.3 * weight,
                suggestions=["Add source citations to improve credibility"],
            )

        # Use bibliography if available
        if report.bibliography.sources:
            avg_reliability = report.bibliography.avg_reliability
            primary_ratio = (
                report.bibliography.primary_sources / max(1, report.bibliography.total_sources)
            )

            score = (avg_reliability * 0.6) + (primary_ratio * 0.4)

            if primary_ratio < 0.2:
                suggestions.append("Include more primary sources (company filings, official announcements)")

            if avg_reliability < 0.7:
                suggestions.append("Use more authoritative sources (research firms, major publications)")

        else:
            score = 0.5

        return DimensionScore(
            dimension="source_quality",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details={
                "total_sources": report.bibliography.total_sources,
                "avg_reliability": report.bibliography.avg_reliability,
            },
            suggestions=suggestions,
        )

    def _score_depth(self, report: ResearchReport) -> DimensionScore:
        """Score depth dimension."""
        weight = self.weights["depth"]
        suggestions = []

        if not report.sections:
            return DimensionScore(
                dimension="depth",
                score=0.0,
                weight=weight,
                weighted_score=0.0,
                suggestions=["Add content to report sections"],
            )

        # Collect depth indicators across sections
        total_indicators = 0
        sections_with_data = 0
        sections_with_citations = 0

        for section in report.sections.values():
            section.content.analyze()
            total_indicators += len(section.content.depth_indicators)
            if section.content.has_data:
                sections_with_data += 1
            if section.content.has_citations:
                sections_with_citations += 1

        num_sections = len(report.sections)

        # Calculate score components
        indicator_score = min(1.0, total_indicators / (num_sections * 3))
        data_score = sections_with_data / num_sections
        citation_score = sections_with_citations / num_sections

        score = (indicator_score * 0.4) + (data_score * 0.35) + (citation_score * 0.25)

        if indicator_score < 0.5:
            suggestions.append("Add more specific data points (percentages, currency figures, growth rates)")

        if data_score < 0.6:
            suggestions.append("Include more numerical data in analysis")

        if citation_score < 0.4:
            suggestions.append("Add source citations to support claims")

        return DimensionScore(
            dimension="depth",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details={
                "total_indicators": total_indicators,
                "sections_with_data": sections_with_data,
                "sections_with_citations": sections_with_citations,
            },
            suggestions=suggestions,
        )

    def _score_actionability(self, report: ResearchReport) -> DimensionScore:
        """Score actionability dimension."""
        weight = self.weights["actionability"]
        suggestions = []

        # Focus on sales section
        sales_section = report.sections.get(ReportSection.SALES)

        if not sales_section:
            return DimensionScore(
                dimension="actionability",
                score=0.3,
                weight=weight,
                weighted_score=0.3 * weight,
                suggestions=["Add a sales strategy section with actionable recommendations"],
            )

        content = sales_section.content.content.lower()

        # Check for actionable elements
        action_indicators = [
            (r"recommend|suggestion|should|consider", 0.2),
            (r"opportunity|potential|target", 0.15),
            (r"approach|strategy|tactic", 0.15),
            (r"talking point|value proposition|pitch", 0.2),
            (r"decision maker|stakeholder|buyer", 0.15),
            (r"next step|follow.?up|action item", 0.15),
        ]

        score = 0.0
        missing_elements = []

        for pattern, points in action_indicators:
            if re.search(pattern, content):
                score += points
            else:
                missing_elements.append(pattern.replace("|", " or ").replace("\\", ""))

        score = min(1.0, score)

        if missing_elements and score < 0.8:
            suggestions.append(f"Consider adding: {', '.join(missing_elements[:3])}")

        if sales_section.content.word_count < 400:
            suggestions.append("Expand sales strategy section with more specific recommendations")

        return DimensionScore(
            dimension="actionability",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details={"word_count": sales_section.content.word_count},
            suggestions=suggestions,
        )

    def _score_freshness(
        self,
        report: ResearchReport,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> DimensionScore:
        """Score freshness dimension."""
        weight = self.weights["freshness"]
        suggestions = []

        # Check report generation date
        if report.metadata.generated_at:
            days_old = (datetime.utcnow() - report.metadata.generated_at).days
        else:
            days_old = 0

        # Base score on report age
        if days_old <= 7:
            score = 1.0
        elif days_old <= 30:
            score = 0.9
        elif days_old <= 90:
            score = 0.7
        elif days_old <= 180:
            score = 0.5
        else:
            score = 0.3
            suggestions.append("Report may contain outdated information - consider refreshing")

        # Check for year references in content
        current_year = datetime.utcnow().year
        all_content = " ".join(
            section.content.content for section in report.sections.values()
        )

        # Find year references
        years_mentioned = set(re.findall(r"\b(20\d{2})\b", all_content))
        years_mentioned = {int(y) for y in years_mentioned}

        if years_mentioned:
            latest_year = max(years_mentioned)
            if latest_year < current_year - 1:
                score *= 0.8
                suggestions.append(f"Data references are from {latest_year} - consider updating")

        return DimensionScore(
            dimension="freshness",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details={
                "report_age_days": days_old,
                "years_mentioned": sorted(years_mentioned) if years_mentioned else [],
            },
            suggestions=suggestions,
        )

    def _score_consistency(self, report: ResearchReport) -> DimensionScore:
        """Score consistency dimension."""
        weight = self.weights["consistency"]
        suggestions = []
        score = 1.0

        if not report.sections:
            return DimensionScore(
                dimension="consistency",
                score=0.5,
                weight=weight,
                weighted_score=0.5 * weight,
            )

        # Check for boilerplate
        all_content = " ".join(
            section.content.content for section in report.sections.values()
        )
        boilerplate = detect_boilerplate(all_content)
        if boilerplate:
            score -= len(boilerplate) * 0.1
            suggestions.append(f"Remove boilerplate content: {', '.join(boilerplate)}")

        # Check company name consistency
        company_name = report.company.name.lower()
        name_variations = set()

        for section in report.sections.values():
            content_lower = section.content.content.lower()
            # Find all potential company name mentions
            words = company_name.split()
            if words:
                if words[0] in content_lower:
                    name_variations.add(words[0])

        # Penalty for inconsistent naming (simplified check)
        # In a full implementation, this would use NER or more sophisticated matching

        # Check for placeholder text
        placeholders = re.findall(r"\[.+?\]", all_content)
        if placeholders:
            score -= min(0.3, len(placeholders) * 0.05)
            suggestions.append("Remove placeholder text")

        score = max(0.0, score)

        return DimensionScore(
            dimension="consistency",
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details={"boilerplate_detected": boilerplate},
            suggestions=suggestions,
        )

    def _score_sections(self, report: ResearchReport) -> Dict[ReportSection, SectionScore]:
        """Score individual sections."""
        section_scores = {}

        for section_type, section in report.sections.items():
            section.content.analyze()
            section.calculate_quality()

            issues = []
            requirements = SECTION_REQUIREMENTS.get(section_type, {})

            if requirements:
                min_words = requirements.get("min_words", 200)
                if section.content.word_count < min_words:
                    issues.append(f"Below minimum word count ({section.content.word_count}/{min_words})")

            if not section.content.has_data:
                issues.append("No numerical data found")

            section_scores[section_type] = SectionScore(
                section=section_type,
                score=section.quality_score,
                word_count=section.content.word_count,
                has_data=section.content.has_data,
                has_citations=section.content.has_citations,
                depth_indicators=section.content.depth_indicators,
                issues=issues,
            )

        return section_scores


# =============================================================================
# Utility Functions
# =============================================================================


def quick_score(drafts: Dict[str, str], company_name: str = "Company") -> Tuple[float, str]:
    """
    Quick scoring function for simple use cases.

    Args:
        drafts: Dictionary of file_path -> content
        company_name: Company name

    Returns:
        Tuple of (score, quality_level)
    """
    scorer = ReportScorer()
    result = scorer.score_from_drafts(company_name, drafts)
    return result.overall_score, result.quality_level.value


def get_improvement_suggestions(
    drafts: Dict[str, str],
    company_name: str = "Company",
    max_suggestions: int = 5
) -> List[str]:
    """
    Get improvement suggestions for a report.

    Args:
        drafts: Dictionary of file_path -> content
        company_name: Company name
        max_suggestions: Maximum suggestions to return

    Returns:
        List of improvement suggestions
    """
    scorer = ReportScorer()
    result = scorer.score_from_drafts(company_name, drafts)

    # Sort by weighted score (lowest first) to prioritize improvements
    sorted_dims = sorted(
        result.dimension_scores.values(),
        key=lambda d: d.weighted_score
    )

    suggestions = []
    for dim in sorted_dims:
        suggestions.extend(dim.suggestions)
        if len(suggestions) >= max_suggestions:
            break

    return suggestions[:max_suggestions]
