"""
URL Utilities for country extraction and URL normalization.

Fixes BUG-049 (wrong country results) and BUG-052 (source deduplication).
"""

from typing import Optional
from urllib.parse import urlparse

# Country code TLD to country name mapping
COUNTRY_TLD_MAP = {
    # Latin America
    "py": "Paraguay",
    "ar": "Argentina",
    "br": "Brazil",
    "mx": "Mexico",
    "co": "Colombia",
    "cl": "Chile",
    "pe": "Peru",
    "uy": "Uruguay",
    "ec": "Ecuador",
    "ve": "Venezuela",
    "bo": "Bolivia",
    "cr": "Costa Rica",
    "pa": "Panama",
    "do": "Dominican Republic",
    "gt": "Guatemala",
    "hn": "Honduras",
    "sv": "El Salvador",
    "ni": "Nicaragua",
    "cu": "Cuba",
    "pr": "Puerto Rico",
    # Europe
    "uk": "United Kingdom",
    "de": "Germany",
    "fr": "France",
    "es": "Spain",
    "it": "Italy",
    "nl": "Netherlands",
    "be": "Belgium",
    "pt": "Portugal",
    "at": "Austria",
    "ch": "Switzerland",
    "pl": "Poland",
    "se": "Sweden",
    "no": "Norway",
    "dk": "Denmark",
    "fi": "Finland",
    "ie": "Ireland",
    "cz": "Czech Republic",
    "gr": "Greece",
    "hu": "Hungary",
    "ro": "Romania",
    "bg": "Bulgaria",
    "hr": "Croatia",
    "sk": "Slovakia",
    "si": "Slovenia",
    "rs": "Serbia",
    "ua": "Ukraine",
    "ru": "Russia",
    # Asia Pacific
    "jp": "Japan",
    "cn": "China",
    "kr": "South Korea",
    "in": "India",
    "au": "Australia",
    "nz": "New Zealand",
    "sg": "Singapore",
    "hk": "Hong Kong",
    "tw": "Taiwan",
    "th": "Thailand",
    "my": "Malaysia",
    "ph": "Philippines",
    "id": "Indonesia",
    "vn": "Vietnam",
    "pk": "Pakistan",
    "bd": "Bangladesh",
    # Middle East & Africa
    "ae": "United Arab Emirates",
    "sa": "Saudi Arabia",
    "il": "Israel",
    "eg": "Egypt",
    "za": "South Africa",
    "ng": "Nigeria",
    "ke": "Kenya",
    "ma": "Morocco",
    "tn": "Tunisia",
    # North America
    "ca": "Canada",
    "us": "United States",
}

# DuckDuckGo region codes for each country TLD
# Format: "{country}-{language}" (e.g., "py-es" for Paraguay Spanish)
COUNTRY_TO_DDG_REGION = {
    # Latin America (Spanish/Portuguese)
    "py": "py-es",  # Paraguay - Spanish
    "ar": "ar-es",  # Argentina - Spanish
    "br": "br-pt",  # Brazil - Portuguese
    "mx": "mx-es",  # Mexico - Spanish
    "co": "co-es",  # Colombia - Spanish
    "cl": "cl-es",  # Chile - Spanish
    "pe": "pe-es",  # Peru - Spanish
    "uy": "uy-es",  # Uruguay - Spanish
    "ec": "ec-es",  # Ecuador - Spanish
    "ve": "ve-es",  # Venezuela - Spanish
    "bo": "bo-es",  # Bolivia - Spanish
    "cr": "cr-es",  # Costa Rica - Spanish
    "pa": "pa-es",  # Panama - Spanish
    "do": "do-es",  # Dominican Republic - Spanish
    "gt": "gt-es",  # Guatemala - Spanish
    "hn": "hn-es",  # Honduras - Spanish
    "sv": "sv-es",  # El Salvador - Spanish
    "ni": "ni-es",  # Nicaragua - Spanish
    # Europe
    "uk": "uk-en",  # UK - English
    "de": "de-de",  # Germany - German
    "fr": "fr-fr",  # France - French
    "es": "es-es",  # Spain - Spanish
    "it": "it-it",  # Italy - Italian
    "nl": "nl-nl",  # Netherlands - Dutch
    "be": "be-nl",  # Belgium - Dutch
    "pt": "pt-pt",  # Portugal - Portuguese
    "at": "at-de",  # Austria - German
    "ch": "ch-de",  # Switzerland - German
    "pl": "pl-pl",  # Poland - Polish
    "se": "se-sv",  # Sweden - Swedish
    "no": "no-no",  # Norway - Norwegian
    "dk": "dk-da",  # Denmark - Danish
    "fi": "fi-fi",  # Finland - Finnish
    "ie": "ie-en",  # Ireland - English
    "ru": "ru-ru",  # Russia - Russian
    # Asia Pacific
    "jp": "jp-jp",  # Japan - Japanese
    "cn": "cn-zh",  # China - Chinese
    "kr": "kr-kr",  # South Korea - Korean
    "in": "in-en",  # India - English
    "au": "au-en",  # Australia - English
    "nz": "nz-en",  # New Zealand - English
    "sg": "sg-en",  # Singapore - English
    "hk": "hk-tzh",  # Hong Kong - Chinese
    "tw": "tw-tzh",  # Taiwan - Chinese
    "th": "th-th",  # Thailand - Thai
    "my": "my-en",  # Malaysia - English
    "ph": "ph-en",  # Philippines - English
    "id": "id-id",  # Indonesia - Indonesian
    "vn": "vn-vi",  # Vietnam - Vietnamese
    # Middle East & Africa
    "ae": "ae-ar",  # UAE - Arabic
    "sa": "sa-ar",  # Saudi Arabia - Arabic
    "il": "il-he",  # Israel - Hebrew
    "eg": "eg-ar",  # Egypt - Arabic
    "za": "za-en",  # South Africa - English
    # North America
    "ca": "ca-en",  # Canada - English
    "us": "us-en",  # United States - English
}

