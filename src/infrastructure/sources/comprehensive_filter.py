"""
Comprehensive Source Filter v2.0 - Implements all 50 quality improvements.

This module provides complete source filtering including:
- Failed source detection (#1-10)
- Entity validation (#11-20)
- Content quality checks (#29-35)
- Data recency validation (#36-42)
- Report quality enforcement (#43-50)

Integrates with the pipeline to ensure only high-quality, relevant sources reach AI synthesis.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from urllib.parse import urlparse

from src.core.config import get_settings
from src.core.logging import setup_logger
from src.core.types.base import ResearchSource
from src.core.types.test_brief import ResearchIntelligenceBrief

logger = setup_logger("comprehensive_filter")


class FilterReason(Enum):
    """Reasons a source was filtered out."""

    # Network/Access failures (#1-5)
    NAVIGATION_FAILED = "navigation_failed"
    BLOCKED_DOMAIN = "blocked_domain"
    CLOUDFLARE = "cloudflare_protection"
    ACCESS_DENIED = "access_denied"
    ERROR_PAGE = "error_page"

    # Content quality (#6-10, #29-35)
    EMPTY_CONTENT = "empty_content"
    PDF_NOT_EXTRACTED = "pdf_not_extracted"
    PAYWALL = "paywall"
    LOGIN_REQUIRED = "login_required"
    TIMEOUT = "timeout"
    LOW_TEXT_RATIO = "low_text_ratio"

    # Entity validation (#11-20)
    WRONG_ENTITY = "wrong_entity"
    WRONG_COUNTRY = "wrong_country"
    WRONG_INDUSTRY = "wrong_industry"
    GENERIC_CONTENT = "generic_content"

    # Data quality (#36-42)
    OUTDATED = "outdated_data"
    IRRELEVANT = "irrelevant_content"
    UNRELATED_TOPIC = "unrelated_topic"

    # Quality thresholds
    LOW_QUALITY = "low_quality"
    DUPLICATE = "duplicate"


@dataclass
class FilteredSource:
    """A source that was filtered out."""

    url: str
    title: str
    reason: FilterReason
    detail: str
    original_source: Optional[ResearchSource] = None


@dataclass
class FilterResult:
    """Result of filtering sources."""

    usable_sources: List[ResearchSource] = field(default_factory=list)
    filtered_sources: List[FilteredSource] = field(default_factory=list)

    # Detailed counters
    navigation_failed: int = 0
    cloudflare_blocked: int = 0
    access_denied: int = 0
    empty_content: int = 0
    wrong_entity: int = 0
    wrong_country: int = 0
    outdated: int = 0
    irrelevant: int = 0
    low_quality: int = 0
    duplicates: int = 0

    @property
    def total_filtered(self) -> int:
        return len(self.filtered_sources)

    @property
    def has_minimum_sources(self) -> bool:
        """Check if we have minimum required sources (3+)."""
        return len(self.usable_sources) >= 3

    @property
    def needs_more_sources(self) -> int:
        """How many more sources needed to meet minimum."""
        return max(0, 3 - len(self.usable_sources))

    def get_summary(self) -> Dict[str, int]:
        """Get summary of filtering results."""
        return {
            "usable": len(self.usable_sources),
            "filtered": self.total_filtered,
            "navigation_failed": self.navigation_failed,
            "cloudflare": self.cloudflare_blocked,
            "access_denied": self.access_denied,
            "empty": self.empty_content,
            "wrong_entity": self.wrong_entity,
            "wrong_country": self.wrong_country,
            "outdated": self.outdated,
            "irrelevant": self.irrelevant,
            "low_quality": self.low_quality,
            "duplicates": self.duplicates,
        }


# =============================================================================
# Pattern Definitions (#1-10, #29-35)
# =============================================================================

# Title patterns indicating fetch failures
FAILED_TITLE_PATTERNS: List[Tuple[str, FilterReason]] = [
    # Navigation/Access failures
    (r"^navigation\s+failed$", FilterReason.NAVIGATION_FAILED),
    (r"^blocked\s+domain$", FilterReason.BLOCKED_DOMAIN),
    (r"^just\s+a\s+moment", FilterReason.CLOUDFLARE),
    (r"^attention\s+required", FilterReason.CLOUDFLARE),
    (r"^access\s+(denied|to\s+this)", FilterReason.ACCESS_DENIED),
    (r"^error\s*[-:]?\s*\d{3}", FilterReason.ERROR_PAGE),
    (
        r"^error:\s+the\s+request\s+could\s+not\s+be\s+satisfied",
        FilterReason.ERROR_PAGE,
    ),
    (r"^404\s", FilterReason.ERROR_PAGE),
    (r"^403\s", FilterReason.ACCESS_DENIED),
    (r"^401\s", FilterReason.ACCESS_DENIED),
    (r"^500\s", FilterReason.ERROR_PAGE),
    (r"^502\s*:?\s*bad\s+gateway", FilterReason.ERROR_PAGE),
    (r"^503\s", FilterReason.ERROR_PAGE),
    (r"^page\s+not\s+found", FilterReason.ERROR_PAGE),
    (r"^forbidden", FilterReason.ACCESS_DENIED),
    (r"^cloudflare", FilterReason.CLOUDFLARE),
    (r"^captcha", FilterReason.CLOUDFLARE),
    (r"^verify\s+you", FilterReason.CLOUDFLARE),
    (r"^checking\s+your\s+browser", FilterReason.CLOUDFLARE),
    (r"^pdf\s+document\s*\(not\s+extracted\)", FilterReason.PDF_NOT_EXTRACTED),
    (r"^no\s+content\s+extracted", FilterReason.EMPTY_CONTENT),
    (r"^fetch\s+timeout", FilterReason.TIMEOUT),
    (r"^timeout", FilterReason.TIMEOUT),
    (r"^request\s+timed?\s*out", FilterReason.TIMEOUT),
    # SEC.gov blocked pages
    (r"sec\.gov\s*\|\s*your\s+request\s+originates", FilterReason.ACCESS_DENIED),
    (
        r"your\s+request\s+originates\s+from\s+an?\s+undeclared",
        FilterReason.ACCESS_DENIED,
    ),
    # Best jobs / irrelevant pages
    (r"^best\s+jobs\s+for\s+you", FilterReason.IRRELEVANT),
    # Recurso placeholder pages
    (r"^recurso\s+\d+$", FilterReason.EMPTY_CONTENT),
]

# Content patterns indicating failed fetch (#3, #4)
FAILED_CONTENT_PATTERNS: List[Tuple[str, FilterReason]] = [
    (r"enable\s+javascript", FilterReason.CLOUDFLARE),
    (r"please\s+verify\s+you\s+are\s+(a\s+)?human", FilterReason.CLOUDFLARE),
    (r"complete\s+the\s+security\s+check", FilterReason.CLOUDFLARE),
    (r"your\s+ip\s+(address\s+)?(has\s+been\s+)?blocked", FilterReason.BLOCKED_DOMAIN),
    (
        r"access\s+to\s+this\s+site\s+has\s+been\s+(denied|blocked)",
        FilterReason.ACCESS_DENIED,
    ),
    (r"security\s+check\s+required", FilterReason.CLOUDFLARE),
    (r"ray\s+id:\s*[a-f0-9]+", FilterReason.CLOUDFLARE),  # Cloudflare Ray ID
    (r"performance\s+&\s+security\s+by\s+cloudflare", FilterReason.CLOUDFLARE),
    # SEC.gov blocks
    (
        r"request\s+originates\s+from\s+an?\s+undeclared\s+automated\s+tool",
        FilterReason.ACCESS_DENIED,
    ),
    # YouTube UI text (not actual content)
    (r"activar\s+sonido.*buscar.*copiar\s+vínculo", FilterReason.EMPTY_CONTENT),
    (
        r"si\s+la\s+reproducción\s+no\s+comienza\s+en\s+breve",
        FilterReason.EMPTY_CONTENT,
    ),
    (
        r"saliste\s+de\s+tu\s+cuenta.*historial\s+de\s+reproducciones",
        FilterReason.EMPTY_CONTENT,
    ),
    # Browser detection warnings
    (r"your\s+browser\s+is.*out\s+of\s+date", FilterReason.EMPTY_CONTENT),
    (r"this\s+browser\s+is\s+out\s+of\s+date", FilterReason.EMPTY_CONTENT),
    (r"chrome\s+headless.*out\s+of\s+date", FilterReason.EMPTY_CONTENT),
]

# Garbage content patterns (UI elements, not real content)
GARBAGE_CONTENT_PATTERNS: List[str] = [
    r"^terms\s+of\s+service.*privacy\s+policy.*careers",
    r"^skip\s+to\s+content.*quick\s+links",
    r"©\s*\d{4}\s+bloomberg\s+l\.p\.\s*all\s+rights\s+reserved\.\s*$",
    r"^cookies?\s+(preferences?|settings)",
]

# Paywall patterns (#8)
PAYWALL_PATTERNS: List[str] = [
    r"subscribe\s+to\s+(read|continue|access)",
    r"premium\s+content",
    r"members?\s+only",
    r"sign\s+up\s+to\s+(read|continue)",
    r"create\s+an?\s+account\s+to",
    r"this\s+(article|content)\s+is\s+(only\s+)?available\s+to\s+subscribers",
    r"you('ve|'re|\s+have)\s+(reached|hit)\s+(your|the)\s+(free\s+)?limit",
    r"unlock\s+full\s+access",
]

# Login required patterns (#31)
LOGIN_PATTERNS: List[str] = [
    r"<form[^>]*login",
    r"sign\s*in\s+required",
    r"please\s+(log|sign)\s+in",
    r"authentication\s+required",
]


# =============================================================================
# Entity Disambiguation Rules (#11-20)
# =============================================================================

COMPANY_DISAMBIGUATION: Dict[str, Dict[str, Any]] = {
    # Tigo Paraguay (telecom) vs Tigo Energy (solar) - #11
    "tigo": {
        "target": "tigo paraguay telecommunications millicom",
        "required_any": [
            "paraguay",
            "telecom",
            "millicom",
            "móvil",
            "celular",
            "telefon",
            "tigo.com.py",
        ],
        "reject_all": [
            "solar",
            "energy",
            "photovoltaic",
            "inverter",
            "panel",
            "watt",
            "kwh",
            "pv system",
            "tigo energy",
            "tigoenergy",
            "power optimizer",
        ],
        "reject_domains": [
            "tigoenergy.com",
            "photovoltaikforum.com",
            "solarweb.com",
            "pvforum.de",
        ],
    },
    # COPACO Paraguay (telecom) vs Copaco Belgium/Netherlands (IT distributor) - #11, #16, #17
    "copaco": {
        "target": "copaco paraguay telecommunications comunicaciones",
        "required_any": [
            "paraguay",
            "comunicaciones",
            "vox",
            "copaco.com.py",
            "conatel",
            "asunción",
        ],
        "reject_all": [
            # Geographic - Belgium/Netherlands
            "belgium",
            "netherlands",
            "nederland",
            "benelux",
            "france",
            "belgian",
            "dutch",
            "bruxelles",
            "brussels",
            "amsterdam",
            "rotterdam",
            "antwerp",
            "affligem",
            "de montil",
            # Business type - IT distribution
            "distributor",
            "it distribution",
            "cloudchampion",
            "reseller",
            "value added",
            "microsoft partner",
            "belux",
            "channel partner",
            "var ",
            "vendor",
            "ict products",
            "ict solutions",
            "msp",
            "managed service provider",
            # Wrong company names
            "copaco financial services",
            "copaco nv",
            "copaco n.v.",
            "copaco bv",
            "copaco b.v.",
            "copaco inc",
            "copaco screenweavers",
            "tejidos copaco",
            "cool - tejidos",
            # US Copaco Inc (mining company)
            "mining",
            "quarrying",
            "milling",
            "nonmetallic minerals",
            "mineral",
            # Domain indicators
            "copaco.be",
            "copaco.nl",
            "copaco.com/en",
            "enterprise solutions copaco.com",
            # Other similar names / events
            "copaconnect",
            "copa connect",
            "copaconnect 2025",
            # Pharmaceutical (completely unrelated)
            "dr. reddy",
            "dr reddy",
            "pharmaceutical",
            "biotech",
        ],
        "reject_domains": [
            # Belgium/Netherlands Copaco (NOT copaco.com.py!)
            "copaco.be",
            "copaco.nl",
            "copaco.com",
            "cloudchampion.be",
            "werkenbijcopaco.com",
            "copaco.cloudchampion.be",
            "kb.copaco.cloud",
            "copaco.cloud",
            "media.copaco.com",
            "itdaily.com",
            "itdaily.be",
            "arcadiz.com",  # Belgian network infrastructure partner
            # US Copaco Inc
            "bloomberg.com/profile/company/0452063D",  # Copaco Inc US
            "bloomberg.com/profile/company/2375001D",  # Copaco Financial Services BV
            # Soccer/sports sites
            "copaamerica.com",
            "conmebol.com",
            "fifa.com",
            # Pharmaceutical
            "biospace.com",
            # Generic government sites (wrong country)
            "belgium.be",
        ],
        # URL path patterns to reject
        "reject_url_patterns": [
            r"/copaco-nederland",
            r"/copaco-belgium",
            r"/en-be/",  # Belgium locale
            r"/nl-nl/",  # Netherlands locale
        ],
    },
    # COPPA (meat) vs COPACO - #16
    "coppa": {
        "reject_if_searching": "copaco",
        "reject_all": [
            "capocollo",
            "cured meat",
            "salumi",
            "italian meat",
            "pork",
            "coppa market",
        ],
    },
    # Copado (DevOps) vs COPACO - #17
    "copado": {
        "reject_if_searching": "copaco",
        "reject_all": ["devops", "salesforce", "ci/cd", "deployment", "copado.com"],
        "reject_domains": ["copado.com"],
    },
    # Cogeco (Canada) vs COPACO - #18
    "cogeco": {
        "reject_if_searching": "copaco",
        "reject_all": [
            "canada",
            "quebec",
            "ontario",
            "canadian",
            "cogeco customer service",
        ],
        "reject_domains": ["cogeco.ca", "cogeco.com"],
    },
    # Claro Paraguay vs other Claro - #19
    "claro": {
        "target": "claro paraguay américa móvil telecommunications amx",
        "required_any": ["paraguay", "claro.com.py"],
        "reject_all": [
            # Colombia Claro (for Paraguay searches)
            "claro colombia",
            "claro.co",
            # Grupo Clarín (Argentina media)
            "grupo clarín",
            "clarín",
            "clarin.com",
        ],
        "reject_domains": [],
    },
    # Personal Paraguay vs Personal Argentina - #19
    "personal": {
        "target": "personal paraguay núcleo telecommunications telecom",
        "required_any": ["paraguay", "núcleo", "personal.com.py"],
        "reject_domains": [],
    },
    # Vox Paraguay (MVNO) vs other Vox - #20
    "vox": {
        "target": "vox paraguay copaco mvno",
        "required_any": ["paraguay", "copaco", "mvno"],
        "reject_all": [
            "vox media",
            "vox.com",
            "vox news",
            "voxeu",
            "vox populi",
            "vox day",
        ],
        "reject_domains": ["vox.com", "voxmedia.com", "voxeu.org"],
    },
}

# Globally blocked domains (always filter regardless of company)
# NOTE: These are matched as exact domains or subdomains (e.g., "copaco.be" blocks "www.copaco.be" but not "copaco.be.other.com")
GLOBALLY_BLOCKED_DOMAINS: Set[str] = {
    # Soccer/Sports sites
    "copaamerica.com",
    "conmebol.com",
    "espn.com",
    "as.com",
    "goal.com",
    "marca.com",
    # Beekeeping (wrong domain entirely)
    "apiaryinspectors.org",
    # Generic template sites
    "canva.com",
    "canvasbusinessmodel.com",
    # SIM unlock services
    "sim-unlock.net",
    "doctorsim.com",
    # App stores (low value)
    "play.google.com",
    "apps.apple.com",
    # Wrong company domains for Paraguay telecom (NOT copaco.com.py which is correct!)
    "copaco.be",
    "copaco.nl",
    "copaco.com",  # Belgium/Netherlands IT distributor (NOT Paraguay's copaco.com.py!)
    "copaco.cloud",
    "cloudchampion.be",
    "copaco.cloudchampion.be",
    "kb.copaco.cloud",
    "media.copaco.com",
    "werkenbijcopaco.com",
    "arcadiz.com",  # Belgian network infrastructure (Copaco Cloud partner)
    # European IT news sites (wrong Copaco - Belgium IT distributor)
    "itdaily.com",
    "itdaily.be",
    # Pharmaceutical/biotech (completely unrelated)
    "biospace.com",
    # Generic business intelligence with low value
    "socket.dev",
    # Job portals with minimal company data
    "glassdoor.ca",
    "glassdoor.co.in",
    "glassdoor.ie",
    "glassdoor.sg",
}


# Generic/irrelevant content patterns (#12, #13, #14)
GENERIC_CONTENT_PATTERNS: List[Tuple[str, str]] = [
    # Generic Wikipedia articles (#12)
    (r"^telecommunications\s*[-–]\s*wikipedia", "Generic telecom Wikipedia"),
    (r"^telecomunicación\s*[-–]\s*wikipedia", "Generic telecom Wikipedia (Spanish)"),
    (r"^economy\s+of\s+\w+\s*[-–]\s*wikipedia", "Generic economy Wikipedia"),
    (r"^world\s+wide\s+web\s*[-–]\s*wikipedia", "Generic WWW Wikipedia"),
    (r"^www\s*[-–]?\s*wikipedia", "Generic WWW Wikipedia"),
    (r"^¿qué\s+significa\s+www", "WWW explanation article"),
    (r"^list\s+of\s+telecommunications\s+regulatory", "Generic regulator list"),
    (r"^category:\s*telecommunications", "Wikipedia category page"),
    # Travel guides for telecom research (#13)
    (r"voyage\s+paraguay", "Travel guide"),
    (r"routard\.com", "Travel guide"),
    (r"lonely\s*planet", "Travel guide"),
    (r"tripadvisor", "Travel guide"),
    (r"petit\s*futé", "Travel guide"),
    # Sports articles (#14) - EXPANDED
    (
        r"paraguay\s+(pulled\s+off|defeated|beat|won|lost).*(brazil|brasil|argentina|uruguay|netherlands)",
        "Sports article",
    ),
    (
        r"(brazil|brasil|argentina|uruguay|netherlands)\s+\d+\s*[-–]\s*\d+\s+paraguay",
        "Sports score",
    ),
    (r"uruguay\s+\d+\s*[-–]\s*\d+\s+paraguay", "Sports score"),
    (r"netherlands\s*[-–]?\s*paraguay\s+match", "Sports article"),
    (r"futsal\s*world\s*cup", "Sports article"),
    (r"copa\s+am[eé]rica\s+(beach\s+)?soccer", "Sports article"),
    (r"beach\s+soccer", "Sports article"),
    (r"goles?,?\s+resumen\s+y\s+resultado", "Sports article"),
    (r"eliminatorias", "Sports article"),
    (r"mundial\s+\d{4}", "Sports article"),
    (r"club\s+(?:guaraní|olimpia|cerro)", "Sports article"),
    (r"sudamericano\s+sub[- ]?\d+", "Sports article"),
    (r"pan\s+american\s+games", "Sports article"),
    # Wrong entity - Copaco Belgium/Netherlands IT distributor
    (r"copaco\s+nederland\b", "Wrong entity - Netherlands Copaco"),
    (r"copaco\s+netherlands", "Wrong entity - Netherlands Copaco"),
    (r"copaco\s+belgium", "Wrong entity - Belgium Copaco"),
    (r"belgium\s+cloud\s+champion", "Wrong entity - Belgium Copaco"),
    (r"copaco\s+(nv|b\.?v\.?)\b", "Wrong entity - Belgium/Netherlands Copaco"),
    (r"copaco.*\bit\s+distribut", "Wrong entity - IT Distributor"),
    (r"copaco.*benelux", "Wrong entity - Benelux region"),
    # Beekeeping / Agriculture (completely wrong domain)
    (r"apiary\s+inspector", "Beekeeping article"),
    (r"beekeeping\s+survey", "Beekeeping article"),
    (r"bee\s+colony\s+loss", "Beekeeping article"),
    # Finance for wrong companies
    (r"onity\s+swot\s+analysis", "Wrong company finance"),
    (r"dr\.?\s*reddy.*financials?", "Wrong company finance"),
    # Generic annual reports
    (r"isags.*annual\s+report", "Wrong organization report"),
    # SIM unlock services
    (r"unlock\s+by\s+code\s+any\s+samsung", "SIM unlock service"),
    (r"sim[-\s]?unlock", "SIM unlock service"),
    # My Apps portal (Microsoft)
    (r"my\s+apps\s+portal\s+overview.*microsoft", "Microsoft docs"),
]

# Irrelevant title patterns (titles that indicate wrong content)
IRRELEVANT_TITLE_PATTERNS: List[Tuple[str, str]] = [
    # Soccer/Sports
    (r"paraguay.*(defeated|beat|won|lost|upset)", "Sports headline"),
    (r"(brazil|argentina|uruguay)\s+\d+\s*-\s*\d+\s+paraguay", "Sports score"),
    (r"uruguay\s+\d+\s*-\s*\d+\s+paraguay", "Sports score"),
    (r"copa\s+am[eé]rica", "Sports event"),
    (r"beach\s+soccer", "Sports"),
    (r"pan\s+american\s+games", "Sports event"),
    # Beekeeping
    (r"apiary\s+inspector", "Beekeeping"),
    (r"beekeeping", "Beekeeping"),
    # Wrong company
    (r"copaco\s+financial\s+services\s+bv", "Wrong company (Netherlands)"),
    (r"copaco\s+nv", "Wrong company (Netherlands)"),
    (r"copaco\s+inc", "Wrong company (US)"),
    (r"microsoft\s+belux.*copaco", "Wrong company (Belgium)"),
    (r"cool\s*[-–]?\s*tejidos.*copaco", "Wrong company (textiles)"),
    (r"copaco\s+screenweavers", "Wrong company (textiles)"),
    # Generic unhelpful
    (r"^www$", "Just WWW"),
    (r"^wwww*$", "Just WWW"),
]


# Domain-based filtering (#18, #19, #20)
DOMAIN_COUNTRY_FILTERS: Dict[str, List[str]] = {
    "paraguay": {
        "prefer": [".com.py", ".gov.py", ".org.py", ".edu.py"],
        "reject_for_local": [".be", ".nl", ".ca"],  # Belgium, Netherlands, Canada
    },
    "argentina": {
        "prefer": [".com.ar", ".gov.ar", ".org.ar"],
        "reject_for_local": [".be", ".nl"],
    },
}


# =============================================================================
# Comprehensive Source Filter Class
# =============================================================================


class ComprehensiveSourceFilter:
    """
    Complete source filtering implementing all 50 improvements.

    Filters:
    - Failed fetches (#1-5)
    - Empty/low-quality content (#6-10, #29-35)
    - Wrong entity sources (#11-20)
    - Outdated data (#36-42)
    - Irrelevant content (#43-50)
    """

    # Minimum content length (characters) - #6
    MIN_CONTENT_LENGTH = 100

    # Default recency threshold (years) - #36
    DEFAULT_RECENCY_YEARS = 2

    # Year pattern for recency check
    YEAR_PATTERN = re.compile(r"\b(20[0-2][0-9])\b")

    def __init__(
        self,
        company_name: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        recency_years: int = DEFAULT_RECENCY_YEARS,
        minimum_sources: int = 3,
        strict_mode: bool = True,
        research_brief: Optional[ResearchIntelligenceBrief] = None,
    ):
        """
        Initialize comprehensive source filter.

        Args:
            company_name: Target company name
            country: Target country (for disambiguation)
            industry: Target industry (for disambiguation)
            recency_years: Max age of data to include
            minimum_sources: Minimum required sources for valid results
            strict_mode: If True, apply all filters; if False, only critical ones
            research_brief: AI-generated research brief for enhanced filtering
        """
        self.company_name = company_name.lower().strip()
        self.country = country.lower() if country else None
        self.industry = industry.lower() if industry else None
        self.recency_years = recency_years
        self.minimum_sources = minimum_sources
        self.strict_mode = strict_mode
        self.research_brief = research_brief

        # Current year for recency calculations
        self.current_year = datetime.now().year
        self.min_year = self.current_year - recency_years

        # Load disambiguation rules
        self._load_entity_rules()

        # Load AI-first brief criteria if available
        self._load_brief_criteria()

        brief_info = ""
        if research_brief and research_brief.confidence_score > 0:
            brief_info = f", brief_confidence={research_brief.confidence_score:.2f}"

        logger.info(
            f"Comprehensive filter initialized: company='{company_name}', "
            f"country={country}, min_year={self.min_year}, strict={strict_mode}{brief_info}"
        )

    def _load_brief_criteria(self) -> None:
        """Load filtering criteria from the AI research brief."""
        self.brief_relevance_keywords: Set[str] = set()
        self.brief_irrelevance_keywords: Set[str] = set()
        self.brief_exclusion_patterns: List[str] = []
        self.brief_entity_identifiers: List[Dict[str, str]] = []
        self.brief_target_domains: Set[str] = set()

        if not self.research_brief or self.research_brief.confidence_score <= 0:
            return

        brief = self.research_brief

        # Load relevance keywords from brief
        if brief.relevance_keywords:
            self.brief_relevance_keywords = {
                kw.lower() for kw in brief.relevance_keywords
            }
            logger.debug(
                f"Loaded {len(self.brief_relevance_keywords)} relevance keywords from brief"
            )

        # Load irrelevance keywords from brief
        if brief.irrelevance_keywords:
            self.brief_irrelevance_keywords = {
                kw.lower() for kw in brief.irrelevance_keywords
            }
            logger.debug(
                f"Loaded {len(self.brief_irrelevance_keywords)} irrelevance keywords from brief"
            )

        # Load exclusion patterns from brief
        if brief.exclusion_patterns:
            self.brief_exclusion_patterns = [
                p.pattern.lower() for p in brief.exclusion_patterns
            ]
            logger.debug(
                f"Loaded {len(self.brief_exclusion_patterns)} exclusion patterns from brief"
            )

        # Load entity identifiers from brief
        if brief.entity_identifiers:
            self.brief_entity_identifiers = [
                {
                    "type": e.identifier_type,
                    "value": e.value.lower(),
                    "confidence": e.confidence,
                }
                for e in brief.entity_identifiers
            ]
            logger.debug(
                f"Loaded {len(self.brief_entity_identifiers)} entity identifiers from brief"
            )

        # Load target domains from brief
        if brief.target_domains:
            self.brief_target_domains = {d.lower() for d in brief.target_domains}
            logger.debug(
                f"Loaded {len(self.brief_target_domains)} target domains from brief"
            )

    def _load_entity_rules(self) -> None:
        """Load entity disambiguation rules for the company."""
        self.entity_rules: Dict[str, Any] = {}
        self.reject_keywords: Set[str] = set()
        self.reject_domains: Set[str] = set()
        self.required_keywords: Set[str] = set()

        # Find matching rules
        for key, rules in COMPANY_DISAMBIGUATION.items():
            if key in self.company_name or self.company_name in key:
                self.entity_rules = rules
                self.reject_keywords.update(rules.get("reject_all", []))
                self.reject_domains.update(rules.get("reject_domains", []))
                if "required_any" in rules:
                    self.required_keywords.update(rules.get("required_any", []))
                break

        # Add rules for commonly confused companies
        for key, rules in COMPANY_DISAMBIGUATION.items():
            if rules.get("reject_if_searching") == self.company_name.split()[0]:
                self.reject_keywords.update(rules.get("reject_all", []))
                self.reject_domains.update(rules.get("reject_domains", []))

    def filter_sources(
        self,
        sources: List[ResearchSource],
        section_name: Optional[str] = None,
    ) -> FilterResult:
        """
        Filter sources to keep only high-quality, relevant ones.

        Implements all filtering improvements (#1-50).

        Args:
            sources: List of sources to filter
            section_name: Optional section name for logging

        Returns:
            FilterResult with usable and filtered sources
        """
        result = FilterResult()
        section_log = f" [{section_name}]" if section_name else ""
        seen_urls: Set[str] = set()

        for source in sources:
            # Normalize URL for deduplication
            normalized_url = self._normalize_url(source.url)

            # Check for duplicates first
            if normalized_url in seen_urls:
                result.filtered_sources.append(
                    FilteredSource(
                        url=source.url,
                        title=source.title or "",
                        reason=FilterReason.DUPLICATE,
                        detail="Duplicate URL",
                        original_source=source,
                    )
                )
                result.duplicates += 1
                continue

            seen_urls.add(normalized_url)

            # Run all filter checks
            filter_outcome = self._evaluate_source(source)

            if filter_outcome is None:
                # Source passed all filters
                result.usable_sources.append(source)
            else:
                # Source was filtered
                reason, detail = filter_outcome
                result.filtered_sources.append(
                    FilteredSource(
                        url=source.url,
                        title=source.title or "",
                        reason=reason,
                        detail=detail,
                        original_source=source,
                    )
                )

                # Update specific counters
                self._update_counters(result, reason)

        # Log summary
        summary = result.get_summary()
        logger.info(
            f"Source filter{section_log}: {len(result.usable_sources)}/{len(sources)} usable | "
            f"nav_fail={summary['navigation_failed']} cloudflare={summary['cloudflare']} "
            f"entity={summary['wrong_entity']} outdated={summary['outdated']} "
            f"irrelevant={summary['irrelevant']} dupes={summary['duplicates']}"
        )

        if not result.has_minimum_sources:
            logger.warning(
                f"Source filter{section_log}: BELOW MINIMUM! "
                f"Have {len(result.usable_sources)}, need {self.minimum_sources}"
            )

        return result

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        normalized = url.lower().rstrip("/")
        # Remove www. prefix
        if "://www." in normalized:
            normalized = normalized.replace("://www.", "://")
        # Remove tracking parameters
        if "?" in normalized:
            normalized = normalized.split("?")[0]
        return normalized

    def _update_counters(self, result: FilterResult, reason: FilterReason) -> None:
        """Update specific counters based on filter reason."""
        if reason == FilterReason.NAVIGATION_FAILED:
            result.navigation_failed += 1
        elif reason in (FilterReason.CLOUDFLARE, FilterReason.BLOCKED_DOMAIN):
            result.cloudflare_blocked += 1
        elif reason == FilterReason.ACCESS_DENIED:
            result.access_denied += 1
        elif reason in (FilterReason.EMPTY_CONTENT, FilterReason.PDF_NOT_EXTRACTED):
            result.empty_content += 1
        elif reason == FilterReason.WRONG_ENTITY:
            result.wrong_entity += 1
        elif reason == FilterReason.WRONG_COUNTRY:
            result.wrong_country += 1
        elif reason == FilterReason.OUTDATED:
            result.outdated += 1
        elif reason in (
            FilterReason.IRRELEVANT,
            FilterReason.UNRELATED_TOPIC,
            FilterReason.GENERIC_CONTENT,
        ):
            result.irrelevant += 1
        else:
            result.low_quality += 1

    def _evaluate_source(
        self,
        source: ResearchSource,
    ) -> Optional[Tuple[FilterReason, str]]:
        """
        Evaluate a single source against all filters.

        Returns:
            None if source is usable, or (FilterReason, detail) if filtered
        """
        title = source.title or ""
        content = source.content or ""
        url = source.url or ""

        title_lower = title.lower().strip()
        content_lower = content.lower()

        # Extract domain
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            domain = ""

        # =================================================================
        # CRITICAL FILTERS (#1-5) - Always applied
        # =================================================================

        # Check globally blocked domains FIRST
        # Use precise matching: domain equals blocked OR domain ends with ".blocked"
        for blocked in GLOBALLY_BLOCKED_DOMAINS:
            if domain == blocked or domain.endswith(f".{blocked}"):
                return (FilterReason.BLOCKED_DOMAIN, f"Globally blocked: {blocked}")

        # #1, #2: Check failed title patterns
        for pattern, reason in FAILED_TITLE_PATTERNS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return (reason, f"Title matches: {title[:50]}")

        # Check irrelevant title patterns (sports, beekeeping, wrong companies)
        for pattern, description in IRRELEVANT_TITLE_PATTERNS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return (FilterReason.IRRELEVANT, f"Irrelevant: {description}")

        # #3, #4: Check failed content patterns
        for pattern, reason in FAILED_CONTENT_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return (reason, "Content matches blocked pattern")

        # #5: Check for empty/minimal content
        if not content or len(content.strip()) < self.MIN_CONTENT_LENGTH:
            return (
                FilterReason.EMPTY_CONTENT,
                f"Content too short: {len(content)} chars",
            )

        # =================================================================
        # ENTITY VALIDATION (#11-20)
        # =================================================================

        # #11: Check rejected domains (use precise matching)
        for rejected_domain in self.reject_domains:
            # Check if domain matches exactly or is a subdomain
            if domain == rejected_domain or domain.endswith(f".{rejected_domain}"):
                return (
                    FilterReason.WRONG_ENTITY,
                    f"Excluded domain: {rejected_domain}",
                )
            # Also check URL paths for specific patterns (e.g., bloomberg.com/profile/company/ID)
            if "/" in rejected_domain and rejected_domain in url.lower():
                return (
                    FilterReason.WRONG_ENTITY,
                    f"Excluded URL pattern: {rejected_domain}",
                )

        # #11-17: Check rejected keywords
        combined = f"{title_lower} {content_lower[:2000]}"
        for keyword in self.reject_keywords:
            if keyword in combined:
                return (FilterReason.WRONG_ENTITY, f"Wrong entity keyword: {keyword}")

        # #12-14: Check generic/irrelevant content patterns
        for pattern, description in GENERIC_CONTENT_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return (FilterReason.GENERIC_CONTENT, description)

        # #18-20: Check country domain mismatch
        if self.country and self.country in DOMAIN_COUNTRY_FILTERS:
            filters = DOMAIN_COUNTRY_FILTERS[self.country]
            for reject_tld in filters.get("reject_for_local", []):
                if domain.endswith(reject_tld):
                    return (
                        FilterReason.WRONG_COUNTRY,
                        f"Foreign domain for {self.country}: {reject_tld}",
                    )

        # =================================================================
        # AI-FIRST BRIEF FILTERING (NEW)
        # Uses AI-generated criteria from ResearchIntelligenceBrief
        # =================================================================

        if self.research_brief and self.research_brief.confidence_score > 0:
            # Check exclusion patterns from AI brief
            for pattern in self.brief_exclusion_patterns:
                if pattern in combined:
                    return (
                        FilterReason.WRONG_ENTITY,
                        f"Brief exclusion: {pattern[:30]}",
                    )

            # Check entity identifiers from AI brief (high confidence only)
            high_conf_identifiers = [
                e
                for e in self.brief_entity_identifiers
                if e.get("confidence") == "high"
            ]
            if high_conf_identifiers:
                # For high-confidence identifiers, at least one should match
                matches_any = any(e["value"] in combined for e in high_conf_identifiers)
                # Only reject if we have substantial content but no matches
                if len(content) > 500 and not matches_any:
                    identifiers_str = ", ".join(
                        e["value"][:20] for e in high_conf_identifiers[:3]
                    )
                    return (
                        FilterReason.WRONG_ENTITY,
                        f"No match for identifiers: {identifiers_str}",
                    )

            # Check irrelevance keywords from AI brief
            irrelevance_count = sum(
                1 for kw in self.brief_irrelevance_keywords if kw in combined
            )
            relevance_count = sum(
                1 for kw in self.brief_relevance_keywords if kw in combined
            )

            # If mostly irrelevant keywords and few relevance keywords, reject
            if irrelevance_count >= 3 and relevance_count == 0:
                return (
                    FilterReason.IRRELEVANT,
                    f"Brief: {irrelevance_count} irrelevance markers, 0 relevance",
                )

        # =================================================================
        # CONTENT QUALITY (#6-10, #29-35)
        # =================================================================

        if self.strict_mode:
            # #8: Check paywall patterns
            for pattern in PAYWALL_PATTERNS:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    return (FilterReason.PAYWALL, "Paywall detected")

            # #31: Check login required patterns
            for pattern in LOGIN_PATTERNS:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    return (FilterReason.LOGIN_REQUIRED, "Login required")

        # =================================================================
        # DATA QUALITY (#36-42)
        # =================================================================

        if self.strict_mode:
            # #36: Check data recency
            recency_issue = self._check_recency(content)
            if recency_issue:
                return (FilterReason.OUTDATED, recency_issue)

        # Source passed all filters
        return None

    def _check_recency(self, content: str) -> Optional[str]:
        """
        Check if content contains only outdated data (#36).

        Returns None if recent data found, or issue description if outdated.
        """
        # Find all years mentioned in content
        years_found = [int(y) for y in self.YEAR_PATTERN.findall(content)]

        if not years_found:
            # No years found - can't determine recency, allow it
            return None

        # Check if any recent year is mentioned
        recent_years = [y for y in years_found if y >= self.min_year]
        old_years = [y for y in years_found if y < self.min_year]

        # If we found recent years, the source is fine
        if recent_years:
            return None

        # If only old years found and strict mode, flag as outdated
        if old_years:
            oldest = min(old_years)
            newest = max(old_years)
            if newest < self.min_year - 1:  # Allow 1 year grace period
                return f"Data from {oldest}-{newest}, need {self.min_year}+"

        return None

    def calculate_brief_relevance_score(self, source: ResearchSource) -> float:
        """
        Calculate relevance score for a source using AI brief criteria.

        Returns a score from 0.0 to 1.0 where higher is more relevant.
        """
        if not self.research_brief or self.research_brief.confidence_score <= 0:
            return 0.5  # Neutral if no brief

        title = (source.title or "").lower()
        content = (source.content or "").lower()[:2000]
        url = (source.url or "").lower()
        combined = f"{title} {content}"

        score = 0.5  # Start neutral

        # Boost for target domains
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            if any(td in domain for td in self.brief_target_domains):
                score += 0.2
        except Exception:
            pass

        # Boost for relevance keywords
        relevance_hits = sum(
            1 for kw in self.brief_relevance_keywords if kw in combined
        )
        if relevance_hits > 0:
            score += min(0.3, relevance_hits * 0.1)

        # Penalize for irrelevance keywords
        irrelevance_hits = sum(
            1 for kw in self.brief_irrelevance_keywords if kw in combined
        )
        if irrelevance_hits > 0:
            score -= min(0.3, irrelevance_hits * 0.1)

        # Boost for entity identifier matches
        for identifier in self.brief_entity_identifiers:
            if identifier["value"] in combined:
                if identifier.get("confidence") == "high":
                    score += 0.15
                else:
                    score += 0.05

        return max(0.0, min(1.0, score))

    def prioritize_sources(
        self,
        sources: List[ResearchSource],
        max_sources: Optional[int] = None,
    ) -> List[ResearchSource]:
        """
        Prioritize and optionally limit sources using AI brief criteria.

        Sources are sorted by relevance score (highest first).
        """
        if not sources:
            return sources

        # Calculate scores for all sources
        scored_sources = [
            (source, self.calculate_brief_relevance_score(source)) for source in sources
        ]

        # Sort by score descending
        scored_sources.sort(key=lambda x: x[1], reverse=True)

        # Log scoring if we have a brief
        if self.research_brief and self.research_brief.confidence_score > 0:
            logger.debug(
                f"Prioritized {len(sources)} sources using brief, "
                f"top score: {scored_sources[0][1]:.2f}, "
                f"bottom score: {scored_sources[-1][1]:.2f}"
            )

        # Extract sources in priority order
        prioritized = [s for s, _ in scored_sources]

        if max_sources and len(prioritized) > max_sources:
            return prioritized[:max_sources]

        return prioritized


# =============================================================================
# Quick Filter Functions
# =============================================================================


def quick_filter_sources(
    sources: List[ResearchSource],
) -> Tuple[List[ResearchSource], int]:
    """
    Quick filter to remove obviously failed sources.

    Use this for fast filtering without full entity validation.
    Returns (usable_sources, filtered_count).
    """
    usable = []
    filtered = 0

    for source in sources:
        title_lower = (source.title or "").lower().strip()
        content = source.content or ""

        is_failed = False

        # Check critical title patterns
        for pattern, _ in FAILED_TITLE_PATTERNS[:15]:  # Most important patterns
            if re.search(pattern, title_lower, re.IGNORECASE):
                is_failed = True
                break

        # Check for empty content
        if not is_failed and len(content.strip()) < 50:
            is_failed = True

        if is_failed:
            filtered += 1
            logger.debug(f"Quick filter removed: {source.url[:60]}...")
        else:
            usable.append(source)

    if filtered > 0:
        logger.info(
            f"Quick filter: removed {filtered} failed sources, kept {len(usable)}"
        )

    return usable, filtered


def filter_sources_for_synthesis(
    sources: List[ResearchSource],
    company_name: str,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    section_name: Optional[str] = None,
    research_brief: Optional[ResearchIntelligenceBrief] = None,
) -> List[ResearchSource]:
    """
    Filter sources before passing to AI synthesis.

    Convenience function that applies comprehensive filtering
    and returns only usable sources.

    Args:
        sources: List of sources to filter
        company_name: Target company name
        country: Target country for disambiguation
        industry: Target industry for disambiguation
        section_name: Optional section name for logging
        research_brief: AI-generated research brief for enhanced filtering
    """
    filter_instance = ComprehensiveSourceFilter(
        company_name=company_name,
        country=country,
        industry=industry,
        research_brief=research_brief,
    )

    result = filter_instance.filter_sources(sources, section_name)
    return result.usable_sources


def filter_sources_for_report(
    sources: List[ResearchSource],
    company_name: str,
    country: Optional[str] = None,
) -> List[ResearchSource]:
    """
    Filter sources before including in final report citations.

    Removes failed sources and wrong-entity sources from citations.
    """
    usable = []

    for source in sources:
        title_lower = (source.title or "").lower().strip()
        url_lower = (source.url or "").lower()

        # Skip failed sources
        skip = False
        for pattern, _ in FAILED_TITLE_PATTERNS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                skip = True
                break

        if skip:
            continue

        # Check entity rules if company is known
        company_lower = company_name.lower()
        for key, rules in COMPANY_DISAMBIGUATION.items():
            if key in company_lower:
                # Check rejected domains
                for domain in rules.get("reject_domains", []):
                    if domain in url_lower:
                        skip = True
                        break
                break

        if not skip:
            usable.append(source)

    return usable


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ComprehensiveSourceFilter",
    "FilterResult",
    "FilteredSource",
    "FilterReason",
    "quick_filter_sources",
    "filter_sources_for_synthesis",
    "filter_sources_for_report",
    "COMPANY_DISAMBIGUATION",
    "FAILED_TITLE_PATTERNS",
    "GENERIC_CONTENT_PATTERNS",
]
