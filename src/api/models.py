from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, Dict, Any


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
    def company_name_must_not_be_empty(cls, v: str) -> str:
        """Validate that company name is not empty or whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty or whitespace only")
        return v

    @field_validator("industry", "country")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from optional string fields."""
        if v is not None:
            return v.strip() or None
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
from sqlalchemy import Column, String, Text
from .database import Base


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String)
    request = Column(Text)  # JSON string
    result = Column(Text)  # JSON string
    error = Column(Text)
