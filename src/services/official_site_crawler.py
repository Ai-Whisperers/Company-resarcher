"""
Official Site Crawler - Comprehensive crawling of company websites.

When we detect a URL from the company's official website, this service:
1. Identifies the website domain
2. Discovers important pages (sitemap, common paths, internal links)
3. Crawls each page to extract comprehensive data
4. Tracks crawled pages to avoid duplicates across runs

This ensures we get ALL available data from official sources.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

from ..core.logger import setup_logger
from ..core.types import ResearchSource

logger = setup_logger("official_site_crawler")


@dataclass
class DiscoveredPage:
    """A page discovered on the official website."""
    url: str
    path: str
    page_type: str  # "sitemap", "common_path", "internal_link", "robots"
    priority: int  # 1=high value (about, investors), 2=medium, 3=low
    title: Optional[str] = None
    discovered_from: Optional[str] = None  # URL where we found this link


@dataclass
class CrawlResult:
    """Result of crawling the official website."""
    company_name: str
    base_url: str
    pages_discovered: int
    pages_crawled: int
    pages_skipped_seen: int
    pages_failed: int
    sources: List[ResearchSource]
    duration_seconds: float
    discovered_pages: List[DiscoveredPage] = field(default_factory=list)
    data_extracted: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Important paths commonly found on company websites
# =============================================================================

# High-priority pages (likely to have key company data)
HIGH_PRIORITY_PATHS = [
    # About/Company Info
    "/about", "/about-us", "/aboutus", "/company", "/who-we-are",
    "/quienes-somos", "/sobre-nosotros", "/acerca-de", "/institucional",
    "/nosotros", "/empresa",

    # Leadership/Team
    "/team", "/leadership", "/management", "/executives", "/directors",
    "/equipo", "/directivos", "/liderazgo",

    # Investors/Financials
    "/investors", "/investor-relations", "/ir", "/financials",
    "/annual-report", "/financial-reports", "/inversionistas",
    "/relacion-inversionistas", "/informes-financieros",

    # Press/News
    "/news", "/newsroom", "/press", "/press-releases", "/media",
    "/noticias", "/sala-de-prensa", "/comunicados",

    # Products/Services
    "/products", "/services", "/solutions", "/offerings",
    "/productos", "/servicios", "/soluciones", "/planes",

    # Contact/Locations
    "/contact", "/contact-us", "/locations", "/offices",
    "/contacto", "/contactenos", "/ubicaciones", "/sucursales",

    # Careers (for employee count hints)
    "/careers", "/jobs", "/work-with-us", "/join-us",
    "/carreras", "/empleos", "/trabaja-con-nosotros",

    # Corporate/Legal
    "/corporate", "/governance", "/compliance",
    "/corporativo", "/gobierno-corporativo",
]

# Medium-priority paths
MEDIUM_PRIORITY_PATHS = [
    "/history", "/historia", "/timeline",
    "/partners", "/socios", "/alianzas",
    "/awards", "/recognition", "/premios",
    "/sustainability", "/csr", "/responsabilidad-social",
    "/technology", "/innovation", "/tecnologia", "/innovacion",
    "/coverage", "/cobertura", "/network", "/red",
    "/faq", "/help", "/support", "/ayuda", "/soporte",
    "/blog", "/articles", "/articulos",
]

# Telecom-specific paths
TELECOM_PATHS = [
    "/planes", "/plans", "/tarifas", "/rates", "/pricing",
    "/prepago", "/prepaid", "/postpago", "/postpaid",
    "/roaming", "/internacional", "/international",
    "/cobertura", "/coverage", "/network-coverage",
    "/4g", "/5g", "/lte", "/fibra", "/fiber",
    "/movil", "/mobile", "/fijo", "/landline",
    "/internet", "/banda-ancha", "/broadband",
    "/tv", "/television", "/streaming",
    "/empresas", "/business", "/corporate", "/pymes", "/sme",
]


class OfficialSiteCrawler:
    """
    Crawls company official websites comprehensively.

    Usage:
        crawler = OfficialSiteCrawler(
            company_name="Claro Paraguay",
            company_website="https://www.claro.com.py",
            source_registry=registry,
        )
        result = await crawler.crawl()

        # Get all discovered sources
        for source in result.sources:
            print(f"{source.title}: {source.url}")
    """

    def __init__(
        self,
        company_name: str,
        company_website: str,
        source_registry=None,
        browser_tool=None,
        max_pages: int = 50,
        max_depth: int = 2,
    ):
        """
        Initialize the crawler.

        Args:
            company_name: Name of the company
            company_website: Base URL of company website
            source_registry: Optional PersistentSourceRegistry to check/store URLs
            browser_tool: Optional browser tool (lazy loaded if not provided)
            max_pages: Maximum pages to crawl per run
            max_depth: Maximum link depth to follow from homepage
        """
        self.company_name = company_name
        self.company_website = self._normalize_base_url(company_website)
        self.base_domain = self._extract_domain(self.company_website)
        self._source_registry = source_registry
        self._browser_tool = browser_tool
        self.max_pages = max_pages
        self.max_depth = max_depth

        # Track state
        self._discovered_pages: Dict[str, DiscoveredPage] = {}
        self._crawled_urls: Set[str] = set()
        self._failed_urls: Set[str] = set()

        logger.info(
            f"OfficialSiteCrawler initialized for {company_name}: {self.company_website}"
        )

    def _normalize_base_url(self, url: str) -> str:
        """Normalize the base URL."""
        url = url.strip().lower()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        # Remove trailing slash
        return url.rstrip("/")

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

    def is_official_url(self, url: str) -> bool:
        """Check if a URL belongs to the company's official website."""
        try:
            domain = self._extract_domain(url)
            # Check if domain matches or is subdomain
            return (
                domain == self.base_domain or
                domain.endswith("." + self.base_domain)
            )
        except Exception:
            return False

    async def _get_browser_tool(self):
        """Lazy load browser tool."""
        if self._browser_tool is None:
            from ..tools import get_shared_browser_tool
            self._browser_tool = get_shared_browser_tool()
        return self._browser_tool

    async def crawl(self) -> CrawlResult:
        """
        Crawl the official website comprehensively using wave-based discovery.

        This method:
        1. Discovers initial pages (sitemap, common paths)
        2. Crawls pages in priority order
        3. Discovers new links from each crawled page
        4. Continues crawling newly discovered pages until max_pages

        Returns:
            CrawlResult with all discovered and crawled pages
        """
        start_time = datetime.now()
        sources: List[ResearchSource] = []
        pages_skipped = 0
        crawled_count = 0

        logger.info(f"Starting comprehensive crawl of {self.company_website}")

        # Phase 1: Discover initial pages
        await self._discover_pages()
        initial_count = len(self._discovered_pages)
        logger.info(f"Initial discovery: {initial_count} potential pages")

        browser = await self._get_browser_tool()

        # Track which URLs we've already processed (crawled or skipped)
        processed_urls: Set[str] = set()

        # Wave-based crawling: keep processing until max_pages or no more pages
        wave = 0
        while crawled_count < self.max_pages:
            wave += 1

            # Get uncrawled pages sorted by priority
            uncrawled = [
                page for url, page in self._discovered_pages.items()
                if url not in processed_urls
            ]

            if not uncrawled:
                logger.info(f"No more pages to crawl after wave {wave}")
                break

            # Sort by priority
            uncrawled.sort(key=lambda p: (p.priority, p.path))

            pages_this_wave = 0
            links_discovered_this_wave = 0

            for page in uncrawled:
                if crawled_count >= self.max_pages:
                    logger.info(f"Reached max pages limit ({self.max_pages})")
                    break

                processed_urls.add(page.url)

                # Check if already seen in registry
                if self._source_registry and self._source_registry.is_url_seen(page.url):
                    pages_skipped += 1
                    logger.debug(f"Skipping already-seen: {page.url}")
                    continue

                # Skip if already crawled (shouldn't happen, but safety check)
                if page.url in self._crawled_urls:
                    continue

                # Crawl the page
                try:
                    result = await browser.fetch(page.url)
                    content = result.get("content", "")
                    title = result.get("title", page.title or page.path)

                    if content and len(content) > 100:
                        source = ResearchSource(
                            url=page.url,
                            title=title,
                            content=content,
                            source_type="official",
                        )
                        sources.append(source)
                        self._crawled_urls.add(page.url)
                        crawled_count += 1
                        pages_this_wave += 1

                        # Register in source registry
                        if self._source_registry:
                            self._source_registry.add_source(
                                url=page.url,
                                content=content,
                                title=title,
                                data_types_found=self._infer_data_types(page.path, content),
                                usefulness_score=0.9,  # High score for official pages
                            )

                        logger.info(f"Crawled [{page.page_type}]: {page.path}")

                        # Discover new internal links from this page
                        new_links = await self._discover_links_from_content(page.url, content)
                        links_discovered_this_wave += new_links

                    else:
                        self._failed_urls.add(page.url)
                        logger.debug(f"Empty content: {page.url}")

                except Exception as e:
                    self._failed_urls.add(page.url)
                    logger.warning(f"Failed to crawl {page.url}: {e}")

                # Rate limiting
                await asyncio.sleep(0.5)

            logger.info(
                f"Wave {wave}: crawled {pages_this_wave} pages, "
                f"discovered {links_discovered_this_wave} new links"
            )

            # If we didn't discover any new links this wave, we can stop
            if links_discovered_this_wave == 0 and pages_this_wave > 0:
                logger.info("No new links discovered, completing crawl")
                break

        duration = (datetime.now() - start_time).total_seconds()
        total_discovered = len(self._discovered_pages)

        logger.info(
            f"Crawl complete: {crawled_count} pages crawled from {total_discovered} discovered, "
            f"{pages_skipped} skipped, {len(self._failed_urls)} failed, "
            f"duration: {duration:.1f}s"
        )

        return CrawlResult(
            company_name=self.company_name,
            base_url=self.company_website,
            pages_discovered=total_discovered,
            pages_crawled=crawled_count,
            pages_skipped_seen=pages_skipped,
            pages_failed=len(self._failed_urls),
            sources=sources,
            duration_seconds=duration,
            discovered_pages=list(self._discovered_pages.values()),
        )

    async def _discover_pages(self) -> None:
        """Discover pages from sitemap, robots.txt, and common paths."""

        # Try to fetch sitemap
        await self._discover_from_sitemap()

        # Try robots.txt for more sitemaps
        await self._discover_from_robots()

        # Add common high-value paths
        for path in HIGH_PRIORITY_PATHS:
            url = urljoin(self.company_website, path)
            if url not in self._discovered_pages:
                self._discovered_pages[url] = DiscoveredPage(
                    url=url,
                    path=path,
                    page_type="common_path",
                    priority=1,
                )

        # Add medium priority paths
        for path in MEDIUM_PRIORITY_PATHS:
            url = urljoin(self.company_website, path)
            if url not in self._discovered_pages:
                self._discovered_pages[url] = DiscoveredPage(
                    url=url,
                    path=path,
                    page_type="common_path",
                    priority=2,
                )

        # Add telecom-specific paths
        for path in TELECOM_PATHS:
            url = urljoin(self.company_website, path)
            if url not in self._discovered_pages:
                self._discovered_pages[url] = DiscoveredPage(
                    url=url,
                    path=path,
                    page_type="common_path",
                    priority=2,
                )

        # Always include homepage
        if self.company_website not in self._discovered_pages:
            self._discovered_pages[self.company_website] = DiscoveredPage(
                url=self.company_website,
                path="/",
                page_type="homepage",
                priority=1,
            )

    async def _discover_from_sitemap(self) -> None:
        """Try to discover pages from sitemap.xml."""
        sitemap_urls = [
            f"{self.company_website}/sitemap.xml",
            f"{self.company_website}/sitemap_index.xml",
            f"{self.company_website}/sitemap/sitemap.xml",
        ]

        browser = await self._get_browser_tool()

        for sitemap_url in sitemap_urls:
            try:
                result = await browser.fetch(sitemap_url)
                content = result.get("content", "")

                if content and "<url>" in content.lower():
                    # Parse sitemap XML
                    urls = self._parse_sitemap_xml(content)
                    for url, priority in urls:
                        if self.is_official_url(url) and url not in self._discovered_pages:
                            path = urlparse(url).path or "/"
                            self._discovered_pages[url] = DiscoveredPage(
                                url=url,
                                path=path,
                                page_type="sitemap",
                                priority=priority,
                                discovered_from=sitemap_url,
                            )

                    logger.info(f"Found {len(urls)} URLs in sitemap: {sitemap_url}")
                    break  # Stop if we found a working sitemap

            except Exception as e:
                logger.debug(f"Sitemap not found at {sitemap_url}: {e}")

    def _parse_sitemap_xml(self, content: str) -> List[Tuple[str, int]]:
        """Parse sitemap XML and extract URLs with priorities."""
        urls = []

        try:
            # Handle XML namespaces
            content = re.sub(r'xmlns="[^"]+"', '', content)
            root = ET.fromstring(content)

            for url_elem in root.iter():
                if url_elem.tag.endswith("url") or url_elem.tag == "url":
                    loc = None
                    priority = 2  # Default medium priority

                    for child in url_elem:
                        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        if tag == "loc" and child.text:
                            loc = child.text.strip()
                        elif tag == "priority" and child.text:
                            try:
                                p = float(child.text)
                                priority = 1 if p >= 0.7 else (2 if p >= 0.4 else 3)
                            except ValueError:
                                pass

                    if loc:
                        urls.append((loc, priority))

        except ET.ParseError as e:
            logger.debug(f"Failed to parse sitemap XML: {e}")
            # Fallback: extract URLs with regex
            url_matches = re.findall(r'<loc>([^<]+)</loc>', content)
            urls = [(url.strip(), 2) for url in url_matches]

        return urls

    async def _discover_from_robots(self) -> None:
        """Try to discover sitemaps from robots.txt."""
        robots_url = f"{self.company_website}/robots.txt"
        browser = await self._get_browser_tool()

        try:
            result = await browser.fetch(robots_url)
            content = result.get("content", "")

            if content:
                # Look for Sitemap: directives
                sitemap_matches = re.findall(r'Sitemap:\s*(\S+)', content, re.IGNORECASE)
                for sitemap_url in sitemap_matches:
                    if sitemap_url not in self._discovered_pages:
                        # Fetch this sitemap
                        try:
                            sm_result = await browser.fetch(sitemap_url)
                            sm_content = sm_result.get("content", "")
                            if sm_content and "<url>" in sm_content.lower():
                                urls = self._parse_sitemap_xml(sm_content)
                                for url, priority in urls:
                                    if self.is_official_url(url) and url not in self._discovered_pages:
                                        path = urlparse(url).path or "/"
                                        self._discovered_pages[url] = DiscoveredPage(
                                            url=url,
                                            path=path,
                                            page_type="sitemap",
                                            priority=priority,
                                            discovered_from=sitemap_url,
                                        )
                                logger.info(f"Found {len(urls)} URLs from robots.txt sitemap")
                        except Exception:
                            pass

        except Exception as e:
            logger.debug(f"robots.txt not found: {e}")

    async def _discover_links_from_content(self, source_url: str, content: str) -> int:
        """
        Discover ALL internal links from page HTML content.

        Extracts links from:
        - <a href="..."> tags
        - <link rel="canonical" href="...">
        - <meta property="og:url" content="...">
        - Navigation menus, footer links
        - Inline onclick="location.href='...'" patterns
        - JSON-LD structured data

        Returns:
            Number of new links discovered
        """
        discovered_count = 0
        candidate_urls: Set[str] = set()

        # Pattern 1: Standard href attributes (a, link, area tags)
        href_patterns = [
            r'<a[^>]+href=["\']([^"\'#][^"\']*)["\']',  # anchor tags
            r'<link[^>]+href=["\']([^"\']+)["\']',       # link tags
            r'<area[^>]+href=["\']([^"\']+)["\']',       # area tags (image maps)
        ]

        # Pattern 2: Form actions
        href_patterns.append(r'<form[^>]+action=["\']([^"\']+)["\']')

        # Pattern 3: Meta redirects and canonical
        href_patterns.append(r'<meta[^>]+url=([^"\'>\s]+)')
        href_patterns.append(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:url["\']')
        href_patterns.append(r'property=["\']og:url["\'][^>]*content=["\']([^"\']+)["\']')

        # Pattern 4: JavaScript location patterns
        js_patterns = [
            r'location\.href\s*=\s*["\']([^"\']+)["\']',
            r'window\.location\s*=\s*["\']([^"\']+)["\']',
            r'location\.replace\s*\(\s*["\']([^"\']+)["\']',
            r'window\.open\s*\(\s*["\']([^"\']+)["\']',
        ]

        # Pattern 5: Data attributes often used for SPA navigation
        data_patterns = [
            r'data-href=["\']([^"\']+)["\']',
            r'data-url=["\']([^"\']+)["\']',
            r'data-link=["\']([^"\']+)["\']',
            r'data-navigate=["\']([^"\']+)["\']',
        ]

        # Pattern 6: JSON-LD structured data URLs
        json_ld_patterns = [
            r'"url"\s*:\s*"([^"]+)"',
            r'"@id"\s*:\s*"([^"]+)"',
            r'"mainEntityOfPage"\s*:\s*"([^"]+)"',
        ]

        # Extract from all patterns
        all_patterns = href_patterns + js_patterns + data_patterns + json_ld_patterns

        for pattern in all_patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match:
                        candidate_urls.add(match.strip())
            except Exception:
                continue

        # Also extract from common navigation structures
        # Look for <nav>, <header>, <footer> sections which often have key links
        nav_sections = re.findall(
            r'<(?:nav|header|footer|menu)[^>]*>(.*?)</(?:nav|header|footer|menu)>',
            content, re.IGNORECASE | re.DOTALL
        )
        for section in nav_sections:
            nav_links = re.findall(r'href=["\']([^"\']+)["\']', section, re.IGNORECASE)
            candidate_urls.update(nav_links)

        # Process all candidate URLs
        excluded_extensions = {
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".ico", ".svg",
            ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".otf",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm",
            ".zip", ".rar", ".tar", ".gz", ".7z",
        }

        excluded_prefixes = {
            "javascript:", "mailto:", "tel:", "sms:", "whatsapp:",
            "data:", "blob:", "about:", "#",
        }

        for url in candidate_urls:
            try:
                # Skip empty or invalid
                if not url or len(url) < 2:
                    continue

                # Skip excluded prefixes
                url_lower = url.lower().strip()
                if any(url_lower.startswith(prefix) for prefix in excluded_prefixes):
                    continue

                # Resolve relative URLs
                full_url = urljoin(source_url, url)

                # Normalize: remove fragment, lowercase domain
                parsed = urlparse(full_url)
                # Remove fragment
                normalized_url = parsed._replace(fragment="").geturl()

                # Only internal links
                if not self.is_official_url(normalized_url):
                    continue

                # Skip already discovered
                if normalized_url in self._discovered_pages:
                    continue

                # Skip excluded extensions
                path = parsed.path.lower()
                if any(path.endswith(ext) for ext in excluded_extensions):
                    continue

                # Skip very long URLs (often tracking/session URLs)
                if len(normalized_url) > 250:
                    continue

                # Skip URLs with too many query params (often filters/pagination)
                if normalized_url.count("&") > 3:
                    continue

                # Determine priority based on path keywords
                priority = self._infer_path_priority(parsed.path)

                self._discovered_pages[normalized_url] = DiscoveredPage(
                    url=normalized_url,
                    path=parsed.path or "/",
                    page_type="internal_link",
                    priority=priority,
                    discovered_from=source_url,
                )
                discovered_count += 1

            except Exception:
                continue

        if discovered_count > 0:
            logger.debug(f"Discovered {discovered_count} new links from {source_url}")

        return discovered_count

    def _infer_path_priority(self, path: str) -> int:
        """Infer page priority from its path."""
        path_lower = path.lower()

        # High priority keywords
        high_keywords = [
            "about", "investor", "financ", "news", "press",
            "contact", "team", "leader", "manage", "director",
            "quienes", "nosotros", "empresa", "institucional",
        ]
        if any(kw in path_lower for kw in high_keywords):
            return 1

        # Medium priority
        medium_keywords = [
            "product", "service", "solution", "plan", "precio",
            "precio", "tarifa", "cobertura", "blog", "partner",
        ]
        if any(kw in path_lower for kw in medium_keywords):
            return 2

        return 3

    def _infer_data_types(self, path: str, content: str) -> Set[str]:
        """Infer what data types might be found on this page."""
        data_types = set()
        path_lower = path.lower()
        content_lower = content.lower()

        # Path-based inference
        if any(kw in path_lower for kw in ["about", "quienes", "nosotros", "empresa"]):
            data_types.update(["company_info", "founded", "mission", "vision"])
        if any(kw in path_lower for kw in ["investor", "financ", "annual"]):
            data_types.update(["revenue", "profit", "financial"])
        if any(kw in path_lower for kw in ["team", "leader", "director", "ejecutivo"]):
            data_types.update(["executives", "leadership"])
        if any(kw in path_lower for kw in ["career", "empleo", "trabajo"]):
            data_types.add("employees")
        if any(kw in path_lower for kw in ["news", "press", "noticia"]):
            data_types.add("news")
        if any(kw in path_lower for kw in ["plan", "precio", "tarifa", "servicio"]):
            data_types.update(["products", "pricing"])
        if any(kw in path_lower for kw in ["cobertura", "coverage", "network"]):
            data_types.add("coverage")

        # Content-based inference
        if any(kw in content_lower for kw in ["revenue", "ingresos", "millones", "billions"]):
            data_types.add("revenue")
        if any(kw in content_lower for kw in ["employee", "empleado", "colaborador"]):
            data_types.add("employees")
        if any(kw in content_lower for kw in ["founded", "fundada", "desde", "established"]):
            data_types.add("founded")
        if any(kw in content_lower for kw in ["subscriber", "suscriptor", "usuario", "cliente"]):
            data_types.add("subscribers")
        if any(kw in content_lower for kw in ["market share", "cuota de mercado"]):
            data_types.add("market_share")

        return data_types


# =============================================================================
# Factory and Utility Functions
# =============================================================================

def detect_official_website(url: str, company_name: str, known_website: Optional[str] = None) -> bool:
    """
    Detect if a URL is from the company's official website.

    Args:
        url: URL to check
        company_name: Company name
        known_website: Known official website (if any)

    Returns:
        True if URL appears to be official
    """
    url_lower = url.lower()
    company_lower = company_name.lower()

    # If we know the official website, check against it
    if known_website:
        known_domain = urlparse(known_website.lower()).netloc.replace("www.", "")
        url_domain = urlparse(url_lower).netloc.replace("www.", "")
        if known_domain and (url_domain == known_domain or url_domain.endswith("." + known_domain)):
            return True

    # Heuristic: company name in domain
    url_domain = urlparse(url_lower).netloc.replace("www.", "")
    company_words = company_lower.split()

    # Check if main company name word is in domain
    for word in company_words:
        if len(word) >= 4 and word in url_domain:
            # Additional check: not a review/comparison site
            if not any(bad in url_domain for bad in [
                "review", "compare", "vs", "wikipedia", "linkedin",
                "crunchbase", "glassdoor", "reddit", "trustpilot"
            ]):
                return True

    return False


async def crawl_official_site(
    company_name: str,
    company_website: str,
    source_registry=None,
    max_pages: int = 50,
) -> CrawlResult:
    """
    Convenience function to crawl a company's official website.

    Args:
        company_name: Company name
        company_website: Base URL of official website
        source_registry: Optional source registry
        max_pages: Maximum pages to crawl

    Returns:
        CrawlResult with all sources
    """
    crawler = OfficialSiteCrawler(
        company_name=company_name,
        company_website=company_website,
        source_registry=source_registry,
        max_pages=max_pages,
    )
    return await crawler.crawl()


def get_priority_paths_for_data(needed_data: List[str]) -> List[str]:
    """
    Get priority paths to crawl based on needed data types.

    Args:
        needed_data: List of data fields needed (e.g., ["Revenue", "Employees"])

    Returns:
        List of paths most likely to contain that data
    """
    data_to_paths = {
        "Revenue": ["/investors", "/investor-relations", "/financials", "/annual-report"],
        "Profit": ["/investors", "/investor-relations", "/financials"],
        "Employees": ["/about", "/about-us", "/careers", "/company"],
        "Founded": ["/about", "/about-us", "/history", "/company"],
        "Mission": ["/about", "/about-us", "/company", "/quienes-somos"],
        "Vision": ["/about", "/about-us", "/company", "/quienes-somos"],
        "Subscribers": ["/investors", "/about", "/company"],
        "Market Share": ["/investors", "/press", "/news"],
        "Headquarters": ["/about", "/contact", "/company"],
        "Leadership": ["/team", "/leadership", "/about", "/management"],
    }

    paths = set()
    for data_type in needed_data:
        if data_type in data_to_paths:
            paths.update(data_to_paths[data_type])

    return list(paths)


__all__ = [
    "OfficialSiteCrawler",
    "CrawlResult",
    "DiscoveredPage",
    "detect_official_website",
    "crawl_official_site",
    "get_priority_paths_for_data",
]
