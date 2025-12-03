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
from .orchestrator import ResearchOrchestrator
from .reasoning_agent import ReasoningAgent
from .deep_research import DeepResearchAgent
from .sector_analyst import SectorAnalyst

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
    "ResearchOrchestrator",
    "ReasoningAgent",
    "DeepResearchAgent",
    "SectorAnalyst",
]
