from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ResearchSource(BaseModel):
    """Represents a single source of information (webpage, PDF, etc.)"""

    url: str
    title: str
    content: str
    source_type: str = "web"  # web, pdf, news, etc.
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    reliability_score: float = 0.0  # 0.0 to 1.0


class CompanyProfile(BaseModel):
    """Basic input information about a company"""

    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    country: str = "Global"
    description: Optional[str] = None
    target_audience: Optional[str] = None
    competitors: List[str] = Field(default_factory=list)


class ResearchPhaseResult(BaseModel):
    """Result of a specific research phase (e.g., Market Analysis)"""

    phase_name: str
    markdown_content: str
    sources: List[ResearchSource]
    key_findings: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)


class FullCompanyResearch(BaseModel):
    """The complete research dossier for a company"""

    company: CompanyProfile
    phases: Dict[str, ResearchPhaseResult] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    output_path: str
