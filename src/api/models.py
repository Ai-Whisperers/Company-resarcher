from pydantic import BaseModel
from typing import Optional, Dict, Any


class ResearchRequest(BaseModel):
    company_name: str
    url: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = "USA"


class ResearchResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