# Region groups for relevance scoring
# Sources from related regions are considered more relevant
REGION_GROUPS = {
    "latin_america": {"py", "ar", "br", "mx", "co", "cl", "pe", "uy", "ec", "ve", "bo", "cr", "pa", "do", "gt", "hn", "sv", "ni", "cu", "pr"},
    "europe_west": {"uk", "de", "fr", "es", "it", "nl", "be", "pt", "at", "ch", "ie"},
    "europe_north": {"se", "no", "dk", "fi"},
    "europe_east": {"pl", "cz", "hu", "ro", "bg", "hr", "sk", "si", "rs", "ua", "ru"},
    "asia_east": {"jp", "cn", "kr", "hk", "tw"},
    "asia_south": {"in", "pk", "bd"},
    "asia_southeast": {"sg", "th", "my", "ph", "id", "vn"},
    "oceania": {"au", "nz"},
    "middle_east": {"ae", "sa", "il", "eg"},
    "africa": {"za", "ng", "ke", "ma", "tn"},
    "north_america": {"ca", "us"},
}

# Irrelevant foreign TLDs - sites from these regions usually return unrelated results
# when researching companies in other regions (unless they're global business sites)
IRRELEVANT_FOREIGN_TLDS = {
    "cn",  # Chinese sites often return unrelated results
    "ru",  # Russian sites
    "jp",  # Japanese sites (unless researching Japan)
    "kr",  # Korean sites
    "vn",  # Vietnamese sites
    "th",  # Thai sites
    "id",  # Indonesian sites
}

# Global business domains that should NOT be filtered by country
# These are authoritative sources regardless of research target country
GLOBAL_BUSINESS_DOMAINS = {
    # Market research
    "mordorintelligence.com",
    "marketresearch.com",
    "globaldata.com",
    "statista.com",
    "ibisworld.com",
    "euromonitor.com",
    "frost.com",
    "gartner.com",
    "forrester.com",
    "mckinsey.com",
    "bcg.com",
    "bain.com",
    "deloitte.com",
    "pwc.com",
    "ey.com",
    "kpmg.com",
    # News & business
    "reuters.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    "economist.com",
    "forbes.com",
    "businessinsider.com",
    "cnbc.com",
    # Company data
    "linkedin.com",
    "crunchbase.com",
    "cbinsights.com",
    "pitchbook.com",
    "zoominfo.com",
    "dnb.com",
    "hoovers.com",
    "leadiq.com",
    "rocketreach.co",
    # Academic/research
    "wikipedia.org",
    "scholar.google.com",
    "researchgate.net",
    "ssrn.com",
    # Industry specific (telecom)
    "gsma.com",
    "itu.int",
    "telegeography.com",
    "fiercewireless.com",
    "lightreading.com",
    "bnamericas.com",
    "dataxis.com",
    # Financial data
    "yahoo.com",
    "finance.yahoo.com",
    "google.com",
    "investing.com",
    "tradingview.com",
    "sec.gov",
    # News wires
    "prnewswire.com",
    "businesswire.com",
    "globenewswire.com",
    "accesswire.com",
}


