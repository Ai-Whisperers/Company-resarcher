import re
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# TypedDict definitions for common data structures (Issue #053)
# These provide type hints for Dict[str, Any] in key areas
# =============================================================================


class SWOTAnalysis(TypedDict, total=False):
    """SWOT analysis structure from insight generator."""

    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]


class StrategicInsightsDict(TypedDict, total=False):
    """Strategic insights response from insight generator."""

    swot: SWOTAnalysis
    strategic_takeaways: List[str]
    executive_summary: str


class SearchResultDict(TypedDict, total=False):
    """Structure for search results from Tavily or local search."""

    url: str
    title: str
    content: str
    score: float


class TechStackDict(TypedDict, total=False):
    """Technology stack analysis data."""

    technologies: List[str]
    frameworks: List[str]
    analytics: List[str]
    hosting: List[str]


class CriticFeedbackDict(TypedDict, total=False):
    """Critic agent feedback structure."""

    score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    approved: bool


# =============================================================================
# Pydantic Response Models for JSON Validation (Issue #070)
# These validate LLM responses against expected schemas
# =============================================================================


class SWOTAnalysisModel(BaseModel):
    """Validated SWOT analysis from LLM."""

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class StrategicInsightsResponse(BaseModel):
    """Validated strategic insights response from insight generator."""

    swot: SWOTAnalysisModel = Field(default_factory=SWOTAnalysisModel)
    strategic_takeaways: List[str] = Field(default_factory=list)
    executive_summary: str = Field(default="N/A")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategicInsightsResponse":
        """Create from potentially malformed dict with defaults."""
        return cls(
            swot=SWOTAnalysisModel(**data.get("swot", {})),
            strategic_takeaways=data.get("strategic_takeaways", []),
            executive_summary=data.get("executive_summary", "N/A"),
        )


