"""
Report Schema - Pydantic models for research report validation.

Defines the expected structure and validation rules for research reports:
- Section models
- Content validation
- Quality indicators
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
import re


# =============================================================================
# Enums
# =============================================================================


class ReportSection(str, Enum):
    """Valid report sections."""
    CONTEXT = "context"
    MARKET = "market"
    COMPETITORS = "competitors"
    FINANCIALS = "financials"
    SALES = "sales"
    BRAND = "brand"
    APPENDIX = "appendix"


class ContentQuality(str, Enum):
    """Content quality levels."""
    EXCELLENT = "excellent"  # Score >= 0.85
    GOOD = "good"           # Score >= 0.70
    ADEQUATE = "adequate"   # Score >= 0.55
    POOR = "poor"           # Score < 0.55


class SourceType(str, Enum):
    """Types of sources."""
    PRIMARY = "primary"      # Company website, SEC filings
    SECONDARY = "secondary"  # News articles, analyst reports
    TERTIARY = "tertiary"    # Wikipedia, aggregators


# =============================================================================
# Source Models
# =============================================================================


class SourceReference(BaseModel):
    """A source reference in the report."""
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Source title")
    accessed_at: Optional[datetime] = Field(None, description="When source was accessed")
    source_type: SourceType = Field(SourceType.SECONDARY, description="Type of source")
    reliability_score: float = Field(0.5, ge=0.0, le=1.0, description="Source reliability")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class Bibliography(BaseModel):
    """Bibliography section of the report."""
    sources: List[SourceReference] = Field(default_factory=list)
    total_sources: int = Field(0, ge=0)
    primary_sources: int = Field(0, ge=0)
    avg_reliability: float = Field(0.0, ge=0.0, le=1.0)

    def calculate_stats(self) -> None:
        """Calculate bibliography statistics."""
        self.total_sources = len(self.sources)
        self.primary_sources = sum(
            1 for s in self.sources if s.source_type == SourceType.PRIMARY
        )
        if self.sources:
            self.avg_reliability = sum(s.reliability_score for s in self.sources) / len(self.sources)


# =============================================================================
# Content Models
# =============================================================================


class SectionContent(BaseModel):
    """Content of a report section."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=100)
    word_count: int = Field(0, ge=0)
    has_data: bool = Field(False, description="Contains numerical data")
    has_citations: bool = Field(False, description="Contains source citations")
    depth_indicators: List[str] = Field(default_factory=list)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate and analyze content."""
        if len(v.strip()) < 100:
            raise ValueError("Content must be at least 100 characters")
        return v

    def analyze(self) -> None:
        """Analyze content for quality indicators."""
        self.word_count = len(self.content.split())

        # Check for numerical data
        number_pattern = re.compile(r"\$?\d+[\d,]*(\.\d+)?[%MB]?")
        self.has_data = bool(number_pattern.search(self.content))

        # Check for citations
        citation_patterns = [r"\[\d+\]", r"\(Source:", r"according to"]
        self.has_citations = any(
            re.search(p, self.content, re.IGNORECASE) for p in citation_patterns
        )

        # Identify depth indicators
        indicators = []
        if re.search(r"\$\d+", self.content):
            indicators.append("currency_figures")
        if re.search(r"\d+\.?\d*%", self.content):
            indicators.append("percentages")
        if re.search(r"CAGR|YoY|QoQ", self.content):
            indicators.append("growth_metrics")
        if re.search(r"\d{4}", self.content):
            indicators.append("year_references")
        self.depth_indicators = indicators


class ReportSectionModel(BaseModel):
    """A complete report section."""
    section_type: ReportSection
    file_path: str = Field(..., description="Relative file path")
    content: SectionContent
    quality_score: float = Field(0.0, ge=0.0, le=1.0)
    quality_level: ContentQuality = Field(ContentQuality.ADEQUATE)
    warnings: List[str] = Field(default_factory=list)

    def calculate_quality(self) -> None:
        """Calculate section quality score."""
        score = 0.0

        # Word count scoring (up to 0.3)
        if self.content.word_count >= 500:
            score += 0.3
        elif self.content.word_count >= 300:
            score += 0.2
        elif self.content.word_count >= 150:
            score += 0.1

        # Data presence scoring (up to 0.25)
        if self.content.has_data:
            score += 0.25

        # Citation scoring (up to 0.2)
        if self.content.has_citations:
            score += 0.2

        # Depth indicators scoring (up to 0.25)
        indicator_count = len(self.content.depth_indicators)
        score += min(0.25, indicator_count * 0.0625)

        self.quality_score = min(1.0, score)

        # Set quality level
        if self.quality_score >= 0.85:
            self.quality_level = ContentQuality.EXCELLENT
        elif self.quality_score >= 0.70:
            self.quality_level = ContentQuality.GOOD
        elif self.quality_score >= 0.55:
            self.quality_level = ContentQuality.ADEQUATE
        else:
            self.quality_level = ContentQuality.POOR

        # Generate warnings
        self._generate_warnings()

    def _generate_warnings(self) -> None:
        """Generate quality warnings."""
        warnings = []

        if self.content.word_count < 200:
            warnings.append("Content is brief - consider adding more detail")

        if not self.content.has_data:
            warnings.append("No numerical data found - consider adding specific figures")

        if not self.content.has_citations:
            warnings.append("No source citations found - consider adding references")

        if len(self.content.depth_indicators) < 2:
            warnings.append("Limited depth indicators - consider adding more specific data")

        self.warnings = warnings


# =============================================================================
# Report Models
# =============================================================================


class CompanyInfo(BaseModel):
    """Basic company information."""
    name: str = Field(..., min_length=1, max_length=200)
    website: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)
    country: str = Field("USA", max_length=100)
    founded: Optional[int] = Field(None, ge=1800, le=2100)
    employees: Optional[int] = Field(None, ge=0)


class ResearchMetadata(BaseModel):
    """Metadata about the research."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_seconds: Optional[float] = None
    model_used: Optional[str] = None
    version: str = Field("1.0.0")
    sources_used: int = Field(0, ge=0)


