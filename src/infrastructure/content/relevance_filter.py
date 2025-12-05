"""
Pre-Fetch Relevance Filter (PERF-017).

Scores search results for relevance BEFORE fetching to avoid wasting
time on irrelevant pages that would be filtered later anyway.

Enhanced with incremental research features:
- Already-seen URL penalty (for cross-run deduplication)
- Fills-gap bonus (prioritize URLs that target missing data)
- Integration with PersistentSourceRegistry
"""

import re
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from src.core.logging import setup_logger
from src.lib.url_utils.domain_filter import get_domain_filter

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from src.services.data import PersistentSourceRegistry

logger = setup_logger("relevance_filter")


@dataclass
class RelevanceScore:
    """Relevance score breakdown for a search result."""

    total: float
    company_in_title: float = 0.0
    company_in_snippet: float = 0.0
    country_match: float = 0.0
    domain_relevance: float = 0.0
    language_match: float = 0.0
    recency_bonus: float = 0.0
    blocked_penalty: float = 0.0
    # Incremental research scores
    already_seen_penalty: float = 0.0  # Penalty for URLs we've fetched before
    fills_gap_bonus: float = 0.0  # Bonus for URLs targeting known data gaps
    high_value_domain_bonus: float = (
        0.0  # Bonus for domains that provided useful data before
    )
    official_site_bonus: float = 0.0  # Bonus for company's official website URLs
    reason: str = ""
    # Metadata
    is_new_url: bool = True  # False if URL was seen in previous runs
    is_official_site: bool = False  # True if URL is from company's official website
    target_gaps: List[str] = field(default_factory=list)  # Data gaps this might fill


@dataclass
class FilterStats:
    """Statistics about relevance filtering."""

    total_scored: int = 0
    passed: int = 0
    filtered_low_score: int = 0
    filtered_blocked_domain: int = 0
    filtered_already_seen: int = 0  # URLs filtered because already fetched
    boosted_fills_gap: int = 0  # URLs boosted because they target gaps
    boosted_official_site: int = 0  # URLs boosted because they're from official site
    avg_score: float = 0.0


