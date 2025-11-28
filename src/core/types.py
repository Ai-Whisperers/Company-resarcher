from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field, HttpUrl, field_validator


# =============================================================================
# TypedDict definitions for common data structures (Issue #053)
# These provide type hints for Dict[str, Any] in key areas
# =============================================================================


class SWOTAnalysis(TypedDict, total=False):
    """SWOT analysis structure from insight generator."""
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]


class StrategicInsightsDict(TypedDict, total=False):
    """Strategic insights response from insight generator."""
    swot: SWOTAnalysis
    strategic_takeaways: List[str]
    executive_summary: str


class SearchResultDict(TypedDict, total=False):
    """Structure for search results from Tavily or local search."""
    url: str
    title: str
    content: str
    score: float


class TechStackDict(TypedDict, total=False):
    """Technology stack analysis data."""
    technologies: List[str]
    frameworks: List[str]
    analytics: List[str]
    hosting: List[str]


class CriticFeedbackDict(TypedDict, total=False):
    """Critic agent feedback structure."""
    score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    approved: bool


# =============================================================================
# Pydantic Response Models for JSON Validation (Issue #070)
# These validate LLM responses against expected schemas
# =============================================================================


class SWOTAnalysisModel(BaseModel):
    """Validated SWOT analysis from LLM."""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class StrategicInsightsResponse(BaseModel):
    """Validated strategic insights response from insight generator."""
    swot: SWOTAnalysisModel = Field(default_factory=SWOTAnalysisModel)
    strategic_takeaways: List[str] = Field(default_factory=list)
    executive_summary: str = Field(default="N/A")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategicInsightsResponse":
        """Create from potentially malformed dict with defaults."""
        return cls(
            swot=SWOTAnalysisModel(**data.get("swot", {})),
            strategic_takeaways=data.get("strategic_takeaways", []),
            executive_summary=data.get("executive_summary", "N/A"),
        )


class CriticFeedbackResponse(BaseModel):
    """Validated critic feedback response."""
    score: float = Field(default=0.0, ge=0.0, le=10.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    approved: bool = Field(default=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticFeedbackResponse":
        """Create from potentially malformed dict with defaults."""
        return cls(
            score=data.get("score", 0.0),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
            approved=data.get("approved", False),
        )


# =============================================================================
# Original Pydantic Models
# =============================================================================


class ResearchSource(BaseModel):
    """Represents a single source of information (webpage, PDF, etc.)"""

    url: str
    title: str
    content: str
    source_type: str = "web"  # web, pdf, news, etc.
    category: Optional[str] = None  # news, financial, etc.
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional data

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        allowed = {"web", "pdf", "news", "financial", "social", "api"}
        if v not in allowed:
            raise ValueError(f"source_type must be one of: {allowed}")
        return v


class CompanyProfile(BaseModel):
    """Basic input information about a company"""

    name: str = Field(..., min_length=1, max_length=500)
    website: Optional[str] = Field(default=None, max_length=2000)
    industry: Optional[str] = Field(default=None, max_length=200)
    country: str = Field(default="Global", max_length=100)
    description: Optional[str] = Field(default=None, max_length=5000)
    target_audience: Optional[str] = Field(default=None, max_length=1000)
    competitors: List[str] = Field(default_factory=list, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty or whitespace")
        return v

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not (v.startswith("http://") or v.startswith("https://")):
            v = f"https://{v}"
        return v

    @field_validator("competitors")
    @classmethod
    def validate_competitors(cls, v: List[str]) -> List[str]:
        return [c.strip() for c in v if c and c.strip()]


class ResearchContext(BaseModel):
    """
    Aggregated research data from specialist agents for insight generation.

    .. deprecated::
        Use TypedResearchContext from src.core.models instead for type safety.
        This class is maintained for backward compatibility.
    """

    financial_data: Dict[str, Any] = Field(default_factory=dict)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    competitor_data: Dict[str, Any] = Field(default_factory=dict)
    brand_data: Dict[str, Any] = Field(default_factory=dict)


class ResearchPhaseResult(BaseModel):
    """Result of a specific research phase (e.g., Market Analysis)"""

    phase_name: str
    markdown_content: str
    sources: List[ResearchSource]
    key_findings: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class FullCompanyResearch(BaseModel):
    """The complete research dossier for a company"""

    company: CompanyProfile
    phases: Dict[str, ResearchPhaseResult] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    output_path: str
