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
