"""
Source Registry - Centralized list of priority sources, blacklists, and domain categories.

This module provides easy-to-maintain lists of:
- Priority sources to ALWAYS check (by research type)
- Sources to check IF RELEVANT (by industry/topic)
- Blacklisted domains to NEVER use
- Domain authority scores

Usage:
    from src.core.source_registry import (
        get_priority_sources,
        get_relevant_sources,
        is_blacklisted,
        get_domain_authority,
    )

    # Get sources for market research
    market_sources = get_priority_sources("market")

    # Get telecom-specific sources
    telecom_sources = get_relevant_sources("telecom")
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum


# =============================================================================
# PRIORITY SOURCES - ALWAYS CHECK THESE
# =============================================================================

class ResearchType(str, Enum):
    """Research types for source categorization."""
    MARKET = "market"
    FINANCIAL = "financial"
    COMPETITOR = "competitor"
    BRAND = "brand"
    SALES = "sales"
    ALL = "all"


@dataclass
class SourceInfo:
    """Information about a source domain."""
    domain: str
    name: str
    description: str
    authority_score: float  # 0.0 - 1.0
    requires_subscription: bool = False
    api_available: bool = False


# -----------------------------------------------------------------------------
# TIER 1: PREMIUM RESEARCH SOURCES (Always check first)
# -----------------------------------------------------------------------------

PREMIUM_MARKET_RESEARCH: Dict[str, SourceInfo] = {
    # Market Size & Industry Reports
    "statista.com": SourceInfo(
        domain="statista.com",
        name="Statista",
        description="Market statistics, industry reports, forecasts",
        authority_score=1.0,
        requires_subscription=True,
    ),
    "mordorintelligence.com": SourceInfo(
        domain="mordorintelligence.com",
        name="Mordor Intelligence",
        description="Industry reports, market size, forecasts, competitive landscape",
        authority_score=0.98,
    ),
    "globaldata.com": SourceInfo(
        domain="globaldata.com",
        name="GlobalData",
        description="Market intelligence, company profiles, deal analytics",
        authority_score=0.98,
        requires_subscription=True,
    ),
    "gartner.com": SourceInfo(
        domain="gartner.com",
        name="Gartner",
        description="Tech market research, Magic Quadrants, analyst reports",
        authority_score=0.97,
        requires_subscription=True,
    ),
    "forrester.com": SourceInfo(
        domain="forrester.com",
        name="Forrester",
        description="Tech research, Wave reports, customer experience",
        authority_score=0.95,
        requires_subscription=True,
    ),
    "ibisworld.com": SourceInfo(
        domain="ibisworld.com",
        name="IBISWorld",
        description="Industry research, market reports, risk ratings",
        authority_score=0.95,
        requires_subscription=True,
    ),
    "euromonitor.com": SourceInfo(
        domain="euromonitor.com",
        name="Euromonitor",
        description="Consumer market research, industry analysis",
        authority_score=0.94,
        requires_subscription=True,
    ),
    "grandviewresearch.com": SourceInfo(
        domain="grandviewresearch.com",
        name="Grand View Research",
        description="Market research reports, industry analysis",
        authority_score=0.92,
    ),
    "marketsandmarkets.com": SourceInfo(
        domain="marketsandmarkets.com",
        name="MarketsandMarkets",
        description="B2B market research, technology forecasts",
        authority_score=0.91,
    ),
    "researchandmarkets.com": SourceInfo(
        domain="researchandmarkets.com",
        name="Research and Markets",
        description="Market research aggregator, industry reports",
        authority_score=0.90,
    ),
}

# -----------------------------------------------------------------------------
# TIER 2: CONSULTING & STRATEGY (Insights, trends, analysis)
# -----------------------------------------------------------------------------

CONSULTING_SOURCES: Dict[str, SourceInfo] = {
    "mckinsey.com": SourceInfo(
        domain="mckinsey.com",
        name="McKinsey & Company",
        description="Strategy insights, industry perspectives, research",
        authority_score=0.97,
    ),
    "bcg.com": SourceInfo(
        domain="bcg.com",
        name="Boston Consulting Group",
        description="Strategy research, industry analysis",
        authority_score=0.96,
    ),
    "bain.com": SourceInfo(
        domain="bain.com",
        name="Bain & Company",
        description="Strategy insights, M&A analysis",
        authority_score=0.95,
    ),
    "deloitte.com": SourceInfo(
        domain="deloitte.com",
        name="Deloitte",
        description="Industry insights, regulatory updates, tech trends",
        authority_score=0.96,
    ),
    "pwc.com": SourceInfo(
        domain="pwc.com",
        name="PwC",
        description="Industry surveys, CEO surveys, market insights",
        authority_score=0.96,
    ),
    "ey.com": SourceInfo(
        domain="ey.com",
        name="EY (Ernst & Young)",
        description="Industry insights, transaction analysis",
        authority_score=0.95,
    ),
    "kpmg.com": SourceInfo(
        domain="kpmg.com",
        name="KPMG",
        description="Industry insights, regulatory, technology",
        authority_score=0.95,
    ),
    "accenture.com": SourceInfo(
        domain="accenture.com",
        name="Accenture",
        description="Technology insights, digital transformation",
        authority_score=0.93,
    ),
}

# -----------------------------------------------------------------------------
# TIER 3: FINANCIAL NEWS & DATA
# -----------------------------------------------------------------------------

FINANCIAL_NEWS_SOURCES: Dict[str, SourceInfo] = {
    "reuters.com": SourceInfo(
        domain="reuters.com",
        name="Reuters",
        description="Breaking news, financial data, company news",
        authority_score=0.94,
    ),
    "bloomberg.com": SourceInfo(
        domain="bloomberg.com",
        name="Bloomberg",
        description="Financial news, market data, company profiles",
        authority_score=0.94,
        requires_subscription=True,
    ),
    "ft.com": SourceInfo(
        domain="ft.com",
        name="Financial Times",
        description="Business news, analysis, company profiles",
        authority_score=0.93,
        requires_subscription=True,
    ),
    "wsj.com": SourceInfo(
        domain="wsj.com",
        name="Wall Street Journal",
        description="Business news, market analysis",
        authority_score=0.93,
        requires_subscription=True,
    ),
    "economist.com": SourceInfo(
        domain="economist.com",
        name="The Economist",
        description="Economic analysis, industry insights",
        authority_score=0.92,
        requires_subscription=True,
    ),
    "forbes.com": SourceInfo(
        domain="forbes.com",
        name="Forbes",
        description="Business news, company rankings, executive profiles",
        authority_score=0.88,
    ),
    "businessinsider.com": SourceInfo(
        domain="businessinsider.com",
        name="Business Insider",
        description="Business news, tech coverage",
        authority_score=0.85,
    ),
    "cnbc.com": SourceInfo(
        domain="cnbc.com",
        name="CNBC",
        description="Financial news, market data, earnings",
        authority_score=0.85,
    ),
}

# -----------------------------------------------------------------------------
# TIER 4: COMPANY & BUSINESS DATA
# -----------------------------------------------------------------------------

COMPANY_DATA_SOURCES: Dict[str, SourceInfo] = {
    "linkedin.com": SourceInfo(
        domain="linkedin.com",
        name="LinkedIn",
        description="Company profiles, employee data, job postings",
        authority_score=0.84,
    ),
    "crunchbase.com": SourceInfo(
        domain="crunchbase.com",
        name="Crunchbase",
        description="Startup data, funding rounds, investor info",
        authority_score=0.83,
        api_available=True,
    ),
    "cbinsights.com": SourceInfo(
        domain="cbinsights.com",
        name="CB Insights",
        description="Tech market intelligence, unicorn tracker",
        authority_score=0.82,
        requires_subscription=True,
    ),
    "pitchbook.com": SourceInfo(
        domain="pitchbook.com",
        name="PitchBook",
        description="Private market data, VC/PE deals",
        authority_score=0.82,
        requires_subscription=True,
    ),
    "zoominfo.com": SourceInfo(
        domain="zoominfo.com",
        name="ZoomInfo",
        description="B2B contact data, company intelligence",
        authority_score=0.80,
        requires_subscription=True,
    ),
    "dnb.com": SourceInfo(
        domain="dnb.com",
        name="Dun & Bradstreet",
        description="Business credit, company data, D-U-N-S",
        authority_score=0.80,
        requires_subscription=True,
    ),
    "owler.com": SourceInfo(
        domain="owler.com",
        name="Owler",
        description="Competitive intelligence, company news",
        authority_score=0.75,
    ),
    "craft.co": SourceInfo(
        domain="craft.co",
        name="Craft",
        description="Company profiles, org charts, tech stacks",
        authority_score=0.74,
    ),
}

# -----------------------------------------------------------------------------
# TIER 5: FINANCIAL DATA & FILINGS
# -----------------------------------------------------------------------------

FINANCIAL_DATA_SOURCES: Dict[str, SourceInfo] = {
    "sec.gov": SourceInfo(
        domain="sec.gov",
        name="SEC EDGAR",
        description="US public company filings (10-K, 10-Q, 8-K)",
        authority_score=0.95,
    ),
    "finance.yahoo.com": SourceInfo(
        domain="finance.yahoo.com",
        name="Yahoo Finance",
        description="Stock quotes, financials, analyst ratings",
        authority_score=0.80,
    ),
    "tradingview.com": SourceInfo(
        domain="tradingview.com",
        name="TradingView",
        description="Charts, technical analysis, financials",
        authority_score=0.78,
    ),
    "investing.com": SourceInfo(
        domain="investing.com",
        name="Investing.com",
        description="Stock quotes, economic calendar, news",
        authority_score=0.76,
    ),
    "morningstar.com": SourceInfo(
        domain="morningstar.com",
        name="Morningstar",
        description="Investment research, fund ratings",
        authority_score=0.85,
    ),
    "seekingalpha.com": SourceInfo(
        domain="seekingalpha.com",
        name="Seeking Alpha",
        description="Investment analysis, earnings coverage",
        authority_score=0.72,
    ),
}

# -----------------------------------------------------------------------------
# TIER 6: PRESS RELEASES & NEWS WIRES
# -----------------------------------------------------------------------------

NEWS_WIRE_SOURCES: Dict[str, SourceInfo] = {
    "prnewswire.com": SourceInfo(
        domain="prnewswire.com",
        name="PR Newswire",
        description="Press releases, corporate announcements",
        authority_score=0.60,
    ),
    "businesswire.com": SourceInfo(
        domain="businesswire.com",
        name="Business Wire",
        description="Press releases, regulatory filings",
        authority_score=0.60,
    ),
    "globenewswire.com": SourceInfo(
        domain="globenewswire.com",
        name="GlobeNewswire",
        description="Press releases, corporate news",
        authority_score=0.58,
    ),
    "accesswire.com": SourceInfo(
        domain="accesswire.com",
        name="ACCESSWIRE",
        description="Press releases",
        authority_score=0.55,
    ),
}


# =============================================================================
# INDUSTRY-SPECIFIC SOURCES - CHECK IF RELEVANT
# =============================================================================

TELECOM_SOURCES: Dict[str, SourceInfo] = {
    "gsma.com": SourceInfo(
        domain="gsma.com",
        name="GSMA",
        description="Mobile industry association, 5G reports, MWC",
        authority_score=0.92,
    ),
    "itu.int": SourceInfo(
        domain="itu.int",
        name="ITU",
        description="UN telecom agency, global standards, statistics",
        authority_score=0.90,
    ),
    "telegeography.com": SourceInfo(
        domain="telegeography.com",
        name="TeleGeography",
        description="Telecom market research, submarine cables, pricing",
        authority_score=0.88,
    ),
    "analysysmason.com": SourceInfo(
        domain="analysysmason.com",
        name="Analysys Mason",
        description="Telecom consulting, market forecasts",
        authority_score=0.87,
    ),
    "fiercewireless.com": SourceInfo(
        domain="fiercewireless.com",
        name="Fierce Wireless",
        description="Wireless industry news, 5G coverage",
        authority_score=0.77,
    ),
    "lightreading.com": SourceInfo(
        domain="lightreading.com",
        name="Light Reading",
        description="Telecom news, network infrastructure",
        authority_score=0.76,
    ),
    "rcrwireless.com": SourceInfo(
        domain="rcrwireless.com",
        name="RCR Wireless",
        description="Wireless technology news",
        authority_score=0.74,
    ),
    "commsupdate.com": SourceInfo(
        domain="commsupdate.com",
        name="CommsUpdate",
        description="Telecom news by country, operator updates",
        authority_score=0.73,
    ),
    "totaltele.com": SourceInfo(
        domain="totaltele.com",
        name="Total Telecom",
        description="Telecom industry news, events",
        authority_score=0.72,
    ),
}

TECHNOLOGY_SOURCES: Dict[str, SourceInfo] = {
    "techcrunch.com": SourceInfo(
        domain="techcrunch.com",
        name="TechCrunch",
        description="Startup news, funding, tech trends",
        authority_score=0.82,
    ),
    "wired.com": SourceInfo(
        domain="wired.com",
        name="Wired",
        description="Tech culture, gadgets, science",
        authority_score=0.80,
    ),
    "theverge.com": SourceInfo(
        domain="theverge.com",
        name="The Verge",
        description="Tech news, reviews, culture",
        authority_score=0.78,
    ),
    "arstechnica.com": SourceInfo(
        domain="arstechnica.com",
        name="Ars Technica",
        description="Tech news, in-depth analysis",
        authority_score=0.80,
    ),
    "zdnet.com": SourceInfo(
        domain="zdnet.com",
        name="ZDNet",
        description="Enterprise tech, IT news",
        authority_score=0.76,
    ),
    "venturebeat.com": SourceInfo(
        domain="venturebeat.com",
        name="VentureBeat",
        description="AI news, gaming, enterprise tech",
        authority_score=0.75,
    ),
    "stackshare.io": SourceInfo(
        domain="stackshare.io",
        name="StackShare",
        description="Tech stacks, developer tools",
        authority_score=0.73,
    ),
    "g2.com": SourceInfo(
        domain="g2.com",
        name="G2",
        description="Software reviews, comparisons",
        authority_score=0.72,
    ),
}

BANKING_FINANCE_SOURCES: Dict[str, SourceInfo] = {
    "bankingdive.com": SourceInfo(
        domain="bankingdive.com",
        name="Banking Dive",
        description="Banking industry news",
        authority_score=0.78,
    ),
    "americanbanker.com": SourceInfo(
        domain="americanbanker.com",
        name="American Banker",
        description="US banking news, fintech",
        authority_score=0.80,
    ),
    "finextra.com": SourceInfo(
        domain="finextra.com",
        name="Finextra",
        description="Fintech news, payments, banking tech",
        authority_score=0.77,
    ),
    "pymnts.com": SourceInfo(
        domain="pymnts.com",
        name="PYMNTS",
        description="Payments industry news, research",
        authority_score=0.75,
    ),
    "bis.org": SourceInfo(
        domain="bis.org",
        name="BIS",
        description="Bank for International Settlements, central bank reports",
        authority_score=0.92,
    ),
}

HEALTHCARE_SOURCES: Dict[str, SourceInfo] = {
    "fiercehealthcare.com": SourceInfo(
        domain="fiercehealthcare.com",
        name="Fierce Healthcare",
        description="Healthcare industry news",
        authority_score=0.78,
    ),
    "healthcaredive.com": SourceInfo(
        domain="healthcaredive.com",
        name="Healthcare Dive",
        description="Healthcare industry news, policy",
        authority_score=0.77,
    ),
    "mobihealthnews.com": SourceInfo(
        domain="mobihealthnews.com",
        name="MobiHealthNews",
        description="Digital health, health tech",
        authority_score=0.75,
    ),
    "beckershospitalreview.com": SourceInfo(
        domain="beckershospitalreview.com",
        name="Becker's Hospital Review",
        description="Hospital news, healthcare management",
        authority_score=0.76,
    ),
}

RETAIL_ECOMMERCE_SOURCES: Dict[str, SourceInfo] = {
    "retaildive.com": SourceInfo(
        domain="retaildive.com",
        name="Retail Dive",
        description="Retail industry news",
        authority_score=0.78,
    ),
    "digitalcommerce360.com": SourceInfo(
        domain="digitalcommerce360.com",
        name="Digital Commerce 360",
        description="E-commerce news, rankings",
        authority_score=0.76,
    ),
    "emarketer.com": SourceInfo(
        domain="emarketer.com",
        name="eMarketer",
        description="Digital marketing, e-commerce data",
        authority_score=0.85,
        requires_subscription=True,
    ),
    "nrf.com": SourceInfo(
        domain="nrf.com",
        name="NRF",
        description="National Retail Federation, retail data",
        authority_score=0.80,
    ),
}

ENERGY_SOURCES: Dict[str, SourceInfo] = {
    "iea.org": SourceInfo(
        domain="iea.org",
        name="IEA",
        description="International Energy Agency, energy data",
        authority_score=0.93,
    ),
    "eia.gov": SourceInfo(
        domain="eia.gov",
        name="EIA",
        description="US Energy Information Administration",
        authority_score=0.92,
    ),
    "spglobal.com": SourceInfo(
        domain="spglobal.com",
        name="S&P Global",
        description="Energy data, commodity prices",
        authority_score=0.90,
    ),
    "woodmac.com": SourceInfo(
        domain="woodmac.com",
        name="Wood Mackenzie",
        description="Energy research, renewables",
        authority_score=0.88,
    ),
    "oilprice.com": SourceInfo(
        domain="oilprice.com",
        name="OilPrice.com",
        description="Energy news, oil prices",
        authority_score=0.70,
    ),
}

# Latin America specific sources
LATAM_SOURCES: Dict[str, SourceInfo] = {
    "bnamericas.com": SourceInfo(
        domain="bnamericas.com",
        name="BNamericas",
        description="Latin America business intelligence",
        authority_score=0.82,
        requires_subscription=True,
    ),
    "dataxis.com": SourceInfo(
        domain="dataxis.com",
        name="Dataxis",
        description="LATAM telecom & media data",
        authority_score=0.80,
    ),
    "eleconomista.com.mx": SourceInfo(
        domain="eleconomista.com.mx",
        name="El Economista (MX)",
        description="Mexican business news",
        authority_score=0.75,
    ),
    "infobae.com": SourceInfo(
        domain="infobae.com",
        name="Infobae",
        description="LATAM news portal",
        authority_score=0.72,
    ),
    "americaeconomia.com": SourceInfo(
        domain="americaeconomia.com",
        name="America Economia",
        description="LATAM business news",
        authority_score=0.74,
    ),
}


# =============================================================================
# BLACKLISTED DOMAINS - NEVER USE THESE
# =============================================================================

BLACKLISTED_DOMAINS: Set[str] = {
    # Low quality / User-generated content
    "reddit.com",
    "quora.com",
    "answers.yahoo.com",
    "ask.com",
    "ehow.com",
    "wikihow.com",  # Can be useful but often generic
    "reference.com",
    "about.com",

    # Content farms / SEO spam
    "buzzfeed.com",
    "huffpost.com",  # Often clickbait
    "dailymail.co.uk",
    "mirror.co.uk",
    "thesun.co.uk",
    "express.co.uk",

    # Paywalled with no value
    "scribd.com",
    "academia.edu",  # Requires login, limited content

    # AI-generated / Aggregators with no original content
    "similarweb.com",  # Data often inaccurate without subscription

    # Press release spam sites
    "prlog.org",
    "pr.com",
    "prweb.com",
    "newswire.com",
    "marketwatch.com",  # Often just reprints PRs

    # Social media (not useful for research)
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
    "tumblr.com",

    # Job boards (not relevant for company research)
    "indeed.com",
    "glassdoor.com",
    "monster.com",
    "careerbuilder.com",
    "ziprecruiter.com",

    # Generic/low value
    "yelp.com",
    "trustpilot.com",  # Review site, limited business data
    "bbb.org",  # US-centric, limited data

    # Potentially dangerous / unreliable
    "4chan.org",
    "8kun.top",

    # Spam domains often in search results
    "amazonaws.com",  # Usually redirects
    "cloudfront.net",  # CDN, not a source
    "googleusercontent.com",  # Not a source
}

# Domains to deprioritize (not blacklist, but lower score)
LOW_PRIORITY_DOMAINS: Set[str] = {
    "medium.com",  # Quality varies wildly
    "substack.com",  # Opinion pieces, not facts
    "wordpress.com",  # Generic blogs
    "blogspot.com",
    "weebly.com",
    "wix.com",
    "squarespace.com",
    "tumblr.com",
    "wikipedia.org",  # Good for overview, not primary source
    "investopedia.com",  # Good for definitions, not research
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_priority_sources(research_type: str) -> Dict[str, SourceInfo]:
    """
    Get priority sources for a specific research type.

    Args:
        research_type: Type of research (market, financial, competitor, brand, sales, all)

    Returns:
        Dictionary of domain -> SourceInfo for priority sources
    """
    # Base sources for all research types
    base_sources = {
        **PREMIUM_MARKET_RESEARCH,
        **CONSULTING_SOURCES,
        **FINANCIAL_NEWS_SOURCES,
    }

    if research_type == "all":
        return {
            **base_sources,
            **COMPANY_DATA_SOURCES,
            **FINANCIAL_DATA_SOURCES,
            **NEWS_WIRE_SOURCES,
        }

    if research_type == "market":
        return {
            **base_sources,
        }

    if research_type == "financial":
        return {
            **base_sources,
            **FINANCIAL_DATA_SOURCES,
        }

    if research_type == "competitor":
        return {
            **base_sources,
            **COMPANY_DATA_SOURCES,
        }

    if research_type == "brand":
        return {
            **CONSULTING_SOURCES,
            **FINANCIAL_NEWS_SOURCES,
            **NEWS_WIRE_SOURCES,
        }

    if research_type == "sales":
        return {
            **COMPANY_DATA_SOURCES,
            **base_sources,
        }

    return base_sources


def get_relevant_sources(industry: str) -> Dict[str, SourceInfo]:
    """
    Get industry-specific sources.

    Args:
        industry: Industry name (telecom, technology, banking, healthcare, etc.)

    Returns:
        Dictionary of domain -> SourceInfo for relevant sources
    """
    industry_lower = industry.lower()

    industry_mapping = {
        "telecom": TELECOM_SOURCES,
        "telecommunications": TELECOM_SOURCES,
        "wireless": TELECOM_SOURCES,
        "mobile": TELECOM_SOURCES,
        "5g": TELECOM_SOURCES,
        "technology": TECHNOLOGY_SOURCES,
        "tech": TECHNOLOGY_SOURCES,
        "software": TECHNOLOGY_SOURCES,
        "saas": TECHNOLOGY_SOURCES,
        "banking": BANKING_FINANCE_SOURCES,
        "finance": BANKING_FINANCE_SOURCES,
        "fintech": BANKING_FINANCE_SOURCES,
        "insurance": BANKING_FINANCE_SOURCES,
        "healthcare": HEALTHCARE_SOURCES,
        "pharma": HEALTHCARE_SOURCES,
        "medical": HEALTHCARE_SOURCES,
        "retail": RETAIL_ECOMMERCE_SOURCES,
        "ecommerce": RETAIL_ECOMMERCE_SOURCES,
        "e-commerce": RETAIL_ECOMMERCE_SOURCES,
        "energy": ENERGY_SOURCES,
        "oil": ENERGY_SOURCES,
        "gas": ENERGY_SOURCES,
        "utilities": ENERGY_SOURCES,
        "latam": LATAM_SOURCES,
        "latin america": LATAM_SOURCES,
        "paraguay": LATAM_SOURCES,
        "argentina": LATAM_SOURCES,
        "brazil": LATAM_SOURCES,
        "mexico": LATAM_SOURCES,
    }

    return industry_mapping.get(industry_lower, {})


def get_regional_sources(region: str) -> Dict[str, SourceInfo]:
    """
    Get regional sources.

    Args:
        region: Region name (latam, europe, asia, etc.)

    Returns:
        Dictionary of domain -> SourceInfo
    """
    if region.lower() in ["latam", "latin america", "south america"]:
        return LATAM_SOURCES

    # Add more regions as needed
    return {}


def is_blacklisted(domain: str) -> bool:
    """
    Check if a domain is blacklisted.

    Args:
        domain: Domain to check (e.g., "reddit.com")

    Returns:
        True if blacklisted, False otherwise
    """
    domain_lower = domain.lower()

    # Check exact match
    if domain_lower in BLACKLISTED_DOMAINS:
        return True

    # Check if subdomain of blacklisted domain
    for blacklisted in BLACKLISTED_DOMAINS:
        if domain_lower.endswith(f".{blacklisted}"):
            return True

    return False


def is_low_priority(domain: str) -> bool:
    """
    Check if a domain is low priority (not blacklisted but deprioritized).

    Args:
        domain: Domain to check

    Returns:
        True if low priority, False otherwise
    """
    domain_lower = domain.lower()
    return domain_lower in LOW_PRIORITY_DOMAINS or any(
        domain_lower.endswith(f".{d}") for d in LOW_PRIORITY_DOMAINS
    )


def get_domain_authority(domain: str) -> float:
    """
    Get authority score for a domain.

    Args:
        domain: Domain to check

    Returns:
        Authority score (0.0 - 1.0), default 0.5 for unknown
    """
    domain_lower = domain.lower()

    # Check all source dictionaries
    all_sources = {
        **PREMIUM_MARKET_RESEARCH,
        **CONSULTING_SOURCES,
        **FINANCIAL_NEWS_SOURCES,
        **COMPANY_DATA_SOURCES,
        **FINANCIAL_DATA_SOURCES,
        **NEWS_WIRE_SOURCES,
        **TELECOM_SOURCES,
        **TECHNOLOGY_SOURCES,
        **BANKING_FINANCE_SOURCES,
        **HEALTHCARE_SOURCES,
        **RETAIL_ECOMMERCE_SOURCES,
        **ENERGY_SOURCES,
        **LATAM_SOURCES,
    }

    if domain_lower in all_sources:
        return all_sources[domain_lower].authority_score

    # Check for subdomain
    for source_domain, info in all_sources.items():
        if domain_lower.endswith(f".{source_domain}"):
            return info.authority_score * 0.95

    # Check if blacklisted or low priority
    if is_blacklisted(domain_lower):
        return 0.1

    if is_low_priority(domain_lower):
        return 0.35

    # Default for unknown domains
    return 0.5


def get_all_priority_domains() -> Set[str]:
    """Get all domains that should be prioritized in search results."""
    all_sources = {
        **PREMIUM_MARKET_RESEARCH,
        **CONSULTING_SOURCES,
        **FINANCIAL_NEWS_SOURCES,
        **COMPANY_DATA_SOURCES,
        **FINANCIAL_DATA_SOURCES,
    }
    return set(all_sources.keys())


def get_search_boost_domains(research_type: str, industry: str = None) -> Set[str]:
    """
    Get domains that should be boosted in search results.

    Args:
        research_type: Type of research
        industry: Optional industry for industry-specific sources

    Returns:
        Set of domains to boost
    """
    priority = get_priority_sources(research_type)
    domains = set(priority.keys())

    if industry:
        relevant = get_relevant_sources(industry)
        domains.update(relevant.keys())

    return domains


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ResearchType",
    # Data classes
    "SourceInfo",
    # Source dictionaries
    "PREMIUM_MARKET_RESEARCH",
    "CONSULTING_SOURCES",
    "FINANCIAL_NEWS_SOURCES",
    "COMPANY_DATA_SOURCES",
    "FINANCIAL_DATA_SOURCES",
    "NEWS_WIRE_SOURCES",
    "TELECOM_SOURCES",
    "TECHNOLOGY_SOURCES",
    "BANKING_FINANCE_SOURCES",
    "HEALTHCARE_SOURCES",
    "RETAIL_ECOMMERCE_SOURCES",
    "ENERGY_SOURCES",
    "LATAM_SOURCES",
    # Blacklists
    "BLACKLISTED_DOMAINS",
    "LOW_PRIORITY_DOMAINS",
    # Functions
    "get_priority_sources",
    "get_relevant_sources",
    "get_regional_sources",
    "is_blacklisted",
    "is_low_priority",
    "get_domain_authority",
    "get_all_priority_domains",
    "get_search_boost_domains",
]
