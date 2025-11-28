"""
Typed data models for research data.

This module provides strongly-typed Pydantic models to replace Dict[str, Any]
usage throughout the codebase. These models provide:

1. Runtime validation of data structure and types
2. IDE autocompletion and type hints
3. Automatic serialization/deserialization
4. Clear documentation of expected data shapes

Addresses architectural issue: Dict[str, Any] overuse (Issue #053)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Financial Data Models
# =============================================================================


class FinancialMetrics(BaseModel):
    """Core financial metrics for a company."""

    revenue: Optional[str] = Field(default=None, description="Annual revenue")
    profit: Optional[str] = Field(default=None, description="Net profit/loss")
    growth: Optional[str] = Field(default=None, description="Growth rate percentage")
    stock_ticker: Optional[str] = Field(default=None, description="Stock ticker symbol")
    market_cap: Optional[str] = Field(default=None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(default=None, description="Price-to-earnings ratio")
    debt_to_equity: Optional[float] = Field(default=None, description="Debt-to-equity ratio")


class FinancialData(BaseModel):
    """
    Complete financial data from the FinancialAgent.

    Used in:
    - ResearchState.financial_data
    - ReportWriter.write_report()
    - InsightGenerator.analyze()
    """

    revenue: Optional[str] = Field(default=None, description="Annual revenue")
    profit: Optional[str] = Field(default=None, description="Net profit/loss")
    growth: Optional[str] = Field(default=None, description="Growth rate percentage")
    stock_ticker: Optional[str] = Field(default=None, description="Stock ticker symbol")
    key_highlights: List[str] = Field(default_factory=list, description="Key financial highlights")

    # Extended metrics
    metrics: Optional[FinancialMetrics] = Field(default=None, description="Detailed metrics")
    sec_filings: List[str] = Field(default_factory=list, description="Recent SEC filing summaries")
    quant_analysis: Optional[str] = Field(default=None, description="Quantitative analysis output")

    # Raw data for flexibility during transition
    raw: Dict[str, Any] = Field(default_factory=dict, description="Additional unstructured data")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialData":
        """Create from a dictionary, handling missing/extra fields gracefully."""
        known_fields = {
            "revenue", "profit", "growth", "stock_ticker",
            "key_highlights", "metrics", "sec_filings", "quant_analysis"
        }

        # Extract known fields
        known = {k: v for k, v in data.items() if k in known_fields}
        # Store unknown fields in raw
        raw = {k: v for k, v in data.items() if k not in known_fields}

        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert back to Dict[str, Any] for backward compatibility."""
        result = self.model_dump(exclude={"raw", "metrics"})
        result.update(self.raw)
        if self.metrics:
            result.update(self.metrics.model_dump(exclude_none=True))
        return result


# =============================================================================
# Market Data Models
# =============================================================================


class MarketTrend(BaseModel):
    """A single market trend."""

    name: str = Field(..., description="Trend name/title")
    description: Optional[str] = Field(default=None, description="Trend description")
    impact: Optional[str] = Field(default=None, description="Expected impact on company")