def get_ddg_region(country_tld: Optional[str]) -> str:
    """
    Get DuckDuckGo region code for a country TLD.

    Args:
        country_tld: Two-letter country code (e.g., "py")

    Returns:
        DuckDuckGo region code (e.g., "py-es") or "wt-wt" for worldwide.
    """
    if not country_tld:
        return "wt-wt"
    return COUNTRY_TO_DDG_REGION.get(country_tld.lower(), "wt-wt")


def get_region_group(country_tld: Optional[str]) -> Optional[str]:
    """
    Get the region group for a country TLD.

    Args:
        country_tld: Two-letter country code

    Returns:
        Region group name or None if not in any group.
    """
    if not country_tld:
        return None

    tld = country_tld.lower()
    for group_name, countries in REGION_GROUPS.items():
        if tld in countries:
            return group_name
    return None


def is_same_region(tld1: Optional[str], tld2: Optional[str]) -> bool:
    """
    Check if two country TLDs are in the same region group.

    Args:
        tld1: First country TLD
        tld2: Second country TLD

    Returns:
        True if both are in the same region group.
    """
    if not tld1 or not tld2:
        return False

    group1 = get_region_group(tld1)
    group2 = get_region_group(tld2)

    if not group1 or not group2:
        return False

    return group1 == group2


def is_global_business_domain(url: str) -> bool:
    """
    Check if a URL is from a global business domain.

    Global business domains are authoritative sources that should not
    be filtered based on country/region.

    Args:
        url: URL to check

    Returns:
        True if the URL is from a global business domain.
    """
    domain = get_domain(url)
    if not domain:
        return False

    # Check exact domain match
    if domain in GLOBAL_BUSINESS_DOMAINS:
        return True

    # Check if domain ends with any global domain (handles subdomains)
    for global_domain in GLOBAL_BUSINESS_DOMAINS:
        if domain == global_domain or domain.endswith(f".{global_domain}"):
            return True

    return False


def is_irrelevant_foreign_source(
    source_url: str,
    target_country_tld: Optional[str],
) -> bool:
    """
    Check if a source URL is from an irrelevant foreign country.

    This filters out results from countries that typically don't provide
    relevant results when researching companies in other regions.

    Args:
        source_url: URL of the source
        target_country_tld: The country TLD we're researching (e.g., "py")

    Returns:
        True if the source should be filtered out.

    Examples:
        >>> is_irrelevant_foreign_source("https://zhidao.baidu.com/...", "py")
        True  # Chinese Q&A site, irrelevant for Paraguay research
        >>> is_irrelevant_foreign_source("https://mordorintelligence.com/...", "py")
        False  # Global business domain, always relevant
    """
    # Global business domains are always relevant
    if is_global_business_domain(source_url):
        return False

    # Get the TLD of the source
    source_tld = extract_country_tld(source_url)

    # If source has no country TLD (e.g., .com, .org), it's potentially relevant
    if not source_tld:
        return False

    # If no target country specified, don't filter
    if not target_country_tld:
        return False

    # If source is from target country, it's relevant
    if source_tld == target_country_tld.lower():
        return False

    # If source is from same region, it's likely relevant
    if is_same_region(source_tld, target_country_tld):
        return False

    # If source is from an irrelevant foreign TLD, filter it
    if source_tld in IRRELEVANT_FOREIGN_TLDS:
        return True

    return False


def calculate_source_relevance_score(
    source_url: str,
    target_country_tld: Optional[str],
) -> float:
    """
    Calculate a relevance score for a source based on geographic relevance.

    Higher scores indicate more relevant sources.

    Args:
        source_url: URL of the source
        target_country_tld: The country TLD we're researching

    Returns:
        Relevance score from 0.0 to 1.0
    """
    # Global business domains get high score
    if is_global_business_domain(source_url):
        return 0.9

    source_tld = extract_country_tld(source_url)

    # No country TLD (generic .com/.org) - neutral score
    if not source_tld:
        return 0.7

    # No target country - all sources get neutral score
    if not target_country_tld:
        return 0.7

    # Exact country match - highest score
    if source_tld == target_country_tld.lower():
        return 1.0

    # Same region - high score
    if is_same_region(source_tld, target_country_tld):
        return 0.85

    # Irrelevant foreign TLD - low score
    if source_tld in IRRELEVANT_FOREIGN_TLDS:
        return 0.2

    # Other countries - moderate score
    return 0.5


