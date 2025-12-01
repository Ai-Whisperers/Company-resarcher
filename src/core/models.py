"""
Typed data models for research data.

This module provides strongly-typed Pydantic models to replace dict[str, Any]
usage throughout the codebase. These models provide:

1. Runtime validation of data structure and types
2. IDE autocompletion and type hints
3. Automatic serialization/deserialization
4. Clear documentation of expected data shapes

Addresses architectural issue: dict[str, Any] overuse (Issue #053)
"""

from datetime import datetime
from typing import Any, Optional, Union
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
    pe_ratio: Optional[float] = Field(
        default=None, description="Price-to-earnings ratio"
    )
    debt_to_equity: Optional[float] = Field(
        default=None, description="Debt-to-equity ratio"
    )


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
    key_highlights: list[str] = Field(
        default_factory=list, description="Key financial highlights"
    )

    # Extended metrics
    metrics: Optional[FinancialMetrics] = Field(
        default=None, description="Detailed metrics"
    )
    ebitda: Optional[str] = Field(default=None, description="EBITDA")
    total_assets: Optional[str] = Field(default=None, description="Total assets")
    total_employees: Optional[str] = Field(default=None, description="Total employees")
    revenue_per_employee: Optional[str] = Field(
        default=None, description="Revenue per employee"
    )
    total_debt: Optional[str] = Field(default=None, description="Total debt")
    credit_rating: Optional[str] = Field(default=None, description="Credit rating")

    sec_filings: list[str] = Field(
        default_factory=list, description="Recent SEC filing summaries"
    )
    quant_analysis: Optional[str] = Field(
        default=None, description="Quantitative analysis output"
    )

    # Raw data for flexibility during transition
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Additional unstructured data"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialData":
        """Create from a dictionary, handling missing/extra fields gracefully."""
        known_fields = {
            "revenue",
            "profit",
            "growth",
            "stock_ticker",
            "key_highlights",
            "metrics",
            "sec_filings",
            "quant_analysis",
        }

        # Extract known fields
        known = {k: v for k, v in data.items() if k in known_fields}
        # Store unknown fields in raw
        raw = {k: v for k, v in data.items() if k not in known_fields}

        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert back to dict[str, Any] for backward compatibility."""
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
    impact: Optional[str] = Field(
        default=None, description="Expected impact on company"
    )


class MarketData(BaseModel):
    """
    Market intelligence data from MarketAnalyst.

    Used in:
    - ResearchState.market_data
    - ReportWriter.write_report()
    - InsightGenerator.analyze()
    """

    industry: Optional[str] = Field(default=None, description="Industry name")
    market_size: Optional[str] = Field(
        default=None, description="Total addressable market size"
    )
    market_growth: Optional[str] = Field(default=None, description="Market growth rate")
    trends: list[str] = Field(default_factory=list, description="Key market trends")

    # Extended data
    structured_trends: list[MarketTrend] = Field(
        default_factory=list, description="Detailed trend analysis"
    )
    target_segments: list[str] = Field(
        default_factory=list, description="Target market segments"
    )
    regulatory_factors: list[str] = Field(
        default_factory=list, description="Regulatory considerations"
    )

    # Raw data for flexibility
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Additional unstructured data"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MarketData":
        """Create from a dictionary, handling missing/extra fields gracefully."""
        known_fields = {
            "industry",
            "market_size",
            "market_growth",
            "trends",
            "structured_trends",
            "target_segments",
            "regulatory_factors",
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        raw = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert back to dict[str, Any] for backward compatibility."""
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
    strengths: list[str] = Field(
        default_factory=list, description="Competitor strengths"
    )
    weaknesses: list[str] = Field(
        default_factory=list, description="Competitor weaknesses"
    )