class MarketData(BaseModel):
    """
    Market intelligence data from MarketAnalyst.

    Used in:
    - ResearchState.market_data
    - ReportWriter.write_report()
    - InsightGenerator.analyze()
    """

    industry: Optional[str] = Field(default=None, description="Industry name")
    market_size: Optional[str] = Field(default=None, description="Total addressable market size")
    market_growth: Optional[str] = Field(default=None, description="Market growth rate")
    trends: List[str] = Field(default_factory=list, description="Key market trends")

    # Extended data
    structured_trends: List[MarketTrend] = Field(default_factory=list, description="Detailed trend analysis")
    target_segments: List[str] = Field(default_factory=list, description="Target market segments")
    regulatory_factors: List[str] = Field(default_factory=list, description="Regulatory considerations")

    # Raw data for flexibility
    raw: Dict[str, Any] = Field(default_factory=dict, description="Additional unstructured data")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketData":
        """Create from a dictionary, handling missing/extra fields gracefully."""
        known_fields = {
            "industry", "market_size", "market_growth", "trends",
            "structured_trends", "target_segments", "regulatory_factors"
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        raw = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert back to Dict[str, Any] for backward compatibility."""
        result = self.model_dump(exclude={"raw", "structured_trends"})
        result.update(self.raw)
        return result


# =============================================================================
# Competitor Data Models
# =============================================================================


class Competitor(BaseModel):
    """Information about a single competitor."""

    name: str = Field(..., description="Competitor name")
    website: Optional[str] = Field(default=None, description="Competitor website")
    description: Optional[str] = Field(default=None, description="Brief description")
    strengths: List[str] = Field(default_factory=list, description="Competitor strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Competitor weaknesses")


class TechStack(BaseModel):
    """Technology stack analysis."""

    technologies: List[str] = Field(default_factory=list, description="Technologies detected")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks used")
    analytics: List[str] = Field(default_factory=list, description="Analytics tools")
    hosting: List[str] = Field(default_factory=list, description="Hosting/infrastructure")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechStack":
        """Create from dictionary."""
        return cls(
            technologies=data.get("technologies", []),
            frameworks=data.get("frameworks", []),
            analytics=data.get("analytics", []),
            hosting=data.get("hosting", []),
        )


class CompetitorData(BaseModel):
    """
    Competitive landscape data from CompetitorScout.

    Used in:
    - ResearchState.competitor_data
    - ReportWriter.write_report()
    - InsightGenerator.analyze()
    """

    competitors_list: Optional[str] = Field(default=None, description="Formatted competitor list")
    competitors: List[Competitor] = Field(default_factory=list, description="Detailed competitor data")
    competitive_advantages: List[str] = Field(default_factory=list, description="Company's advantages")
    tech_stack: Optional[TechStack] = Field(default=None, description="Technology stack analysis")

    # Raw data for flexibility
    raw: Dict[str, Any] = Field(default_factory=dict, description="Additional unstructured data")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompetitorData":
        """Create from a dictionary."""
        known_fields = {"competitors_list", "competitors", "competitive_advantages", "tech_stack"}

        # Handle nested tech_stack
        tech_stack = None
        if "tech_stack" in data and isinstance(data["tech_stack"], dict):
            tech_stack = TechStack.from_dict(data["tech_stack"])

        known = {k: v for k, v in data.items() if k in known_fields and k != "tech_stack"}
        raw = {k: v for k, v in data.items() if k not in known_fields}

        return cls(**known, tech_stack=tech_stack, raw=raw)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert back to Dict[str, Any] for backward compatibility."""
        result = self.model_dump(exclude={"raw", "competitors", "tech_stack"})
        result.update(self.raw)
        if self.tech_stack:
            result["tech_stack"] = self.tech_stack.model_dump()
        return result


# =============================================================================
# Brand Data Models
# =============================================================================


class BrandData(BaseModel):
    """
    Brand strategy data from BrandAuditor.

    Used in:
    - ResearchState.brand_data
    - ReportWriter.write_report()
    - InsightGenerator.analyze()
    """

    brand_positioning: Optional[str] = Field(default=None, description="Brand positioning statement")
    brand_voice: Optional[str] = Field(default=None, description="Brand voice description")
    brand_values: List[str] = Field(default_factory=list, description="Core brand values")
    messaging_themes: List[str] = Field(default_factory=list, description="Key messaging themes")
    customer_perception: Optional[str] = Field(default=None, description="Customer perception analysis")

    # Raw data for flexibility
    raw: Dict[str, Any] = Field(default_factory=dict, description="Additional unstructured data")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrandData":
        """Create from a dictionary."""
        known_fields = {
            "brand_positioning", "brand_voice", "brand_values",
            "messaging_themes", "customer_perception"
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        raw = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert back to Dict[str, Any] for backward compatibility."""
        result = self.model_dump(exclude={"raw"})
        result.update(self.raw)
        return result


# =============================================================================
# Sales Data Models
# =============================================================================


class SalesData(BaseModel):
    """
    Sales intelligence data from SalesAgent.

    Used in:
    - ResearchState.sales_data
    """

    sales_strategy: Optional[str] = Field(default=None, description="Sales strategy overview")
    distribution_channels: List[str] = Field(default_factory=list, description="Distribution channels")
    pricing_strategy: Optional[str] = Field(default=None, description="Pricing strategy")
    key_clients: List[str] = Field(default_factory=list, description="Notable B2B clients")
    pain_points: List[str] = Field(default_factory=list, description="Customer pain points")

    # Raw data for flexibility
    raw: Dict[str, Any] = Field(default_factory=dict, description="Additional unstructured data")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SalesData":
        """Create from a dictionary."""
        known_fields = {
            "sales_strategy", "distribution_channels", "pricing_strategy",
            "key_clients", "pain_points"
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        raw = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert back to Dict[str, Any] for backward compatibility."""
        result = self.model_dump(exclude={"raw"})
        result.update(self.raw)
        return result


# =============================================================================
# Strategic Insights Models
# =============================================================================


class SWOTAnalysis(BaseModel):
    """SWOT analysis structure."""

    strengths: List[str] = Field(default_factory=list, description="Company strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Company weaknesses")
    opportunities: List[str] = Field(default_factory=list, description="Market opportunities")
    threats: List[str] = Field(default_factory=list, description="Market threats")

    def is_empty(self) -> bool:
        """Check if SWOT analysis has any content."""
        return not any([self.strengths, self.weaknesses, self.opportunities, self.threats])


class StrategicInsights(BaseModel):
    """
    Strategic insights from InsightGenerator.

    Used in:
    - ReportWriter.write_report() as 'insights' parameter
    """

    swot: SWOTAnalysis = Field(default_factory=SWOTAnalysis, description="SWOT analysis")
    strategic_takeaways: List[str] = Field(default_factory=list, description="Key strategic insights")
    executive_summary: str = Field(default="N/A", description="Executive summary")

    # Raw data for flexibility
    raw: Dict[str, Any] = Field(default_factory=dict, description="Additional unstructured data")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategicInsights":
        """Create from a dictionary, handling LLM output variations and None values."""
        if data is None:
            data = {}

        swot_data = data.get("swot") or {}
        swot = SWOTAnalysis(
            strengths=swot_data.get("strengths") or [],
            weaknesses=swot_data.get("weaknesses") or [],
            opportunities=swot_data.get("opportunities") or [],
            threats=swot_data.get("threats") or [],
        )

        known_fields = {"swot", "strategic_takeaways", "executive_summary"}
        raw = {k: v for k, v in data.items() if k not in known_fields}

        # Handle None values by providing defaults
        executive_summary = data.get("executive_summary")
        if executive_summary is None:
            executive_summary = "N/A"

        strategic_takeaways = data.get("strategic_takeaways")
        if strategic_takeaways is None:
            strategic_takeaways = []

        return cls(
            swot=swot,
            strategic_takeaways=strategic_takeaways,
            executive_summary=executive_summary,
            raw=raw,
        )

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert back to Dict[str, Any] for backward compatibility."""
        result = {
            "swot": self.swot.model_dump(),
            "strategic_takeaways": self.strategic_takeaways,
            "executive_summary": self.executive_summary,
        }
        result.update(self.raw)
        return result


# =============================================================================
# Research Context (Aggregated Data)
# =============================================================================


class TypedResearchContext(BaseModel):
    """
    Aggregated research data from specialist agents.

    Replaces the loosely-typed ResearchContext from types.py
    with strongly-typed fields.
    """

    financial_data: FinancialData = Field(default_factory=FinancialData)
    market_data: MarketData = Field(default_factory=MarketData)
    competitor_data: CompetitorData = Field(default_factory=CompetitorData)
    brand_data: BrandData = Field(default_factory=BrandData)
    sales_data: SalesData = Field(default_factory=SalesData)

    @classmethod
    def from_state_dicts(
        cls,
        financial: Dict[str, Any],
        market: Dict[str, Any],
        competitor: Dict[str, Any],
        brand: Dict[str, Any],
        sales: Optional[Dict[str, Any]] = None,
    ) -> "TypedResearchContext":
        """Create from individual Dict[str, Any] fields in ResearchState."""
        return cls(
            financial_data=FinancialData.from_dict(financial or {}),
            market_data=MarketData.from_dict(market or {}),
            competitor_data=CompetitorData.from_dict(competitor or {}),
            brand_data=BrandData.from_dict(brand or {}),
            sales_data=SalesData.from_dict(sales or {}),
        )

    def to_legacy_dicts(self) -> Dict[str, Dict[str, Any]]:
        """Convert to legacy Dict[str, Any] format for backward compatibility."""
        return {
            "financial_data": self.financial_data.to_legacy_dict(),
            "market_data": self.market_data.to_legacy_dict(),
            "competitor_data": self.competitor_data.to_legacy_dict(),
            "brand_data": self.brand_data.to_legacy_dict(),
            "sales_data": self.sales_data.to_legacy_dict(),
        }


# =============================================================================
# Search Result Models
# =============================================================================


class SearchResult(BaseModel):
    """A single search result from Tavily or other search tools."""

    url: str = Field(..., description="Result URL")
    title: str = Field(default="", description="Result title")
    content: str = Field(default="", description="Result content/snippet")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create from dictionary."""
        return cls(
            url=data.get("url", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            score=data.get("score", 0.0),
        )


class SearchResults(BaseModel):
    """Collection of search results."""

    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(default_factory=list)
    total_count: int = Field(default=0, description="Total results available")

    @classmethod
    def from_list(cls, query: str, results: List[Dict[str, Any]]) -> "SearchResults":
        """Create from a list of result dictionaries."""
        return cls(
            query=query,
            results=[SearchResult.from_dict(r) for r in results],
            total_count=len(results),
        )


# =============================================================================
# Critic Feedback Model
# =============================================================================


class CriticFeedback(BaseModel):
    """Feedback from the Critic agent."""

    score: float = Field(default=0.0, ge=0.0, le=10.0, description="Quality score 0-10")
    strengths: List[str] = Field(default_factory=list, description="Report strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    suggestions: List[str] = Field(default_factory=list, description="Specific suggestions")
    approved: bool = Field(default=False, description="Whether report is approved")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticFeedback":
        """Create from dictionary, handling LLM output variations."""
        return cls(
            score=float(data.get("score", 0.0)),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
            approved=bool(data.get("approved", False)),
        )


# =============================================================================
# Raw Data Item (for state.raw_data)
# =============================================================================


class RawDataItem(BaseModel):
    """A single raw data item collected during research."""

    source: str = Field(..., description="Data source identifier")
    content: str = Field(default="", description="Raw content")
    url: Optional[str] = Field(default=None, description="Source URL if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RawDataItem":
        """Create from dictionary."""
        return cls(
            source=data.get("source", "unknown"),
            content=data.get("content", ""),
            url=data.get("url"),
            metadata={k: v for k, v in data.items() if k not in {"source", "content", "url", "timestamp"}},
        )


# =============================================================================
# Export all models
# =============================================================================

__all__ = [
    # Financial
    "FinancialMetrics",
    "FinancialData",
    # Market
    "MarketTrend",
    "MarketData",
    # Competitor
    "Competitor",
    "TechStack",
    "CompetitorData",
    # Brand
    "BrandData",
    # Sales
    "SalesData",
    # Insights
    "SWOTAnalysis",
    "StrategicInsights",
    # Context
    "TypedResearchContext",
    # Search
    "SearchResult",
    "SearchResults",
    # Critic
    "CriticFeedback",
    # Raw data
    "RawDataItem",
]