def extract_country_from_url(url: str) -> Optional[str]:
    """
    Extract country from URL's TLD (top-level domain).

    Handles both simple TLDs (.py) and compound TLDs (.com.py).

    Args:
        url: Full URL like "https://www.personal.com.py"

    Returns:
        Country name if detected, None otherwise.

    Examples:
        >>> extract_country_from_url("https://www.personal.com.py")
        'Paraguay'
        >>> extract_country_from_url("https://www.personal.com.ar")
        'Argentina'
        >>> extract_country_from_url("https://www.google.com")
        None
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path

        # Remove www. prefix
        hostname = hostname.lstrip("www.")

        # Get the TLD (last part after the last dot)
        parts = hostname.split(".")
        if len(parts) < 2:
            return None

        tld = parts[-1].lower()

        # Check if it's a country TLD
        return COUNTRY_TLD_MAP.get(tld)

    except Exception:
        return None


def extract_country_tld(url: str) -> Optional[str]:
    """
    Extract the country TLD code from a URL.

    Args:
        url: Full URL

    Returns:
        Two-letter country code or None.

    Examples:
        >>> extract_country_tld("https://personal.com.py")
        'py'
        >>> extract_country_tld("https://google.com")
        None
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path
        hostname = hostname.lstrip("www.")

        parts = hostname.split(".")
        if len(parts) < 2:
            return None

        tld = parts[-1].lower()

        # Only return if it's a known country TLD
        if tld in COUNTRY_TLD_MAP:
            return tld

        return None

    except Exception:
        return None


def normalize_url(url: str, strip_query: bool = True, strip_fragment: bool = True) -> str:
    """
    Normalize URL for deduplication comparison.

    Fixes BUG-052: www.example.com and example.com should be treated as same.

    Args:
        url: URL to normalize
        strip_query: Remove query parameters (default True)
        strip_fragment: Remove URL fragments/anchors (default True)

    Returns:
        Normalized URL string.

    Examples:
        >>> normalize_url("https://www.example.com/about/")
        'https://example.com/about'
        >>> normalize_url("http://EXAMPLE.COM/Page?ref=1")
        'https://example.com/page'
    """
    if not url:
        return ""

    try:
        # Parse URL
        parsed = urlparse(url.lower())

        # Normalize scheme to https
        scheme = "https"

        # Remove www. prefix
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Normalize path - remove trailing slash
        path = parsed.path.rstrip("/")

        # Build normalized URL
        if strip_query and strip_fragment:
            return f"{scheme}://{netloc}{path}"
        elif strip_fragment:
            query = f"?{parsed.query}" if parsed.query else ""
            return f"{scheme}://{netloc}{path}{query}"
        else:
            query = f"?{parsed.query}" if parsed.query else ""
            fragment = f"#{parsed.fragment}" if parsed.fragment else ""
            return f"{scheme}://{netloc}{path}{query}{fragment}"

    except Exception:
        return url.lower()


def get_domain(url: str) -> str:
    """
    Extract the registered domain from a URL.

    Args:
        url: Full URL

    Returns:
        Domain without www prefix (e.g., "personal.com.py")
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path.split("/")[0]
        hostname = hostname.lstrip("www.")
        return hostname.lower()
    except Exception:
        return ""


def is_same_site(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same site.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if both URLs share the same domain.
    """
    return get_domain(url1) == get_domain(url2)


def add_country_context_to_query(query: str, country: str) -> str:
    """
    Add country context to a search query if not already present.

    Args:
        query: Original search query
        country: Country name to add

    Returns:
        Query with country context added.

    Examples:
        >>> add_country_context_to_query("telecommunications market", "Paraguay")
        'telecommunications market Paraguay'
        >>> add_country_context_to_query("Paraguay telecom", "Paraguay")
        'Paraguay telecom'  # Already has country
    """
    if not country or country.lower() == "global":
        return query

    # Check if country is already in query (case-insensitive)
    if country.lower() in query.lower():
        return query

    return f"{query} {country}"


