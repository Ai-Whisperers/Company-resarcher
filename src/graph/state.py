from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class SourceMetadata(BaseModel):
    url: str
    title: str
    date_accessed: str
    reliability_score: float = 0.0
    summary: str = ""


class ResearchState(BaseModel):
    """
    The global state (Blackboard) for the research process.
    Passed between all agents in the LangGraph.
    """

    # Input
    company_name: str
    website: str

    # Wave 1: Raw Data Gathering
    # Stores raw text chunks or source objects
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)
    source_log: List[SourceMetadata] = Field(default_factory=list)

    # Wave 2: Inferred Data (Analysis)
    # These will be populated by Analyst agents
    financial_data: Dict[str, Any] = Field(default_factory=dict)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    sales_data: Dict[str, Any] = Field(default_factory=dict)

    # Wave 3: Drafting
    # Key = Section Name (e.g., "01-Executive-Summary"), Value = Markdown Content
    drafts: Dict[str, str] = Field(default_factory=dict)

    # Meta / Control Flow
    current_wave: str = "init"  # init, gathering, thinking, writing, review
    messages: List[BaseMessage] = Field(
        default_factory=list
    )  # For chat history/agent comms
    errors: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
