import re
from enum import Enum
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, Dict, Any, List

# Character patterns for input validation
COMPANY_NAME_PATTERN = re.compile(r'^[\w\s\-\.\,\&\'\"\(\)\+\/\:]+$', re.UNICODE)
INDUSTRY_PATTERN = re.compile(r'^[\w\s\-\/\&\,\.]+$', re.UNICODE)
COUNTRY_PATTERN = re.compile(r'^[\w\s\-\.\']+$', re.UNICODE)


class ResearchMode(str, Enum):
    """Available research modes."""
    STANDARD = "standard"           # Quick research with essential phases
    COMPREHENSIVE = "comprehensive" # Full 200+ query deep research
    DEEP = "deep"                   # Iterative research with learnings extraction
    INCREMENTAL = "incremental"     # Update existing research with new data
    SINGLE_PHASE = "single_phase"   # Run a single research phase
    ITERATIVE = "iterative"         # Iterative research with automatic gap-filling


class ResearchPhase(str, Enum):
    """Available research phases."""
    MARKET = "market"
    FINANCIAL = "financial"
    COMPETITOR = "competitor"
    BRAND = "brand"
    SALES = "sales"


class ResearchRequest(BaseModel):
    """Request model for starting a research task."""

    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the company to research",
    )
    url: Optional[HttpUrl] = Field(
        None,
        description="Company website URL",
    )
    industry: Optional[str] = Field(
        None,
        max_length=100,
        description="Industry sector of the company",
    )
    country: Optional[str] = Field(
        "USA",
        max_length=100,
        description="Country where the company is headquartered",
    )
    research_mode: ResearchMode = Field(
        ResearchMode.STANDARD,
        description="Research mode: standard (quick), comprehensive (full), deep (iterative), incremental (update), single_phase",
    )
    phases: Optional[List[ResearchPhase]] = Field(
        None,
        description="Specific phases to research (defaults to all). Only used with standard/comprehensive modes.",
    )
    single_phase: Optional[ResearchPhase] = Field(
        None,
        description="Required when research_mode is 'single_phase'. The specific phase to run.",
    )
    include_github: bool = Field(
        False,
        description="Include GitHub tech stack analysis (requires GITHUB_TOKEN)",
    )
    include_corporate_registry: bool = Field(
        False,
        description="Include corporate registry and WHOIS lookup",
    )

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        """Validate company name is not empty and contains only allowed characters."""
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty or whitespace only")
        if not COMPANY_NAME_PATTERN.match(v):
            raise ValueError(
                "Company name contains invalid characters. "
                "Allowed: letters, numbers, spaces, and common punctuation (-.,'\"()&+/:)"
            )
        return v

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, v: Optional[str]) -> Optional[str]:
        """Validate industry field contains only allowed characters."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not INDUSTRY_PATTERN.match(v):
            raise ValueError(
                "Industry contains invalid characters. "
                "Allowed: letters, numbers, spaces, and basic punctuation (-/&,.)"
            )
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        """Validate country field contains only allowed characters."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not COUNTRY_PATTERN.match(v):
            raise ValueError(
                "Country contains invalid characters. "
                "Allowed: letters, numbers, spaces, hyphens, periods, and apostrophes"
            )
        return v


class ResearchResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = Field(default=None, description="Research result data")
    error: Optional[str] = Field(default=None, description="Error message if task failed")


class MarketConsolidationRequest(BaseModel):
    """Request to consolidate research from multiple companies into a market report."""
    market_name: str = Field(..., description="Name for the consolidated market report")
    company_folders: List[str] = Field(..., description="List of company folder names to consolidate")
    market_config: Optional[Dict[str, Any]] = Field(None, description="Optional market configuration")


# SQLAlchemy Models
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from .database import Base


class Task(Base):
    """SQLAlchemy model for research tasks with timestamps."""
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String)
    request = Column(Text)  # JSON string
    result = Column(Text)  # JSON string
    error = Column(Text)

    # Timestamp fields (BUG-021 fix)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
