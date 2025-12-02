"""
SQLAlchemy models for Company Researcher database schema.

This module defines the relational database schema for persisting
research data to PostgreSQL, including:
- Companies: Target companies being researched
- ResearchRuns: Individual research sessions
- Sources: Web sources and documents used in research
- Insights: Key findings and analysis results

Usage:
    from src.data.models import Base, Company, ResearchRun, Source, Insight

    # Create tables
    Base.metadata.create_all(engine)

    # Create a company
    company = Company(name="Acme Corp", website="https://acme.com")
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# =============================================================================
# Enums
# =============================================================================


class ResearchRunStatus(str, PyEnum):
    """Status of a research run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InsightCategory(str, PyEnum):
    """Categories of research insights."""
    FINANCIAL = "financial"
    MARKET = "market"
    COMPETITIVE = "competitive"
    BRAND = "brand"
    SALES = "sales"
    TECHNOLOGY = "technology"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    GENERAL = "general"


class SourceType(str, PyEnum):
    """Types of research sources."""
    WEB_PAGE = "web_page"
    PDF = "pdf"
    NEWS_ARTICLE = "news_article"
    PRESS_RELEASE = "press_release"
    SEC_FILING = "sec_filing"
    SOCIAL_MEDIA = "social_media"
    VIDEO = "video"
    INTERNAL_DOC = "internal_doc"
    API_DATA = "api_data"
    OTHER = "other"


# =============================================================================
# Models
# =============================================================================


class Company(Base):
    """
    Company being researched.

    Represents a target company with basic information and metadata.
    A company can have multiple research runs over time.
    """
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(512))
    industry: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Company identifiers
    ticker_symbol: Mapped[Optional[str]] = mapped_column(String(20))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512))
    crunchbase_url: Mapped[Optional[str]] = mapped_column(String(512))

    # Company size/type
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    company_type: Mapped[Optional[str]] = mapped_column(String(50))  # public, private, startup
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)

    # Metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    research_runs: Mapped[List["ResearchRun"]] = relationship(
        "ResearchRun", back_populates="company", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_companies_name_country", "name", "country"),
        UniqueConstraint("name", "website", name="uq_company_name_website"),
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}')>"


class ResearchRun(Base):
    """
    A single research session for a company.

    Tracks the execution of a research pipeline including status,
    timing, configuration, and results.
    """
    __tablename__ = "research_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    # Run identification
    run_name: Mapped[Optional[str]] = mapped_column(String(255))
    run_type: Mapped[str] = mapped_column(String(50), default="full")  # full, quick, deep

    # Status tracking
    status: Mapped[ResearchRunStatus] = mapped_column(
        Enum(ResearchRunStatus), default=ResearchRunStatus.PENDING, nullable=False
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_phase: Mapped[Optional[str]] = mapped_column(String(100))

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50))
    ai_model: Mapped[Optional[str]] = mapped_column(String(100))

    # Results summary
    total_sources: Mapped[int] = mapped_column(Integer, default=0)
    total_insights: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)

    # Cost tracking
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Float)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Output paths
    output_dir: Mapped[Optional[str]] = mapped_column(String(512))
    report_path: Mapped[Optional[str]] = mapped_column(String(512))

    # Metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="research_runs")
    sources: Mapped[List["Source"]] = relationship(
        "Source", back_populates="research_run", cascade="all, delete-orphan"
    )
    insights: Mapped[List["Insight"]] = relationship(
        "Insight", back_populates="research_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_research_runs_company_status", "company_id", "status"),
        Index("ix_research_runs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ResearchRun(id={self.id}, company_id={self.company_id}, status={self.status})>"


class Source(Base):
    """
    A source used in research.

    Represents a web page, document, or other data source that was
    accessed and analyzed during a research run.
    """
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False
    )

    # Source identification
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(512))
    domain: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType), default=SourceType.WEB_PAGE
    )

    # Content
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA256
    content_length: Mapped[Optional[int]] = mapped_column(Integer)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)  # First ~500 chars

    # Quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)
    credibility_score: Mapped[Optional[float]] = mapped_column(Float)

    # Fetch metadata
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fetch_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    fetch_error: Mapped[Optional[str]] = mapped_column(Text)

    # Usage tracking
    used_in_analysis: Mapped[bool] = mapped_column(Boolean, default=True)
    cited_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    research_run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="sources")

    __table_args__ = (
        Index("ix_sources_research_run_domain", "research_run_id", "domain"),
        Index("ix_sources_url_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, url='{self.url[:50]}...')>"


class Insight(Base):
    """
    A research insight or finding.

    Represents a key finding, analysis result, or insight derived
    from research data.
    """
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False
    )

    # Insight content
    category: Mapped[InsightCategory] = mapped_column(
        Enum(InsightCategory), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(1000))

    # Classification
    sentiment: Mapped[Optional[str]] = mapped_column(String(20))  # positive, negative, neutral
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    importance_score: Mapped[Optional[float]] = mapped_column(Float)

    # Source attribution
    source_ids: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    citations: Mapped[Optional[List[dict]]] = mapped_column(JSONB, default=list)

    # AI generation info
    generated_by: Mapped[Optional[str]] = mapped_column(String(100))  # agent/model name
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text)

    # Validation
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(255))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Tags and metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    research_run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="insights")

    __table_args__ = (
        Index("ix_insights_research_run_category", "research_run_id", "category"),
        Index("ix_insights_importance", "importance_score"),
    )

    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, category={self.category}, title='{self.title[:30]}...')>"


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "Base",
    "Company",
    "ResearchRun",
    "Source",
    "Insight",
    "ResearchRunStatus",
    "InsightCategory",
    "SourceType",
]