class TechStack(BaseModel):
    """Technology stack analysis."""

    technologies: list[str] = Field(
        default_factory=list, description="Technologies detected"
    )
    frameworks: list[str] = Field(default_factory=list, description="Frameworks used")
    analytics: list[str] = Field(default_factory=list, description="Analytics tools")
    hosting: list[str] = Field(
        default_factory=list, description="Hosting/infrastructure"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TechStack":
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

    competitors_list: Optional[str] = Field(
        default=None, description="Formatted competitor list"
    )
    competitors: list[Competitor] = Field(
        default_factory=list, description="Detailed competitor data"
    )
    competitive_advantages: list[str] = Field(
        default_factory=list, description="Company's advantages"
    )
    tech_stack: Optional[TechStack] = Field(
        default=None, description="Technology stack analysis"
    )

    # Raw data for flexibility
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Additional unstructured data"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompetitorData":
        """Create from a dictionary."""
        known_fields = {
            "competitors_list",
            "competitors",
            "competitive_advantages",
            "tech_stack",
        }

        # Handle nested tech_stack
        tech_stack = None
        if "tech_stack" in data and isinstance(data["tech_stack"], dict):
            tech_stack = TechStack.from_dict(data["tech_stack"])

        known = {
            k: v for k, v in data.items() if k in known_fields and k != "tech_stack"
        }
        raw = {k: v for k, v in data.items() if k not in known_fields}

        return cls(**known, tech_stack=tech_stack, raw=raw)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert back to dict[str, Any] for backward compatibility."""
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

    brand_positioning: Optional[str] = Field(
        default=None, description="Brand positioning statement"
    )
    brand_voice: Optional[str] = Field(
        default=None, description="Brand voice description"
    )
    brand_values: list[str] = Field(
        default_factory=list, description="Core brand values"
    )
    messaging_themes: list[str] = Field(
        default_factory=list, description="Key messaging themes"
    )
    customer_perception: Optional[str] = Field(
        default=None, description="Customer perception analysis"
    )

    # Raw data for flexibility
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Additional unstructured data"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrandData":
        """Create from a dictionary."""
        known_fields = {
            "brand_positioning",
            "brand_voice",
            "brand_values",
            "messaging_themes",
            "customer_perception",
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        raw = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert back to dict[str, Any] for backward compatibility."""
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

    sales_strategy: Optional[str] = Field(
        default=None, description="Sales strategy overview"
    )
    distribution_channels: list[str] = Field(
        default_factory=list, description="Distribution channels"
    )
    pricing_strategy: Optional[str] = Field(
        default=None, description="Pricing strategy"
    )
    key_clients: list[str] = Field(
        default_factory=list, description="Notable B2B clients"
    )
    pain_points: list[str] = Field(
        default_factory=list, description="Customer pain points"
    )

    # Raw data for flexibility
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Additional unstructured data"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SalesData":
        """Create from a dictionary."""
        known_fields = {
            "sales_strategy",
            "distribution_channels",
            "pricing_strategy",
            "key_clients",
            "pain_points",
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        raw = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, raw=raw)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert back to dict[str, Any] for backward compatibility."""
        result = self.model_dump(exclude={"raw"})
        result.update(self.raw)
        return result


# =============================================================================
# Strategic Insights Models
# =============================================================================


class SWOTAnalysis(BaseModel):
    """SWOT analysis structure."""

    strengths: list[str] = Field(default_factory=list, description="Company strengths")
    weaknesses: list[str] = Field(
        default_factory=list, description="Company weaknesses"
    )
    opportunities: list[str] = Field(
        default_factory=list, description="Market opportunities"
    )
    threats: list[str] = Field(default_factory=list, description="Market threats")

    def is_empty(self) -> bool:
        """Check if SWOT analysis has any content."""
        return not any(
            [self.strengths, self.weaknesses, self.opportunities, self.threats]
        )


class StrategicInsights(BaseModel):
    """
    Strategic insights from InsightGenerator.

    Used in:
    - ReportWriter.write_report() as 'insights' parameter
    """

    swot: SWOTAnalysis = Field(
        default_factory=SWOTAnalysis, description="SWOT analysis"
    )
    strategic_takeaways: list[str] = Field(
        default_factory=list, description="Key strategic insights"
    )
    executive_summary: str = Field(default="N/A", description="Executive summary")

    # Raw data for flexibility
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Additional unstructured data"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrategicInsights":
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

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convert back to dict[str, Any] for backward compatibility."""
        result = {
            "swot": self.swot.model_dump(),
            "strategic_takeaways": self.strategic_takeaways,
            "executive_summary": self.executive_summary,
        }
        result.update(self.raw)
        return result


# =============================================================================
# New Data Models (Enhanced Research)
# =============================================================================


class ContactInfo(BaseModel):
    """Contact details and digital presence."""

    email_addresses: list[str] = Field(
        default_factory=list, description="Email addresses"
    )
    phone_numbers: list[str] = Field(default_factory=list, description="Phone numbers")
    social_media: dict[str, str] = Field(
        default_factory=dict, description="Social media handles/URLs"
    )
    locations: list[str] = Field(
        default_factory=list, description="Physical locations/branches"
    )
    hq_address: Optional[str] = Field(default=None, description="Headquarters address")
    customer_service: Optional[str] = Field(
        default=None, description="Customer service contact"
    )
    app_store_links: dict[str, str] = Field(
        default_factory=dict, description="App store links"
    )


class Leadership(BaseModel):
    """Company leadership and ownership structure."""

    executives: list[dict[str, str]] = Field(
        default_factory=list, description="Key executives (Name, Title)"
    )
    board_members: list[str] = Field(
        default_factory=list, description="Board of Directors"
    )
    ownership_structure: list[dict[str, Any]] = Field(
        default_factory=list, description="Shareholders and percentages"
    )
    ultimate_beneficial_owners: list[str] = Field(
        default_factory=list, description="UBOs"
    )
    holding_company: Optional[str] = Field(
        default=None, description="Parent/Holding company"
    )


class ProductService(BaseModel):
    """Product and service offerings."""

    catalog: list[dict[str, Any]] = Field(
        default_factory=list, description="Product/Service catalog"
    )
    pricing_models: list[str] = Field(
        default_factory=list, description="Pricing tiers/models"
    )
    target_segments: list[str] = Field(
        default_factory=list, description="Target customer segments"
    )
    unique_selling_props: list[str] = Field(default_factory=list, description="USPs")


class RegulatoryCompliance(BaseModel):
    """Regulatory and compliance information."""

    licenses: list[str] = Field(default_factory=list, description="Operating licenses")
    certifications: list[str] = Field(
        default_factory=list, description="Certifications (ISO, etc.)"
    )
    sanctions: list[str] = Field(
        default_factory=list, description="Sanctions or penalties"
    )
    legal_disputes: list[str] = Field(
        default_factory=list, description="Ongoing legal disputes"
    )
    regulatory_bodies: list[str] = Field(
        default_factory=list, description="Regulating bodies"
    )


class Infrastructure(BaseModel):
    """Physical and technical infrastructure."""

    facilities: list[str] = Field(
        default_factory=list, description="Data centers, factories, towers"
    )
    tech_stack: Optional[TechStack] = Field(
        default=None, description="Technology stack"
    )
    patents: list[str] = Field(default_factory=list, description="Patents held")
    rd_investments: Optional[str] = Field(
        default=None, description="R&D investment details"
    )


class Partnership(BaseModel):
    """Strategic partnerships and ecosystem."""

    strategic_partners: list[str] = Field(
        default_factory=list, description="Strategic partners"
    )
    suppliers: list[str] = Field(
        default_factory=list, description="Key suppliers/vendors"
    )
    associations: list[str] = Field(
        default_factory=list, description="Industry associations"
    )
    joint_ventures: list[str] = Field(
        default_factory=list, description="Joint ventures"
    )


class ESGData(BaseModel):
    """Environmental, Social, and Governance data."""

    sustainability_initiatives: list[str] = Field(
        default_factory=list, description="Environmental initiatives"
    )
    csr_programs: list[str] = Field(default_factory=list, description="CSR programs")
    diversity_metrics: Optional[str] = Field(
        default=None, description="Diversity statistics"
    )
    governance_policies: list[str] = Field(
        default_factory=list, description="Governance policies"
    )


class CompanyHistory(BaseModel):
    """Historical timeline and milestones."""

    founded_date: Optional[str] = Field(default=None, description="Date founded")
    founders: list[str] = Field(default_factory=list, description="Founders")
    milestones: list[dict[str, str]] = Field(
        default_factory=list, description="Key milestones (Date, Event)"
    )
    mergers_acquisitions: list[str] = Field(
        default_factory=list, description="M&A history"
    )
    pivots: list[str] = Field(default_factory=list, description="Major strategy pivots")


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

    # New Fields
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    leadership: Leadership = Field(default_factory=Leadership)
    products: ProductService = Field(default_factory=ProductService)
    regulatory: RegulatoryCompliance = Field(default_factory=RegulatoryCompliance)
    infrastructure: Infrastructure = Field(default_factory=Infrastructure)
    partnerships: Partnership = Field(default_factory=Partnership)
    esg_data: ESGData = Field(default_factory=ESGData)
    history: CompanyHistory = Field(default_factory=CompanyHistory)

    sources: list[Any] = Field(
        default_factory=list, description="List of ResearchSource objects"
    )

    @classmethod
    def from_state_dicts(
        cls,
        financial: dict[str, Any],
        market: dict[str, Any],
        competitor: dict[str, Any],
        brand: dict[str, Any],
        sales: Optional[dict[str, Any]] = None,
        sources: Optional[list[Any]] = None,
        # New fields (optional for backward compatibility)
        contact: Optional[dict[str, Any]] = None,
        leadership: Optional[dict[str, Any]] = None,
        products: Optional[dict[str, Any]] = None,
        regulatory: Optional[dict[str, Any]] = None,
        infrastructure: Optional[dict[str, Any]] = None,
        partnerships: Optional[dict[str, Any]] = None,
        esg: Optional[dict[str, Any]] = None,
        history: Optional[dict[str, Any]] = None,
    ) -> "TypedResearchContext":
        """Create from individual dict[str, Any] fields in ResearchState."""
        return cls(
            financial_data=FinancialData.from_dict(financial or {}),
            market_data=MarketData.from_dict(market or {}),
            competitor_data=CompetitorData.from_dict(competitor or {}),
            brand_data=BrandData.from_dict(brand or {}),
            sales_data=SalesData.from_dict(sales or {}),
            contact_info=ContactInfo(**(contact or {})),
            leadership=Leadership(**(leadership or {})),
            products=ProductService(**(products or {})),
            regulatory=RegulatoryCompliance(**(regulatory or {})),
            infrastructure=Infrastructure(**(infrastructure or {})),
            partnerships=Partnership(**(partnerships or {})),
            esg_data=ESGData(**(esg or {})),
            history=CompanyHistory(**(history or {})),
            sources=sources or [],
        )

    def to_legacy_dicts(self) -> dict[str, dict[str, Any]]:
        """Convert to legacy dict[str, Any] format for backward compatibility."""
        return {
            "financial_data": self.financial_data.to_legacy_dict(),
            "market_data": self.market_data.to_legacy_dict(),
            "competitor_data": self.competitor_data.to_legacy_dict(),
            "brand_data": self.brand_data.to_legacy_dict(),
            "sales_data": self.sales_data.to_legacy_dict(),
            "contact_info": self.contact_info.model_dump(),
            "leadership": self.leadership.model_dump(),
            "products": self.products.model_dump(),
            "regulatory": self.regulatory.model_dump(),
            "infrastructure": self.infrastructure.model_dump(),
            "partnerships": self.partnerships.model_dump(),
            "esg_data": self.esg_data.model_dump(),
            "history": self.history.model_dump(),
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
    def from_dict(cls, data: dict[str, Any]) -> "SearchResult":
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
    results: list[SearchResult] = Field(default_factory=list)
    total_count: int = Field(default=0, description="Total results available")

    @classmethod
    def from_list(cls, query: str, results: list[dict[str, Any]]) -> "SearchResults":
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
    strengths: list[str] = Field(default_factory=list, description="Report strengths")
    weaknesses: list[str] = Field(
        default_factory=list, description="Areas for improvement"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Specific suggestions"
    )
    approved: bool = Field(default=False, description="Whether report is approved")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CriticFeedback":
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
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawDataItem":
        """Create from dictionary."""
        return cls(
            source=data.get("source", "unknown"),
            content=data.get("content", ""),
            url=data.get("url"),
            metadata={
                k: v
                for k, v in data.items()
                if k not in {"source", "content", "url", "timestamp"}
            },
        )


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
    # New Models
    "ContactInfo",
    "Leadership",
    "ProductService",
    "RegulatoryCompliance",
    "Infrastructure",
    "Partnership",
    "ESGData",
    "CompanyHistory",
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
