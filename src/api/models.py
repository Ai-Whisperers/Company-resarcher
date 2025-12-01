import re
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, Dict, Any

# Character patterns for input validation
COMPANY_NAME_PATTERN = re.compile(r'^[\w\s\-\.\,\&\'\"\(\)\+\/\:]+$', re.UNICODE)
INDUSTRY_PATTERN = re.compile(r'^[\w\s\-\/\&\,\.]+$', re.UNICODE)
COUNTRY_PATTERN = re.compile(r'^[\w\s\-\.\']+$', re.UNICODE)


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