class RelevanceFilter:
    """
    Filters search results for relevance before fetching.

    Scores each search result based on:
    - Company name mention in title/snippet
    - Country/region relevance
    - Domain quality
    - Language indicators
    - Already-seen URL penalty (incremental mode)
    - Fills-gap bonus (incremental mode)

    Results below threshold are filtered out BEFORE browser fetch.

    Usage:
        # Basic usage
        filter = RelevanceFilter(company="Vox Paraguay", country="Paraguay")
        relevant_results = filter.filter_results(search_results)

        # Incremental mode with registry and gaps
        filter = RelevanceFilter(
            company="Vox Paraguay",
            country="Paraguay",
            source_registry=registry,  # PersistentSourceRegistry
            known_gaps=["Revenue", "Market Share"],  # Fields we need
        )
        relevant_results = filter.filter_results(search_results)
    """

    # Minimum score to pass filter
    DEFAULT_THRESHOLD = 0.3

    # Scoring weights (base)
    WEIGHTS = {
        "company_in_title": 0.30,  # Reduced slightly to make room for incremental scores
        "company_in_snippet": 0.12,
        "country_match": 0.12,
        "domain_relevance": 0.12,
        "language_match": 0.08,
        "recency_bonus": 0.08,
        # Incremental research weights
        "already_seen_penalty": -0.50,  # Heavy penalty for duplicate URLs
        "fills_gap_bonus": 0.25,  # Strong bonus for targeting missing data
        "high_value_domain_bonus": 0.10,  # Bonus for domains that worked well before
        "official_site_bonus": 0.35,  # Strong bonus for official company website URLs
    }

    # Country code to TLD mapping
    COUNTRY_TLDS = {
        "paraguay": [".py", ".com.py"],
        "argentina": [".ar", ".com.ar"],
        "chile": [".cl"],
        "mexico": [".mx", ".com.mx"],
        "brazil": [".br", ".com.br"],
        "colombia": [".co", ".com.co"],
        "peru": [".pe", ".com.pe"],
        "uruguay": [".uy", ".com.uy"],
        "ecuador": [".ec", ".com.ec"],
        "venezuela": [".ve", ".com.ve"],
        "usa": [".us", ".com"],
        "uk": [".uk", ".co.uk"],
    }

    # High-quality news/business domains
    QUALITY_DOMAINS = {
        "reuters.com",
        "bloomberg.com",
        "forbes.com",
        "wsj.com",
        "ft.com",
        "businessinsider.com",
        "techcrunch.com",
        "crunchbase.com",
        "pitchbook.com",
        "wikipedia.org",
        "sec.gov",
    }

    # Language indicators in URLs/content
    SPANISH_INDICATORS = ["/es/", "/es-", "spanish", "espanol", "español"]
    PORTUGUESE_INDICATORS = ["/pt/", "/pt-", "portuguese", "portugues", "português"]
    ENGLISH_INDICATORS = ["/en/", "/en-", "english"]

    # Negative language indicators (wrong language for LatAm)
    NEGATIVE_LANG_INDICATORS = [
        "/zh/",
        "/cn/",
        "/zh-cn/",
        "/zh-tw/",  # Chinese
        "/de/",
        "/de-de/",  # German
        "/ru/",
        "/ru-ru/",  # Russian
        "/ja/",
        "/ja-jp/",  # Japanese
        "/ko/",
        "/ko-kr/",  # Korean
        "/ar/",
        "/ar-",  # Arabic
    ]

    # Keywords that indicate content might fill specific data gaps
    GAP_KEYWORDS: Dict[str, List[str]] = {
        "Revenue": [
            "revenue",
            "ingresos",
            "sales",
            "ventas",
            "financial",
            "earnings",
            "facturación",
        ],
        "Market Share": [
            "market share",
            "cuota de mercado",
            "participación",
            "share %",
            "market position",
        ],
        "Subscribers": [
            "subscribers",
            "suscriptores",
            "usuarios",
            "customers",
            "abonados",
            "clientes",
        ],
        "TAM": ["total addressable market", "tam", "market size", "tamaño del mercado"],
        "SAM": ["serviceable available market", "sam", "addressable market"],
        "SOM": ["serviceable obtainable market", "som", "obtainable market"],
        "CAGR": ["cagr", "growth rate", "tasa de crecimiento", "compound annual"],
        "Employees": ["employees", "empleados", "workforce", "staff", "headcount"],
        "Founded": [
            "founded",
            "fundada",
            "established",
            "since",
            "year founded",
            "history",
        ],
        "ARPU": ["arpu", "average revenue per user", "ingreso promedio"],
        "Profit": ["profit", "net income", "ganancia", "utilidad", "earnings"],
    }

    def __init__(
        self,
        company: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        threshold: float = DEFAULT_THRESHOLD,
        source_registry: Optional["PersistentSourceRegistry"] = None,
        known_gaps: Optional[List[str]] = None,
        high_value_domains: Optional[Set[str]] = None,
        official_website: Optional[str] = None,
    ):
        """
        Initialize relevance filter.

        Args:
            company: Company name to search for
            country: Target country (for TLD/language matching)
            industry: Industry keywords (optional)
            threshold: Minimum score to pass filter
            source_registry: Optional PersistentSourceRegistry for incremental mode
            known_gaps: Optional list of data gaps we're trying to fill
            high_value_domains: Optional set of domains that provided useful data before
            official_website: Optional URL of company's official website for boosting
        """
        self.company = company.lower()
        self.company_words = set(self.company.split())
        self.country = country.lower() if country else None
        self.industry = industry.lower() if industry else None
        self.threshold = threshold
        self._stats = FilterStats()
        self._lock = threading.Lock()

        # Get domain filter for blocklist checking
        self._domain_filter = get_domain_filter()

        # Incremental research integration
        self._source_registry = source_registry
        self._known_gaps = set(known_gaps) if known_gaps else set()
        self._high_value_domains = high_value_domains or set()
        self._incremental_mode = source_registry is not None

        # Official website domain for boosting
        self._official_domain = self._extract_official_domain(official_website)

        # Build gap keyword lookup
        self._gap_keywords: Dict[str, Set[str]] = {}
        for gap in self._known_gaps:
            if gap in self.GAP_KEYWORDS:
                self._gap_keywords[gap] = {kw.lower() for kw in self.GAP_KEYWORDS[gap]}

        mode_str = "incremental" if self._incremental_mode else "standard"
        official_str = (
            f", official={self._official_domain}" if self._official_domain else ""
        )
        logger.info(
            f"Relevance filter initialized ({mode_str}): company='{company}', "
            f"country='{country}', threshold={threshold}, gaps={len(self._known_gaps)}{official_str}"
        )

    def calculate_score(
        self, result: Dict, target_query_gaps: Optional[List[str]] = None
    ) -> RelevanceScore:
        """
        Calculate relevance score for a search result.

        Args:
            result: Search result dict with url, title, snippet/content
            target_query_gaps: Optional list of gaps this query was targeting

        Returns:
            RelevanceScore with breakdown
        """
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        snippet = result.get("snippet", result.get("content", "")).lower()
        combined_text = f"{title} {snippet}"

        score = RelevanceScore(total=0.0)

        # Check blocked domain first
        if not self._domain_filter.should_fetch(url):
            score.blocked_penalty = -1.0
            score.total = 0.0
            score.reason = "Blocked domain"
            return score

        # =====================================================================
        # INCREMENTAL MODE: Check if URL already seen
        # =====================================================================
        if self._incremental_mode and self._source_registry:
            if self._source_registry.is_url_seen(url):
                score.already_seen_penalty = self.WEIGHTS["already_seen_penalty"]
                score.is_new_url = False
                logger.debug(f"URL already seen: {url[:60]}...")

        # Company name in title (highest weight)
        if self.company in title:
            score.company_in_title = self.WEIGHTS["company_in_title"]
        else:
            # Partial match - check if key words present
            title_words = set(title.split())
            matches = self.company_words & title_words
            if matches:
                score.company_in_title = self.WEIGHTS["company_in_title"] * (
                    len(matches) / len(self.company_words)
                )

        # Company name in snippet
        if self.company in snippet:
            score.company_in_snippet = self.WEIGHTS["company_in_snippet"]
        else:
            snippet_words = set(snippet.split())
            matches = self.company_words & snippet_words
            if matches:
                score.company_in_snippet = self.WEIGHTS["company_in_snippet"] * (
                    len(matches) / len(self.company_words)
                )

        # Country TLD matching
        if self.country:
            tlds = self.COUNTRY_TLDS.get(self.country, [])
            domain = urlparse(url).netloc
            for tld in tlds:
                if domain.endswith(tld):
                    score.country_match = self.WEIGHTS["country_match"]
                    break

        # Domain quality
        domain = self._extract_domain(url)
        if domain in self.QUALITY_DOMAINS:
            score.domain_relevance = self.WEIGHTS["domain_relevance"]

        # Language matching
        # Positive: Spanish/Portuguese for LatAm
        if any(ind in url for ind in self.SPANISH_INDICATORS):
            score.language_match = self.WEIGHTS["language_match"]
        elif any(ind in url for ind in self.PORTUGUESE_INDICATORS):
            score.language_match = self.WEIGHTS["language_match"]
        elif any(ind in url for ind in self.ENGLISH_INDICATORS):
            score.language_match = (
                self.WEIGHTS["language_match"] * 0.7
            )  # Slightly less for English
        # Negative: Wrong language
        elif any(ind in url for ind in self.NEGATIVE_LANG_INDICATORS):
            score.language_match = -0.2

        # Recency bonus (if published_date available)
        if "published_date" in result and result["published_date"]:
            # Recent articles get bonus
            score.recency_bonus = self.WEIGHTS["recency_bonus"]

        # =====================================================================
        # INCREMENTAL MODE: Check if content might fill known gaps
        # =====================================================================
        if self._incremental_mode and self._gap_keywords:
            matched_gaps = self._check_gap_keywords(combined_text, target_query_gaps)
            if matched_gaps:
                score.fills_gap_bonus = self.WEIGHTS["fills_gap_bonus"]
                score.target_gaps = matched_gaps
                with self._lock:
                    self._stats.boosted_fills_gap += 1

        # =====================================================================
        # INCREMENTAL MODE: Bonus for high-value domains
        # =====================================================================
        if self._incremental_mode and domain in self._high_value_domains:
            score.high_value_domain_bonus = self.WEIGHTS["high_value_domain_bonus"]

        # =====================================================================
        # OFFICIAL SITE: Strong bonus for company's official website URLs
        # =====================================================================
        if self._is_official_url(url):
            score.official_site_bonus = self.WEIGHTS["official_site_bonus"]
            score.is_official_site = True
            with self._lock:
                self._stats.boosted_official_site += 1
            logger.debug(f"Official site URL detected: {url[:60]}...")

        # Calculate total (including incremental scores)
        score.total = max(
            0.0,
            min(
                1.0,
                score.company_in_title
                + score.company_in_snippet
                + score.country_match
                + score.domain_relevance
                + score.language_match
                + score.recency_bonus
                + score.blocked_penalty
                + score.already_seen_penalty
                + score.fills_gap_bonus
                + score.high_value_domain_bonus
                + score.official_site_bonus,
            ),
        )

        # Set reason
        if score.total < self.threshold:
            reasons = []
            if score.company_in_title == 0 and score.company_in_snippet == 0:
                reasons.append("no company mention")
            if score.language_match < 0:
                reasons.append("wrong language")
            if score.already_seen_penalty < 0:
                reasons.append("already fetched")
            score.reason = ", ".join(reasons) if reasons else "low overall score"

        return score

    def _check_gap_keywords(
        self,
        text: str,
        target_query_gaps: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Check if text contains keywords that might fill known gaps.

        Args:
            text: Combined title + snippet text
            target_query_gaps: Gaps this query was specifically targeting

        Returns:
            List of gap names this content might fill
        """
        matched_gaps = []

        # First, check gaps from the target query
        if target_query_gaps:
            for gap in target_query_gaps:
                if gap in self._known_gaps:
                    matched_gaps.append(gap)

        # Then, check for keyword matches in text
        text_lower = text.lower()
        for gap_name, keywords in self._gap_keywords.items():
            if gap_name not in matched_gaps:  # Don't double-count
                for keyword in keywords:
                    if keyword in text_lower:
                        matched_gaps.append(gap_name)
                        break

        return matched_gaps

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    def _extract_official_domain(
        self, official_website: Optional[str]
    ) -> Optional[str]:
        """Extract the official domain from company website URL."""
        if not official_website:
            return None
        try:
            url = official_website.lower().strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if domain else None
        except Exception:
            return None

    def _is_official_url(self, url: str) -> bool:
        """Check if URL belongs to the company's official website."""
        if not self._official_domain:
            return False
        try:
            domain = self._extract_domain(url)
            # Check if domain matches or is a subdomain
            return domain == self._official_domain or domain.endswith(
                "." + self._official_domain
            )
        except Exception:
            return False

    def filter_results(
        self,
        results: List[Dict],
        max_results: Optional[int] = None,
        target_query_gaps: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Filter search results by relevance.

        Args:
            results: List of search result dicts
            max_results: Maximum results to return (optional)
            target_query_gaps: Optional list of gaps this query was targeting

        Returns:
            List of results that pass the relevance threshold
        """
        scored_results = []
        total_score = 0.0

        for result in results:
            score = self.calculate_score(result, target_query_gaps)

            with self._lock:
                self._stats.total_scored += 1
                total_score += score.total

            if score.total >= self.threshold:
                result["_relevance_score"] = score.total
                result["_is_new_url"] = score.is_new_url
                result["_target_gaps"] = score.target_gaps
                scored_results.append((score.total, result))
                with self._lock:
                    self._stats.passed += 1
            else:
                # Track why it was filtered
                if score.blocked_penalty < 0:
                    with self._lock:
                        self._stats.filtered_blocked_domain += 1
                elif score.already_seen_penalty < 0:
                    with self._lock:
                        self._stats.filtered_already_seen += 1
                else:
                    with self._lock:
                        self._stats.filtered_low_score += 1
                logger.debug(
                    f"Filtered result (score={score.total:.2f}): "
                    f"{result.get('url', 'unknown')[:60]} - {score.reason}"
                )

        # Update average score
        with self._lock:
            if self._stats.total_scored > 0:
                self._stats.avg_score = total_score / self._stats.total_scored

        # Sort by score and limit results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        filtered = [r[1] for r in scored_results]

        if max_results and len(filtered) > max_results:
            filtered = filtered[:max_results]

        # Log with incremental mode info
        mode_info = ""
        if self._incremental_mode:
            mode_info = f", {self._stats.filtered_already_seen} already-seen"
        logger.info(
            f"Relevance filter: {len(filtered)}/{len(results)} passed "
            f"(threshold={self.threshold}{mode_info})"
        )

        return filtered

    def get_stats(self) -> FilterStats:
        """Get filtering statistics."""
        with self._lock:
            return FilterStats(
                total_scored=self._stats.total_scored,
                passed=self._stats.passed,
                filtered_low_score=self._stats.filtered_low_score,
                filtered_blocked_domain=self._stats.filtered_blocked_domain,
                filtered_already_seen=self._stats.filtered_already_seen,
                boosted_fills_gap=self._stats.boosted_fills_gap,
                boosted_official_site=self._stats.boosted_official_site,
                avg_score=self._stats.avg_score,
            )

    def set_source_registry(self, registry: "PersistentSourceRegistry") -> None:
        """Set the source registry for incremental mode."""
        self._source_registry = registry
        self._incremental_mode = registry is not None

    def set_known_gaps(self, gaps: List[str]) -> None:
        """Update the list of known data gaps."""
        self._known_gaps = set(gaps)
        self._gap_keywords = {}
        for gap in self._known_gaps:
            if gap in self.GAP_KEYWORDS:
                self._gap_keywords[gap] = {kw.lower() for kw in self.GAP_KEYWORDS[gap]}

    def set_high_value_domains(self, domains: Set[str]) -> None:
        """Update the set of high-value domains."""
        self._high_value_domains = domains

    def set_official_website(self, official_website: str) -> None:
        """Set the official website URL for boosting."""
        self._official_domain = self._extract_official_domain(official_website)
        if self._official_domain:
            logger.info(f"Official website set: {self._official_domain}")


def create_relevance_filter(
    company: str,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    threshold: float = 0.3,
    source_registry: Optional["PersistentSourceRegistry"] = None,
    known_gaps: Optional[List[str]] = None,
    high_value_domains: Optional[Set[str]] = None,
    official_website: Optional[str] = None,
) -> RelevanceFilter:
    """
    Factory function to create a relevance filter.

    Args:
        company: Company name
        country: Target country
        industry: Industry keywords
        threshold: Minimum relevance score
        source_registry: Optional PersistentSourceRegistry for incremental mode
        known_gaps: Optional list of data gaps to prioritize
        high_value_domains: Optional set of domains that provided useful data
        official_website: Optional URL of company's official website for boosting

    Returns:
        Configured RelevanceFilter instance
    """
    return RelevanceFilter(
        company=company,
        country=country,
        industry=industry,
        threshold=threshold,
        source_registry=source_registry,
        known_gaps=known_gaps,
        high_value_domains=high_value_domains,
        official_website=official_website,
    )


def create_incremental_filter(
    company: str,
    country: str,
    base_dir: str = "outputs",
    industry: Optional[str] = None,
    threshold: float = 0.3,
    official_website: Optional[str] = None,
) -> RelevanceFilter:
    """
    Factory function to create an incremental relevance filter.

    Automatically loads the source registry and analyzes existing data
    to determine known gaps.

    Args:
        company: Company name
        country: Target country
        base_dir: Base output directory
        industry: Industry keywords
        threshold: Minimum relevance score
        official_website: Optional URL of company's official website for boosting

    Returns:
        Configured RelevanceFilter with incremental features enabled
    """
    from src.services.data import get_source_registry
    from src.services.research import get_data_analyzer

    # Load source registry
    registry = get_source_registry(company, base_dir)

    # Analyze existing data for gaps
    analyzer = get_data_analyzer(base_dir)
    analysis = analyzer.analyze_company(company)

    # Extract gap names
    known_gaps = [gap.field_name for gap in analysis.all_gaps]

    # Get high-value domains from registry
    high_value_sources = registry.get_high_value_sources(min_score=0.7)
    high_value_domains = set()
    for source in high_value_sources:
        try:
            from urllib.parse import urlparse

            domain = urlparse(source.url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            high_value_domains.add(domain)
        except Exception:
            pass

    return RelevanceFilter(
        company=company,
        country=country,
        industry=industry,
        threshold=threshold,
        source_registry=registry,
        known_gaps=known_gaps,
        high_value_domains=high_value_domains,
        official_website=official_website,
    )