class QualityMetrics(BaseModel):
    """Overall quality metrics for the report."""
    completeness: float = Field(0.0, ge=0.0, le=1.0, description="Section coverage")
    source_quality: float = Field(0.0, ge=0.0, le=1.0, description="Source reliability")
    depth: float = Field(0.0, ge=0.0, le=1.0, description="Analysis depth")
    actionability: float = Field(0.0, ge=0.0, le=1.0, description="Recommendation quality")
    freshness: float = Field(0.0, ge=0.0, le=1.0, description="Data recency")
    overall_score: float = Field(0.0, ge=0.0, le=1.0)
    quality_level: ContentQuality = Field(ContentQuality.ADEQUATE)

    def calculate_overall(self) -> None:
        """Calculate overall score from components."""
        self.overall_score = (
            self.completeness * 0.25 +
            self.source_quality * 0.20 +
            self.depth * 0.25 +
            self.actionability * 0.15 +
            self.freshness * 0.15
        )

        if self.overall_score >= 0.85:
            self.quality_level = ContentQuality.EXCELLENT
        elif self.overall_score >= 0.70:
            self.quality_level = ContentQuality.GOOD
        elif self.overall_score >= 0.55:
            self.quality_level = ContentQuality.ADEQUATE
        else:
            self.quality_level = ContentQuality.POOR


class ResearchReport(BaseModel):
    """Complete research report model."""
    company: CompanyInfo
    metadata: ResearchMetadata = Field(default_factory=ResearchMetadata)
    sections: Dict[ReportSection, ReportSectionModel] = Field(default_factory=dict)
    bibliography: Bibliography = Field(default_factory=Bibliography)
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    warnings: List[str] = Field(default_factory=list)
    is_valid: bool = Field(True)

    def validate_completeness(self) -> float:
        """Check if all required sections are present."""
        required_sections = {
            ReportSection.CONTEXT,
            ReportSection.MARKET,
            ReportSection.COMPETITORS,
            ReportSection.FINANCIALS,
            ReportSection.SALES
        }

        present = set(self.sections.keys())
        missing = required_sections - present

        if missing:
            self.warnings.append(f"Missing sections: {', '.join(s.value for s in missing)}")

        return len(present.intersection(required_sections)) / len(required_sections)

    def calculate_quality_metrics(self) -> None:
        """Calculate all quality metrics."""
        # Completeness
        self.quality.completeness = self.validate_completeness()

        # Source quality
        self.bibliography.calculate_stats()
        self.quality.source_quality = self.bibliography.avg_reliability

        # Depth (average section depth)
        if self.sections:
            depth_scores = []
            for section in self.sections.values():
                section.content.analyze()
                section.calculate_quality()
                depth_scores.append(section.quality_score)
            self.quality.depth = sum(depth_scores) / len(depth_scores)

        # Actionability (check sales section)
        sales_section = self.sections.get(ReportSection.SALES)
        if sales_section and sales_section.quality_score >= 0.7:
            self.quality.actionability = sales_section.quality_score
        else:
            self.quality.actionability = 0.4

        # Freshness (based on metadata)
        if self.metadata.generated_at:
            days_old = (datetime.utcnow() - self.metadata.generated_at).days
            self.quality.freshness = max(0.0, 1.0 - (days_old / 30))
        else:
            self.quality.freshness = 0.5

        self.quality.calculate_overall()

        # Collect section warnings
        for section in self.sections.values():
            for warning in section.warnings:
                self.warnings.append(f"[{section.section_type.value}] {warning}")

    def passes_threshold(self, threshold: float = 0.60) -> bool:
        """Check if report passes quality threshold."""
        return self.quality.overall_score >= threshold


