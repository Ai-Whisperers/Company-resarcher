"""
Domain Filtering - Irrelevant domain blocklist (PERF-012).

Filters out domains that consistently return irrelevant results,
particularly for non-English research in Latin American markets.
"""

import os
import threading
from dataclasses import dataclass
from typing import Set, Dict, Optional, List
from urllib.parse import urlparse

from ..logging import setup_logger

logger = setup_logger("domain_filter")


@dataclass
class FilterStats:
    """Statistics about domain filtering."""
    total_checked: int = 0
    blocked_count: int = 0
    blocked_by_domain: Dict[str, int] = None

    def __post_init__(self):
        if self.blocked_by_domain is None:
            self.blocked_by_domain = {}


class DomainFilter:
    """
    Filters out irrelevant domains before fetching.

    Maintains a blocklist of domains that consistently return:
    - Foreign language content unrelated to target market
    - Forum spam / low-quality content
    - Sites that require login / block scrapers

    Usage:
        filter = DomainFilter()
        if filter.should_fetch(url):
            result = await browser.fetch_page(url)
        else:
            logger.info(f"Blocked irrelevant domain: {url}")
    """

    # Static blocklist of irrelevant domains (PERF-012)
    # Domains that consistently return irrelevant results for Latin American research
    BLOCKED_DOMAINS: Set[str] = {
        # Chinese sites (irrelevant for Spanish/Portuguese markets)
        "zhihu.com",
        "baidu.com",
        "tieba.baidu.com",
        "zhidao.baidu.com",
        "weibo.com",
        "bilibili.com",
        "163.com",
        "qq.com",
        "sina.com.cn",
        "sohu.com",
        "csdn.net",
        "jianshu.com",
        "douban.com",
        "taobao.com",
        "tmall.com",
        "jd.com",
        "1688.com",
        "sogou.com",
        "iqiyi.com",
        "youku.com",
        "hupu.com",
        "zhibo8.cc",
        "btime.com",
        "thepaper.cn",

        # German/European forums (irrelevant for LatAm research)
        "photovoltaikforum.com",
        "heise.de",
        "golem.de",
        "chip.de",
        "computerbild.de",
        "gutefrage.net",
        "mydealz.de",
        "stern.de",
        "spiegel.de",
        "focus.de",

        # Russian sites
        "yandex.ru",
        "mail.ru",
        "vk.com",
        "ok.ru",
        "pikabu.ru",
        "livejournal.com",
        "rambler.ru",
        "ria.ru",
        "tass.ru",

        # Japanese sites
        "yahoo.co.jp",
        "livedoor.jp",
        "ameblo.jp",
        "hatena.ne.jp",
        "rakuten.co.jp",
        "nicovideo.jp",
        "fc2.com",

        # Korean sites
        "naver.com",
        "daum.net",
        "tistory.com",
        "kakao.com",

        # Sites that block scrapers or require login
        "linkedin.com",
        "instagram.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "pinterest.com",
        "tiktok.com",
        "snapchat.com",
        "whatsapp.com",
        "telegram.org",

        # Job boards (usually behind login)
        "glassdoor.com",
        "indeed.com",
        "monster.com",
        "ziprecruiter.com",
        "careerbuilder.com",

        # Academic paywalls
        "jstor.org",
        "sciencedirect.com",
        "springer.com",
        "wiley.com",
        "ieee.org",
        "researchgate.net",
        "academia.edu",

        # Aggregators / low-quality content farms
        "quora.com",
        "answers.yahoo.com",
        "ehow.com",
        "wikihow.com",
        "answers.com",
        "ask.com",

        # Stock photo / media sites (no useful text content)
        "shutterstock.com",
        "gettyimages.com",
        "istockphoto.com",
        "alamy.com",
        "dreamstime.com",

        # App stores (require specific tools)
        "play.google.com",
        "apps.apple.com",
        "itunes.apple.com",

        # File sharing / download sites
        "mega.nz",
        "dropbox.com",
        "drive.google.com",
        "mediafire.com",

        # E-commerce (irrelevant for company research)
        "amazon.com",
        "ebay.com",
        "aliexpress.com",
        "alibaba.com",
        "mercadolibre.com",

        # Forums often with outdated/irrelevant content
        "reddit.com",  # Often blocked by rate limits anyway
        "stackexchange.com",
        "stackoverflow.com",
    }

    # URL path patterns that indicate irrelevant content
    BLOCKED_PATH_PATTERNS: List[str] = [
        "/zh-cn/",
        "/zh-tw/",
        "/de-de/",
        "/ru-ru/",
        "/ja-jp/",
        "/ko-kr/",
        "/zh/",
        "/cn/",
        "/de/",
        "/ru/",
        "/ja/",
        "/ko/",
        "/question/",  # Often Q&A sites with low-quality answers
        "/answers/",
        "/forum/",  # Forums often have outdated/irrelevant content
    ]

    def __init__(self, custom_blocklist: Optional[Set[str]] = None):
        """
        Initialize domain filter.

        Args:
            custom_blocklist: Additional domains to block
        """
        self._blocklist = self.BLOCKED_DOMAINS.copy()
        if custom_blocklist:
            self._blocklist.update(custom_blocklist)

        # Load additional domains from environment
        extra_blocked = os.getenv("BLOCKED_DOMAINS", "")
        if extra_blocked:
            for domain in extra_blocked.split(","):
                domain = domain.strip().lower()
                if domain:
                    self._blocklist.add(domain)

        self._stats = FilterStats()
        self._lock = threading.Lock()
        logger.info(f"Domain filter initialized with {len(self._blocklist)} blocked domains")

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]
            return domain
        except Exception:
            return ""

    def should_fetch(self, url: str, context: Optional[Dict] = None) -> bool:
        """
        Check if a URL should be fetched.

        Args:
            url: URL to check
            context: Optional context with target_country, target_language etc.

        Returns:
            True if URL should be fetched, False if it should be blocked
        """
        with self._lock:
            self._stats.total_checked += 1

        domain = self.extract_domain(url)
        if not domain:
            return True  # Can't parse, allow anyway

        # Check exact domain match
        if domain in self._blocklist:
            self._record_blocked(domain)
            logger.debug(f"Blocked domain (exact): {domain}")
            return False

        # Check if domain is a subdomain of blocked domain
        for blocked in self._blocklist:
            if domain.endswith("." + blocked):
                self._record_blocked(blocked)
                logger.debug(f"Blocked domain (subdomain of {blocked}): {domain}")
                return False

        # Check URL path patterns
        url_lower = url.lower()
        for pattern in self.BLOCKED_PATH_PATTERNS:
            if pattern in url_lower:
                self._record_blocked(f"pattern:{pattern}")
                logger.debug(f"Blocked URL pattern '{pattern}': {url}")
                return False

        return True

    def _record_blocked(self, domain: str) -> None:
        """Record a blocked domain for statistics."""
        with self._lock:
            self._stats.blocked_count += 1
            if domain not in self._stats.blocked_by_domain:
                self._stats.blocked_by_domain[domain] = 0
            self._stats.blocked_by_domain[domain] += 1

    def add_to_blocklist(self, domain: str) -> None:
        """
        Add a domain to the blocklist at runtime.

        Args:
            domain: Domain to block
        """
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        self._blocklist.add(domain)
        logger.info(f"Added domain to blocklist: {domain}")

    def get_stats(self) -> FilterStats:
        """Get filtering statistics."""
        with self._lock:
            return FilterStats(
                total_checked=self._stats.total_checked,
                blocked_count=self._stats.blocked_count,
                blocked_by_domain=self._stats.blocked_by_domain.copy(),
            )

    def get_blocklist(self) -> Set[str]:
        """Get current blocklist."""
        return self._blocklist.copy()


# Global domain filter instance
_domain_filter: Optional[DomainFilter] = None
_domain_filter_lock = threading.Lock()


def get_domain_filter() -> DomainFilter:
    """Get or create the global domain filter instance."""
    global _domain_filter
    if _domain_filter is None:
        with _domain_filter_lock:
            if _domain_filter is None:
                _domain_filter = DomainFilter()
    return _domain_filter


def is_domain_allowed(url: str) -> bool:
    """
    Quick check if a domain is allowed (not in blocklist).

    Args:
        url: URL to check

    Returns:
        True if domain is allowed, False if blocked
    """
    return get_domain_filter().should_fetch(url)
