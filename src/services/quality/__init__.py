"""
Quality assessment services.

Provides:
- SourceQualityAssessor: Overall quality assessment
- SourceQualityScore: Source quality scoring result
- FactVerifier: Fact verification
- ContradictionDetector: Contradiction detection
- ReportScorer: Report quality scoring
- GroundingService: Content grounding
"""

from .assessor import SourceQualityAssessor, get_quality_assessor
from .source_quality_scorer import (
    SourceQualityScore,
    RecencyCategory,
    RecencyInfo,
    get_recency_category,
    get_recency_description,
    get_domain_authority_score,
)
from .fact_verifier import FactVerifier, VerificationResult
from .contradiction_detector import ContradictionDetector, Contradiction
from .report_scorer import ReportScorer, ReportScore, SectionScore, DimensionScore, get_improvement_suggestions
from .grounding_service import GroundingService, GroundedClaim

__all__ = [
    # Classes
    "SourceQualityAssessor",
    "SourceQualityScore",
    "RecencyCategory",
    "RecencyInfo",
    "FactVerifier",
    "VerificationResult",
    "ContradictionDetector",
    "Contradiction",
    "ReportScorer",
    "ReportScore",
    "SectionScore",
    "DimensionScore",
    "GroundingService",
    "GroundedClaim",
    # Functions
    "get_quality_assessor",
    "get_recency_category",
    "get_recency_description",
    "get_domain_authority_score",
    "get_improvement_suggestions",
]
