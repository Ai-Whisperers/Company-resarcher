"""
SQLAlchemy database models for Company Researcher.

DATA-002: Full PostgreSQL schema design with:
- Companies: Company profiles and metadata
- ResearchRuns: Research task execution history
- Sources: External sources used in research
- Insights: Generated insights from research
- Citations: Source-to-insight mappings

Supports both SQLite (development) and PostgreSQL (production).
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    Enum,
    Index,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from .database import Base


class TaskStatus(str, PyEnum):
    """Research task status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, PyEnum):
    """Source type classification."""
    WEB = "web"
    PDF = "pdf"
    SEC_FILING = "sec_filing"
    NEWS = "news"
    SOCIAL = "social"
    VIDEO = "video"
    API = "api"
    OTHER = "other"


class InsightCategory(str, PyEnum):
    """Insight categorization."""
    FINANCIAL = "financial"
    MARKET = "market"
    COMPETITOR = "competitor"
    BRAND = "brand"
    SALES = "sales"
    INVESTMENT = "investment"
    SOCIAL_MEDIA = "social_media"
    GENERAL = "general"


# =============================================================================
# Core Models
# =============================================================================


class Company(Base):
    """
    Company profile and metadata.

    Stores basic company information that persists across research runs.
    """
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    research_runs: Mapped[List["ResearchRun"]] = relationship("ResearchRun", back_populates="company", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_companies_name_lower", "name"),
        UniqueConstraint("name", "country", name="uq_company_name_country"),
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', industry='{self.industry}')>"


class ResearchRun(Base):
    """
    Individual research execution record.

    Tracks each research run with its configuration, status, and results.
    """
    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    # Status tracking
    status: Mapped[str] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Research config snapshot

    # Results
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Full result JSON

    # Metrics
    total_sources: Mapped[int] = mapped_column(Integer, default=0)
    total_insights: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="research_runs")
    sources: Mapped[List["Source"]] = relationship("Source", back_populates="research_run", cascade="all, delete-orphan")
    insights: Mapped[List["Insight"]] = relationship("Insight", back_populates="research_run", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_research_runs_status", "status"),
        Index("ix_research_runs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ResearchRun(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"


class Source(Base):
    """
    External source used in research.

    Stores information about web pages, documents, and other sources.
    """
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    research_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False)

    # Source identification
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(Enum(SourceType), default=SourceType.WEB, nullable=False)

    # Content
    content_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # First ~500 chars
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA256 of full content

    # Quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1 score
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1 score
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)  # Primary vs supporting source

    # Metadata
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    research_run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="sources")
    citations: Mapped[List["Citation"]] = relationship("Citation", back_populates="source", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_sources_url_hash", "content_hash"),
        Index("ix_sources_source_type", "source_type"),
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, domain='{self.domain}', type='{self.source_type}')>"


class Insight(Base):
    """
    Generated insight from research.

    Stores individual insights with their category and confidence.
    """
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    research_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False)

    # Insight content
    category: Mapped[str] = mapped_column(Enum(InsightCategory), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Brief summary

    # Confidence and importance
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    importance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    is_key_finding: Mapped[bool] = mapped_column(Boolean, default=False)

    # Structured data
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Additional structured data

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    research_run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="insights")
    citations: Mapped[List["Citation"]] = relationship("Citation", back_populates="insight", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_insights_category", "category"),
        Index("ix_insights_is_key_finding", "is_key_finding"),
    )

    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, category='{self.category}', title='{self.title[:50]}...')>"


class Citation(Base):
    """
    Link between insights and their supporting sources.

    Enables tracking which sources support which insights.
    """
    __tablename__ = "citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_id: Mapped[int] = mapped_column(Integer, ForeignKey("insights.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)

    # Citation context
    quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Relevant quote from source
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For PDFs
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Section reference

    # Relationships
    insight: Mapped["Insight"] = relationship("Insight", back_populates="citations")
    source: Mapped["Source"] = relationship("Source", back_populates="citations")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("insight_id", "source_id", name="uq_citation_insight_source"),
    )

    def __repr__(self) -> str:
        return f"<Citation(insight_id={self.insight_id}, source_id={self.source_id})>"


# =============================================================================
# Analytics & Caching Tables
# =============================================================================


class SearchCache(Base):
    """
    Cache for search query results.

    Reduces API costs by caching search results.
    """
    __tablename__ = "search_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    results: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, default=0)

    # TTL management
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<SearchCache(query_hash='{self.query_hash[:16]}...', hits={self.hit_count})>"


class UsageMetrics(Base):
    """
    Track API usage and costs per day.

    Enables cost monitoring and budget management.
    """
    __tablename__ = "usage_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Token usage
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Costs
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # Request counts
    requests_total: Mapped[int] = mapped_column(Integer, default=0)
    requests_failed: Mapped[int] = mapped_column(Integer, default=0)
    requests_cached: Mapped[int] = mapped_column(Integer, default=0)

    # Unique constraint per day per provider
    __table_args__ = (
        UniqueConstraint("date", "provider", name="uq_usage_date_provider"),
    )

    def __repr__(self) -> str:
        return f"<UsageMetrics(date={self.date}, provider='{self.provider}', cost=${self.cost_usd:.4f})>"


# =============================================================================
# Helper Functions
# =============================================================================


def create_all_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(bind=engine)
