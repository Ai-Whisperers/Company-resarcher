"""
Report schemas - Pydantic models for research report validation.
"""

from .report_schema import (
    ReportSection,
    ContentQuality,
    SourceType,
    SourceReference,
    Bibliography,
    SectionContent,
    ReportSectionModel,
    CompanyInfo,
    ResearchMetadata,
    QualityMetrics,
    ResearchReport,
    create_section_from_content,
    create_report_from_drafts,
    validate_report_structure,
    detect_boilerplate,
)

__all__ = [
    "ReportSection",
    "ContentQuality",
    "SourceType",
    "SourceReference",
    "Bibliography",
    "SectionContent",
    "ReportSectionModel",
    "CompanyInfo",
    "ResearchMetadata",
    "QualityMetrics",
    "ResearchReport",
    "create_section_from_content",
    "create_report_from_drafts",
    "validate_report_structure",
    "detect_boilerplate",
]