# =============================================================================
# Factory Functions
# =============================================================================


def create_section_from_content(
    section_type: ReportSection,
    file_path: str,
    title: str,
    content: str
) -> ReportSectionModel:
    """Create a report section from raw content."""
    section_content = SectionContent(title=title, content=content)
    section_content.analyze()

    section = ReportSectionModel(
        section_type=section_type,
        file_path=file_path,
        content=section_content
    )
    section.calculate_quality()

    return section


def create_report_from_drafts(
    company_name: str,
    drafts: Dict[str, str],
    sources: Optional[List[Dict[str, Any]]] = None
) -> ResearchReport:
    """Create a research report from draft content."""
    # Map file paths to sections
    section_mapping = {
        "context": ReportSection.CONTEXT,
        "overview": ReportSection.CONTEXT,
        "market": ReportSection.MARKET,
        "competitor": ReportSection.COMPETITORS,
        "financial": ReportSection.FINANCIALS,
        "sales": ReportSection.SALES,
        "brand": ReportSection.BRAND,
    }

    company = CompanyInfo(name=company_name)
    report = ResearchReport(company=company)

    # Process drafts
    for file_path, content in drafts.items():
        # Determine section type from path
        path_lower = file_path.lower()
        section_type = None

        for keyword, sec_type in section_mapping.items():
            if keyword in path_lower:
                section_type = sec_type
                break

        if section_type and section_type not in report.sections:
            # Extract title from content
            lines = content.strip().split("\n")
            title = lines[0].lstrip("#").strip() if lines else "Untitled"

            try:
                section = create_section_from_content(
                    section_type=section_type,
                    file_path=file_path,
                    title=title,
                    content=content
                )
                report.sections[section_type] = section
            except Exception:
                # Skip invalid sections
                pass

    # Process sources
    if sources:
        for source_data in sources:
            try:
                source = SourceReference(
                    url=source_data.get("url", ""),
                    title=source_data.get("title", "Unknown"),
                    reliability_score=source_data.get("reliability_score", 0.5)
                )
                report.bibliography.sources.append(source)
            except Exception:
                pass

    # Calculate quality
    report.calculate_quality_metrics()

    return report


# =============================================================================
# Validation Functions
# =============================================================================


def validate_report_structure(drafts: Dict[str, str]) -> List[str]:
    """Validate report structure and return list of issues."""
    issues = []

    required_patterns = [
        ("context", ["overview", "context"]),
        ("market", ["market"]),
        ("competitors", ["competitor"]),
        ("financials", ["financial"]),
        ("sales", ["sales"]),
    ]

    for section_name, patterns in required_patterns:
        found = any(
            any(p in path.lower() for p in patterns)
            for path in drafts.keys()
        )
        if not found:
            issues.append(f"Missing section: {section_name}")

    return issues


def detect_boilerplate(content: str) -> List[str]:
    """Detect boilerplate text in content."""
    boilerplate_patterns = [
        (r"Lorem ipsum", "Lorem ipsum placeholder text"),
        (r"\[INSERT .+?\]", "Placeholder text"),
        (r"\[TODO\]", "TODO marker"),
        (r"As an AI", "AI disclosure"),
        (r"I cannot provide", "AI limitation statement"),
        (r"based on my training", "AI training reference"),
    ]

    detected = []
    for pattern, description in boilerplate_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            detected.append(description)

    return detected
