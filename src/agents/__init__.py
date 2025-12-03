"""
Research Agents module.

Provides:
- BaseAgent: Abstract base class for all agents
- AgentFactory: Factory for creating agents
- Specialized agents: FinancialAgent, MarketAnalyst, etc.
"""

from .base_agent import BaseAgent
from .factory import AgentFactory, get_agent_factory
from .generic_agent import GenericResearchAgent
from .specialists import (
    FinancialAgent,
    MarketAnalyst,
    CompetitorScout,
    BrandAuditor,
    SalesAgent,
    InvestmentAgent,
    SocialMediaAgent,
)
from .writer import ReportWriter
from .critic import LogicCritic
from .insight_generator import InsightGenerator
from .reasoning_agent import ReasoningAgent
from .deep_research import DeepResearchAgent
from .sector_analyst import SectorAnalyst


# Lazy import for ResearchOrchestrator to avoid circular import with graph module
def __getattr__(name):
    """Lazy import for deprecated modules."""
    if name == "ResearchOrchestrator":
        from .orchestrator import ResearchOrchestrator
        return ResearchOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base
    "BaseAgent",
    # Factory
    "AgentFactory",
    "get_agent_factory",
    # Generic
    "GenericResearchAgent",
    # Specialists
    "FinancialAgent",
    "MarketAnalyst",
    "CompetitorScout",
    "BrandAuditor",
    "SalesAgent",
    "InvestmentAgent",
    "SocialMediaAgent",
    # Other agents
    "ReportWriter",
    "LogicCritic",
    "InsightGenerator",
    "ResearchOrchestrator",  # Deprecated - lazy loaded
    "ReasoningAgent",
    "DeepResearchAgent",
    "SectorAnalyst",
]