class CriticFeedbackResponse(BaseModel):
    """Validated critic feedback response."""

    score: float = Field(default=0.0, ge=0.0, le=10.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    approved: bool = Field(default=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticFeedbackResponse":
        """Create from potentially malformed dict with defaults."""
        return cls(
            score=data.get("score", 0.0),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
            approved=data.get("approved", False),
        )


# =============================================================================
# Original Pydantic Models
# =============================================================================

# Mapping from AI-generated source types to canonical types
# Defined at module level to avoid Pydantic class attribute access issues in validators
_SOURCE_TYPE_MAPPING: Dict[str, str] = {
    # Financial/business types
    "market_data": "financial",
    "industry_report": "financial",
    "company_profile": "financial",
    "business": "financial",
    "economic": "financial",
    # News types
    "news_article": "news",
    "press_release": "news",
    "blog": "news",
    "article": "news",
    # Social types
    "social_media": "social",
    "forum": "social",
    "review": "social",
    # Government/academic types
    "government": "web",
    "academic": "web",
    "research": "web",
    "legal": "web",
    # Error/fallback types
    "error": "web",
    "unknown": "web",
    "other": "web",
}

# Patterns that indicate error/blocked pages
_ERROR_TITLE_PATTERNS: List[str] = [
    r"just a moment",
    r"attention required",
    r"cloudflare",
    r"captcha",
    r"access.*denied",
    r"error.*request",
    r"error fetching",  # Browser tool error prefix
    r"failed to fetch",  # Alternative error prefix
    r"403 forbidden",
    r"404 not found",
    r"page not found",
    r"blocked",
    r"rate limit",
    r"too many requests",
    r"temporarily unavailable",
    r"service unavailable",
    r"please verify",
    r"human verification",
    r"robot check",
    r"security check",
    r"subscribe to continue",
    r"sign in required",
    r"login required",
    # Additional error patterns (Issue #3)
    r"technical difficulties",
    r"something went wrong",
    r"server error",
    r"internal server error",
    r"bad gateway",
    r"gateway timeout",
    r"connection refused",
    r"connection timed out",
    r"not available",
    r"under maintenance",
    r"coming soon",
    r"site.*unavailable",
]

# Dictionary/translation sites that should be filtered out (BUG-039)
_DICTIONARY_DOMAIN_PATTERNS: List[str] = [
    r"iciba\.com",
    r"dictionary\.cambridge\.org",
    r"baidu\.com/item",
    r"baike\.baidu\.com",
    r"dict\.cn",
    r"youdao\.com",
    r"translate\.google",
    r"deepl\.com/translator",
    r"linguee\.com",
    r"wordreference\.com",
    r"merriam-webster\.com",
    r"dictionary\.com",
    r"thesaurus\.com",
    r"urbandictionary\.com",
    r"wiktionary\.org",
    r"collinsdictionary\.com",
    r"oxfordlearnersdictionaries\.com",
    r"lexico\.com",
    r"reverso\.net",
    # Spam/irrelevant domains that return junk results
    r"zhihu\.com",  # Chinese Q&A site - returns irrelevant results for English queries
    r"douban\.com",  # Chinese social site
    r"weibo\.com",  # Chinese social media
    r"tianya\.cn",  # Chinese forum
    r"163\.com",  # Chinese portal
    r"sohu\.com",  # Chinese portal
    r"qq\.com/.*",  # QQ non-news pages
    r"csdn\.net",  # Chinese developer blog (often irrelevant)
    r"jianshu\.com",  # Chinese blog platform
    # Ad/tracking URLs that return no useful content
    r"bing\.com/aclick",  # Bing ad redirect URLs
    r"googleadservices\.com",  # Google ad redirects
    r"doubleclick\.net",  # Ad tracking
    r"clickserve\.dartsearch",  # Ad tracking
    r"go\.redirectingat\.com",  # Affiliate redirects
    r"tracking\.",  # Generic tracking domains
    r"/aclk\?",  # Google ad click URLs
    r"zhidao\.baidu\.com",  # Baidu Q&A - irrelevant for company research
]

# Common irrelevant patterns shared across industries
_COMMON_IRRELEVANT = [
    r"rotor\s+market",
    r"diagnostic\s+testing",
    r"medical\s+device",
    r"pharmaceutical",
]

# Irrelevant industry keywords to filter (BUG-045, Issue #10)
_IRRELEVANT_INDUSTRY_PATTERNS: Dict[str, List[str]] = {
    "telecommunications": _COMMON_IRRELEVANT
    + [
        r"industrial\s+equipment",
        r"manufacturing\s+sector",
        r"discount\s+retail",
        r"grocery\s+market",
        r"cryptocurrency",
        r"nft\s+market",
        r"real\s+estate\s+investment",
        # Issue #10: Filter beauty/personal care when researching telecom
        r"beauty.*personal\s*care",
        r"personal\s*care.*market",
        r"cosmetic",
        r"skincare",
        r"haircare",
        r"fragrance",
        r"makeup",
        r"personal\s*hygiene",
        r"toiletries",
        r"deodorant",
        r"shampoo",
        r"lotion",
    ],
    "banking": _COMMON_IRRELEVANT
    + [
        r"industrial\s+equipment",
        r"beauty.*personal\s*care",
        r"cosmetic",
    ],
    "technology": _COMMON_IRRELEVANT
    + [
        r"grocery\s+market",
        r"beauty.*personal\s*care",
        r"cosmetic",
    ],
}


class ResearchSource(BaseModel):
    """Represents a single source of information (webpage, PDF, etc.)"""

    url: str
    title: str
    content: str
    source_type: str = "web"  # web, pdf, news, etc.
    category: Optional[str] = None  # news, financial, etc.
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional data

    # FE-010: Source quality fields
    fetch_status: str = Field(default="success")  # success, blocked, paywall, error, empty
    content_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)  # 0-1 quality score

    @model_validator(mode="after")
    def fix_unknown_title(self) -> "ResearchSource":
        """CODE-002: Replace 'Unknown' title with domain name fallback.

        If title is 'Unknown' or empty, extract domain from URL as fallback.
        This ensures sources always have a meaningful title for display.
        """
        unknown_patterns = {"unknown", "unknown source", "", "untitled", "no title"}

        if self.title.lower().strip() in unknown_patterns:
            try:
                parsed = urlparse(self.url)
                domain = parsed.netloc or parsed.path.split("/")[0]
                # Clean up domain (remove www. prefix)
                if domain.startswith("www."):
                    domain = domain[4:]
                self.title = domain or "Source"
            except Exception:
                self.title = "Source"

        return self

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        """Validate and normalize source_type to canonical values.

        Maps AI-generated source types to canonical types instead of rejecting them.
        This prevents ~90% data loss from overly restrictive validation.
        """
        canonical = {"web", "pdf", "news", "financial", "social", "api"}

        # If already canonical, return as-is
        if v in canonical:
            return v

        # Normalize: lowercase and strip
        v_normalized = v.lower().strip()

        # Check if normalized version is canonical
        if v_normalized in canonical:
            return v_normalized

        # Map to canonical type, default to "web" if not found
        mapped = _SOURCE_TYPE_MAPPING.get(v_normalized, "web")
        return mapped

    def is_error_source(self) -> bool:
        """Check if this source is an error/blocked page.

        Returns True if the source title matches error patterns or content is too short.
        """
        title_lower = self.title.lower()

        # Check title against error patterns
        for pattern in _ERROR_TITLE_PATTERNS:
            if re.search(pattern, title_lower):
                return True

        # Check if content is too short (likely failed to load)
        if len(self.content.strip()) < 100:
            return True

        return False

    def is_dictionary_site(self) -> bool:
        """Check if this source is a dictionary/translation site (BUG-039).

        Returns True if the URL matches dictionary domain patterns.
        """
        url_lower = self.url.lower()
        for pattern in _DICTIONARY_DOMAIN_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        return False

    def is_irrelevant_industry(self, target_industry: Optional[str] = None) -> bool:
        """Check if this source is from an irrelevant industry (BUG-045).

        Args:
            target_industry: The industry we're researching (e.g., "telecommunications")

        Returns True if the source mentions industries unrelated to the target.
        """
        if not target_industry:
            return False

        target_lower = target_industry.lower()
        text_lower = f"{self.title} {self.content[:500]}".lower()

        # Get patterns for this industry
        patterns = _IRRELEVANT_INDUSTRY_PATTERNS.get(target_lower, _COMMON_IRRELEVANT)

        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def is_irrelevant_foreign_source(
        self, target_country_tld: Optional[str] = None
    ) -> bool:
        """Check if this source is from an irrelevant foreign country.

        Filters out results from countries that typically don't provide
        relevant results when researching companies in other regions.
        Global business domains (e.g., mordorintelligence.com) are never filtered.

        Args:
            target_country_tld: The country TLD we're researching (e.g., "py")

        Returns:
            True if the source should be filtered out.
        """
        from ..utils.url_utils import is_irrelevant_foreign_source

        return is_irrelevant_foreign_source(self.url, target_country_tld)

    def get_geographic_relevance_score(
        self, target_country_tld: Optional[str] = None
    ) -> float:
        """Calculate geographic relevance score for this source.

        Higher scores indicate more geographically relevant sources.
        Scores range from 0.0 to 1.0.

        Args:
            target_country_tld: The country TLD we're researching (e.g., "py")

        Returns:
            Relevance score from 0.0 to 1.0
        """
        from ..utils.url_utils import calculate_source_relevance_score

        return calculate_source_relevance_score(self.url, target_country_tld)

    def is_usable(
        self,
        target_industry: Optional[str] = None,
        target_country_tld: Optional[str] = None,
    ) -> bool:
        """Check if this source is usable for reports.

        Returns True if the source has valid content, is not an error page,
        is not a dictionary site, is not from an irrelevant industry,
        and is not from an irrelevant foreign country.

        Args:
            target_industry: The industry we're researching (e.g., "telecommunications")
            target_country_tld: The country TLD we're researching (e.g., "py")
        """
        if self.is_error_source():
            return False
        if self.is_dictionary_site():
            return False
        if self.is_irrelevant_industry(target_industry):
            return False
        if self.is_irrelevant_foreign_source(target_country_tld):
            return False
        return True


class CompanyProfile(BaseModel):
    """Basic input information about a company"""

    name: str = Field(..., min_length=1, max_length=500)
    website: Optional[str] = Field(default=None, max_length=2000)
    industry: Optional[str] = Field(default=None, max_length=200)
    country: str = Field(default="Global", max_length=100)
    description: Optional[str] = Field(default=None, max_length=5000)
    target_audience: Optional[str] = Field(default=None, max_length=1000)
    competitors: List[str] = Field(default_factory=list, max_length=50)
    # Stock ticker for public companies (INT-002: Alpha Vantage integration)
    ticker: Optional[str] = Field(default=None, max_length=20)
    exchange: Optional[str] = Field(default=None, max_length=50)
    # Parent company ticker for subsidiaries
    parent_ticker: Optional[str] = Field(default=None, max_length=20)
    parent_company: Optional[str] = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty or whitespace")
        return v

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not (v.startswith("http://") or v.startswith("https://")):
            v = f"https://{v}"
        return v

    @field_validator("competitors")
    @classmethod
    def validate_competitors(cls, v: List[str]) -> List[str]:
        return [c.strip() for c in v if c and c.strip()]

    def with_country_from_url(self) -> "CompanyProfile":
        """
        Return a new CompanyProfile with country extracted from website URL.

        If country is already set to something other than "Global", keeps it.
        If website has a country TLD, extracts and sets the country.

        Returns:
            New CompanyProfile with country populated.
        """
        # Don't override if country is already set
        if self.country and self.country != "Global":
            return self

        if not self.website:
            return self

        from ..utils.url_utils import extract_country_from_url

        detected_country = extract_country_from_url(self.website)
        if detected_country:
            return self.model_copy(update={"country": detected_country})

        return self

    def get_country_tld(self) -> Optional[str]:
        """
        Get the country TLD from the website URL.

        Returns:
            Two-letter country code (e.g., "py") or None.
        """
        if not self.website:
            return None

        from ..utils.url_utils import extract_country_tld

        return extract_country_tld(self.website)

    def with_inferred_industry(self) -> "CompanyProfile":
        """
        Return a new CompanyProfile with industry inferred from URL/name.

        If industry is already set, keeps it.
        Uses domain patterns and company name to infer industry (BUG-050).

        Returns:
            New CompanyProfile with industry populated if detected.
        """
        # Don't override if industry is already set
        if self.industry:
            return self

        from ..utils.url_utils import infer_industry

        detected_industry = infer_industry(self.website or "", self.name)
        if detected_industry:
            return self.model_copy(update={"industry": detected_industry})

        return self

    def with_enriched_context(self) -> "CompanyProfile":
        """
        Return a new CompanyProfile with both country and industry enriched.

        Convenience method that applies both with_country_from_url() and
        with_inferred_industry() for full context enrichment.

        Returns:
            New CompanyProfile with country and industry populated if detected.
        """
        return self.with_country_from_url().with_inferred_industry()

    def get_effective_ticker(self) -> Optional[str]:
        """
        Get the effective stock ticker for financial data lookup.

        Returns own ticker if available, otherwise parent_ticker.
        This allows fetching financial data for subsidiaries via their parent.

        Returns:
            Stock ticker symbol or None if not available.
        """
        return self.ticker or self.parent_ticker

    def has_financial_data_available(self) -> bool:
        """
        Check if financial data can be fetched for this company.

        Returns True if either the company or its parent has a stock ticker.
        """
        return bool(self.get_effective_ticker())

    def is_subsidiary(self) -> bool:
        """Check if this company is a subsidiary (has parent ticker but no own ticker)."""
        return bool(self.parent_ticker and not self.ticker)


class ResearchContext(BaseModel):
    """
    Aggregated research data from specialist agents for insight generation.

    .. deprecated::
        Use TypedResearchContext from src.core.models instead for type safety.
        This class is maintained for backward compatibility.
    """

    financial_data: Dict[str, Any] = Field(default_factory=dict)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    competitor_data: Dict[str, Any] = Field(default_factory=dict)
    brand_data: Dict[str, Any] = Field(default_factory=dict)


class ResearchPhaseResult(BaseModel):
    """Result of a specific research phase (e.g., Market Analysis)"""

    phase_name: str
    markdown_content: str
    sources: List[ResearchSource]
    key_findings: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    evaluation: Optional[Dict[str, Any]] = None


class FullCompanyResearch(BaseModel):
    """The complete research dossier for a company"""

    company: CompanyProfile
    phases: Dict[str, ResearchPhaseResult] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    output_path: str