# Domain pattern to industry mapping (BUG-050)
DOMAIN_INDUSTRY_PATTERNS = {
    # Telecommunications
    "personal": "Telecommunications",
    "movistar": "Telecommunications",
    "claro": "Telecommunications",
    "tigo": "Telecommunications",
    "telefonica": "Telecommunications",
    "vodafone": "Telecommunications",
    "tmobile": "Telecommunications",
    "verizon": "Telecommunications",
    "att": "Telecommunications",
    "orange": "Telecommunications",
    "telecom": "Telecommunications",
    "telco": "Telecommunications",
    "mobile": "Telecommunications",
    # Banking / Finance
    "banco": "Banking",
    "bank": "Banking",
    "finance": "Financial Services",
    "invest": "Financial Services",
    "capital": "Financial Services",
    "credit": "Financial Services",
    "insurance": "Insurance",
    "seguros": "Insurance",
    # Technology
    "tech": "Technology",
    "software": "Software",
    "cloud": "Cloud Services",
    "data": "Data Services",
    "cyber": "Cybersecurity",
    "ai": "Artificial Intelligence",
    # Retail / E-commerce
    "shop": "Retail",
    "store": "Retail",
    "market": "Retail",
    "mall": "Retail",
    "ecommerce": "E-commerce",
    # Healthcare
    "health": "Healthcare",
    "medical": "Healthcare",
    "pharma": "Pharmaceuticals",
    "hospital": "Healthcare",
    "clinic": "Healthcare",
    # Manufacturing
    "manufacturing": "Manufacturing",
    "industrial": "Manufacturing",
    "factory": "Manufacturing",
    # Energy
    "energy": "Energy",
    "power": "Energy",
    "oil": "Oil & Gas",
    "gas": "Oil & Gas",
    "solar": "Renewable Energy",
    "electric": "Utilities",
    # Real Estate
    "realty": "Real Estate",
    "property": "Real Estate",
    "housing": "Real Estate",
    # Transportation
    "logistics": "Logistics",
    "transport": "Transportation",
    "shipping": "Shipping",
    "freight": "Logistics",
    "airline": "Aviation",
    # Hospitality
    "hotel": "Hospitality",
    "travel": "Travel",
    "tourism": "Tourism",
    "resort": "Hospitality",
    # Education
    "edu": "Education",
    "university": "Education",
    "school": "Education",
    "academy": "Education",
    # Media
    "media": "Media",
    "news": "Media",
    "entertainment": "Entertainment",
    "gaming": "Gaming",
}


def infer_industry_from_domain(url: str) -> Optional[str]:
    """
    Infer company industry from domain name patterns.

    This is a heuristic-based approach for BUG-050 that provides
    reasonable defaults when industry is not explicitly provided.

    Args:
        url: Company website URL

    Returns:
        Inferred industry name or None if not detected.

    Examples:
        >>> infer_industry_from_domain("https://personal.com.py")
        'Telecommunications'
        >>> infer_industry_from_domain("https://banco-nacional.com")
        'Banking'
        >>> infer_industry_from_domain("https://example.com")
        None
    """
    if not url:
        return None

    try:
        domain = get_domain(url).lower()

        # Check each pattern against the domain
        for pattern, industry in DOMAIN_INDUSTRY_PATTERNS.items():
            if pattern in domain:
                return industry

        return None

    except Exception:
        return None


def infer_industry_from_name(company_name: str) -> Optional[str]:
    """
    Infer company industry from company name patterns.

    Args:
        company_name: Company name

    Returns:
        Inferred industry name or None if not detected.

    Examples:
        >>> infer_industry_from_name("Personal Paraguay")
        'Telecommunications'
        >>> infer_industry_from_name("First National Bank")
        'Banking'
    """
    if not company_name:
        return None

    name_lower = company_name.lower()

    # Check each pattern against the company name
    for pattern, industry in DOMAIN_INDUSTRY_PATTERNS.items():
        if pattern in name_lower:
            return industry

    return None


def infer_industry(url: str, company_name: str = "") -> Optional[str]:
    """
    Infer company industry from URL and/or company name.

    Tries URL first, then falls back to company name.

    Args:
        url: Company website URL
        company_name: Company name (optional)

    Returns:
        Inferred industry name or None if not detected.
    """
    # Try URL first (more reliable)
    industry = infer_industry_from_domain(url)
    if industry:
        return industry

    # Fall back to company name
    return infer_industry_from_name(company_name)
