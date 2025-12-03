"""
Quality Thresholds - FE-007: Dynamic output structure based on data quality.

Defines thresholds for determining when to generate reports based on
data quality and completeness.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class QualityThresholds:
    """
    Quality thresholds for report generation.

    A report is only generated when all applicable thresholds are met.
    """
    min_sources: int = 2              # Minimum sources to generate report
    min_content_length: int = 500     # Minimum characters of useful content
    min_confidence: float = 0.6       # Minimum AI confidence score
    required_fields_pct: float = 0.5  # % of template fields that must be filled
    min_quality_score: float = 0.35   # Minimum overall quality score


# Default thresholds (can be overridden via environment)
DEFAULT_THRESHOLDS = QualityThresholds(
    min_sources=int(os.getenv("REPORT_MIN_SOURCES", "2")),
    min_content_length=int(os.getenv("REPORT_MIN_CONTENT_LENGTH", "500")),
    min_confidence=float(os.getenv("REPORT_MIN_CONFIDENCE", "0.6")),
    required_fields_pct=float(os.getenv("REPORT_REQUIRED_FIELDS_PCT", "0.5")),
    min_quality_score=float(os.getenv("REPORT_MIN_QUALITY_SCORE", "0.35")),
)


@dataclass
class PhaseResult:
    """Result from a research phase."""
    name: str
    sources: list
    content: str
    confidence: float
    quality_score: float
    filled_fields: int = 0
    total_fields: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def should_generate_report(
    phase_result: PhaseResult,
    thresholds: Optional[QualityThresholds] = None,
) -> bool:
    """
    Determine if a phase has enough quality data to generate a report.

    Args:
        phase_result: Result from a research phase
        thresholds: Quality thresholds (uses defaults if not provided)

    Returns:
        True if report should be generated
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS

    # Check minimum sources
    if len(phase_result.sources) < thresholds.min_sources:
        return False

    # Check minimum content length
    if len(phase_result.content) < thresholds.min_content_length:
        return False

    # Check confidence score
    if phase_result.confidence < thresholds.min_confidence:
        return False

    # Check quality score
    if phase_result.quality_score < thresholds.min_quality_score:
        return False

    # Check filled fields percentage (if tracked)
    if phase_result.total_fields > 0:
        filled_pct = phase_result.filled_fields / phase_result.total_fields
        if filled_pct < thresholds.required_fields_pct:
            return False

    return True


def get_skip_reason(
    phase_result: PhaseResult,
    thresholds: Optional[QualityThresholds] = None,
) -> str:
    """
    Get human-readable reason why report was not generated.

    Args:
        phase_result: Result from a research phase
        thresholds: Quality thresholds (uses defaults if not provided)

    Returns:
        Skip reason string
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS

    if len(phase_result.sources) < thresholds.min_sources:
        return f"Insufficient sources ({len(phase_result.sources)}/{thresholds.min_sources})"

    if len(phase_result.content) < thresholds.min_content_length:
        return f"Insufficient content ({len(phase_result.content)}/{thresholds.min_content_length} chars)"

    if phase_result.confidence < thresholds.min_confidence:
        return f"Low confidence ({phase_result.confidence:.1%}/{thresholds.min_confidence:.1%})"

    if phase_result.quality_score < thresholds.min_quality_score:
        return f"Low quality score ({phase_result.quality_score:.2f}/{thresholds.min_quality_score:.2f})"

    if phase_result.total_fields > 0:
        filled_pct = phase_result.filled_fields / phase_result.total_fields
        if filled_pct < thresholds.required_fields_pct:
            return f"Too many missing fields ({filled_pct:.1%}/{thresholds.required_fields_pct:.1%})"

    return "Unknown"


def calculate_data_quality_score(phase_result: PhaseResult) -> Dict[str, float]:
    """
    Calculate detailed data quality breakdown for a phase.

    Returns dict with:
    - source_diversity: Score based on source variety
    - content_depth: Score based on content richness
    - data_recency: Score based on data freshness
    - coverage: Score based on field coverage
    - overall: Weighted average
    """
    scores = {}

    # Source diversity (0-25)
    source_count = len(phase_result.sources)
    if source_count >= 5:
        scores["source_diversity"] = 25.0
    elif source_count >= 3:
        scores["source_diversity"] = 20.0
    elif source_count >= 2:
        scores["source_diversity"] = 15.0
    elif source_count >= 1:
        scores["source_diversity"] = 10.0
    else:
        scores["source_diversity"] = 0.0

    # Content depth (0-25)
    content_len = len(phase_result.content)
    if content_len >= 5000:
        scores["content_depth"] = 25.0
    elif content_len >= 2000:
        scores["content_depth"] = 20.0
    elif content_len >= 1000:
        scores["content_depth"] = 15.0
    elif content_len >= 500:
        scores["content_depth"] = 10.0
    else:
        scores["content_depth"] = 5.0

    # Data recency (0-25) - placeholder, would check source dates
    scores["data_recency"] = phase_result.quality_score * 25

    # Coverage (0-25)
    if phase_result.total_fields > 0:
        coverage_pct = phase_result.filled_fields / phase_result.total_fields
        scores["coverage"] = coverage_pct * 25
    else:
        scores["coverage"] = phase_result.confidence * 25

    # Overall (0-100)
    scores["overall"] = sum(scores.values())

    return scores
