"""
Domain Reputation Scoring (IMP-007: Enhanced Source Quality Scoring).

Provides domain-based reputation scoring for research sources.
Helps filter out low-quality, spammy, or unreliable sources.

Usage:
    from src.core.domain_reputation import DomainReputationScorer, get_domain_scorer

    scorer = get_domain_scorer()
    score = scorer.get_reputation(url)  # Returns 0.0 - 1.0
    is_trusted = scorer.is_trusted(url)
"""

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, Set, Optional, List
from urllib.parse import urlparse

from .logger import setup_logger

logger = setup_logger("domain_reputation")


# Default trusted domains (high-quality sources)
DEFAULT_TRUSTED_DOMAINS: Set[str] = {
    # Major news outlets
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "nytimes.com",
    "ft.com",
    "economist.com",
    "forbes.com",
    "fortune.com",
    "businessinsider.com",
    "cnbc.com",
    "bbc.com",
    "theguardian.com",
    # Financial data providers
    "sec.gov",
    "yahoo.com",
    "finance.yahoo.com",
    "marketwatch.com",
    "morningstar.com",
    "seekingalpha.com",
    "investing.com",
    "tradingview.com",
    # Business databases
    "crunchbase.com",
    "pitchbook.com",
    "owler.com",
    "zoominfo.com",
    "linkedin.com",
    "glassdoor.com",
    # Tech/Industry news
    "techcrunch.com",
    "wired.com",
    "theverge.com",
    "arstechnica.com",
    "venturebeat.com",
    "zdnet.com",
    # Official sources
    "gov",  # Any .gov domain
    "edu",  # Any .edu domain
    "github.com",
    "wikipedia.org",
    # Patent/Legal
    "patents.google.com",
    "uspto.gov",
}

# Domains to block entirely (spam, SEO farms, low quality)
DEFAULT_BLOCKED_DOMAINS: Set[str] = {
    # Known spam/SEO farms
    "medium.com",  # Quality varies widely
    "quora.com",  # Often low quality answers
    "pinterest.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "tiktok.com",
    # Generic aggregators
    "prlog.org",
    "prnewswire.com",
    "businesswire.com",
    "globenewswire.com",
    # Low-quality directories
    "yellowpages.com",
    "yelp.com",
    "manta.com",
    # Known content farms
    "ehow.com",
    "wikihow.com",
    "answers.com",
}

# Spam indicators in content
SPAM_INDICATORS: List[str] = [
    "casino",
    "gambling",
    "payday loan",
    "erectile",
    "viagra",
    "crypto scam",
    "get rich quick",
    "work from home",
    "click here to claim",
    "limited time offer",
    "act now",
    "congratulations you won",
]


@dataclass
class DomainReputationScorer:
    """
    Scores domain reputation for source quality filtering.

    Uses a combination of:
    - Domain allowlist (trusted sources)
    - Domain blocklist (known spam/low quality)
    - TLD-based scoring
    - Content heuristics
    """

    trusted_domains: Set[str] = field(default_factory=lambda: DEFAULT_TRUSTED_DOMAINS.copy())
    blocked_domains: Set[str] = field(default_factory=lambda: DEFAULT_BLOCKED_DOMAINS.copy())
    spam_indicators: List[str] = field(default_factory=lambda: SPAM_INDICATORS.copy())

    # Scoring weights
    base_score: float = 0.5
    trusted_bonus: float = 0.4
    blocked_penalty: float = -1.0  # Results in 0.0 score
    gov_edu_bonus: float = 0.35
    https_bonus: float = 0.05

    def extract_domain(self, url: str) -> str:
        """Extract the base domain from a URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    def get_tld(self, domain: str) -> str:
        """Get the top-level domain."""
        parts = domain.split(".")
        return parts[-1] if parts else ""

    def is_trusted(self, url: str) -> bool:
        """Check if URL is from a trusted domain."""
        domain = self.extract_domain(url)
        if not domain:
            return False

        # Check exact match
        if domain in self.trusted_domains:
            return True

        # Check if parent domain is trusted
        parts = domain.split(".")
        for i in range(len(parts)):
            parent = ".".join(parts[i:])
            if parent in self.trusted_domains:
                return True

        # Check TLD
        tld = self.get_tld(domain)
        if tld in ("gov", "edu"):
            return True

        return False

    def is_blocked(self, url: str) -> bool:
        """Check if URL is from a blocked domain."""
        domain = self.extract_domain(url)
        if not domain:
            return False

        # Check exact match
        if domain in self.blocked_domains:
            return True

        # Check if parent domain is blocked
        parts = domain.split(".")
        for i in range(len(parts)):
            parent = ".".join(parts[i:])
            if parent in self.blocked_domains:
                return True

        return False

    def has_spam_content(self, content: str) -> bool:
        """Check if content contains spam indicators."""
        content_lower = content.lower()
        for indicator in self.spam_indicators:
            if indicator in content_lower:
                return True
        return False

    def calculate_content_density(self, html: str, text: str) -> float:
        """
        Calculate text-to-HTML ratio as a quality indicator.

        Higher ratio = more actual content vs. boilerplate.
        """
        html_len = len(html) if html else 1
        text_len = len(text) if text else 0
        ratio = text_len / html_len
        # Normalize to 0-1 range (typical good ratio is 0.1-0.3)
        return min(1.0, ratio * 3)

    def get_reputation(
        self,
        url: str,
        content: Optional[str] = None,
        html: Optional[str] = None,
    ) -> float:
        """
        Calculate reputation score for a URL (0.0 - 1.0).

        Args:
            url: The URL to score
            content: Optional text content for spam detection
            html: Optional HTML for content density calculation

        Returns:
            Score from 0.0 (blocked/spam) to 1.0 (highly trusted)
        """
        # Check blocklist first
        if self.is_blocked(url):
            logger.debug(f"Blocked domain: {url[:50]}")
            return 0.0

        # Start with base score
        score = self.base_score

        # Trusted domain bonus
        if self.is_trusted(url):
            score += self.trusted_bonus

        # TLD bonuses
        domain = self.extract_domain(url)
        tld = self.get_tld(domain)
        if tld in ("gov", "edu"):
            score += self.gov_edu_bonus

        # HTTPS bonus
        if url.startswith("https://"):
            score += self.https_bonus

        # Content-based penalties
        if content:
            # Spam content penalty
            if self.has_spam_content(content):
                score -= 0.3
                logger.debug(f"Spam indicators found in: {url[:50]}")

            # Short content penalty
            word_count = len(content.split())
            if word_count < 50:
                score -= 0.2
            elif word_count < 100:
                score -= 0.1

        # Content density scoring
        if html and content:
            density = self.calculate_content_density(html, content)
            if density < 0.1:
                score -= 0.1  # Very low density = lots of boilerplate

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    def add_trusted_domain(self, domain: str) -> None:
        """Add a domain to the trusted list."""
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        self.trusted_domains.add(domain)
        logger.info(f"Added trusted domain: {domain}")

    def add_blocked_domain(self, domain: str) -> None:
        """Add a domain to the blocked list."""
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        self.blocked_domains.add(domain)
        logger.info(f"Added blocked domain: {domain}")

    def get_stats(self) -> Dict:
        """Get scorer statistics."""
        return {
            "trusted_count": len(self.trusted_domains),
            "blocked_count": len(self.blocked_domains),
            "spam_indicator_count": len(self.spam_indicators),
        }


@lru_cache()
def get_domain_scorer() -> DomainReputationScorer:
    """Get cached domain reputation scorer instance."""
    scorer = DomainReputationScorer()

    # Load custom domains from environment
    custom_trusted = os.getenv("TRUSTED_DOMAINS", "")
    if custom_trusted:
        for domain in custom_trusted.split(","):
            scorer.add_trusted_domain(domain.strip())

    custom_blocked = os.getenv("BLOCKED_DOMAINS", "")
    if custom_blocked:
        for domain in custom_blocked.split(","):
            scorer.add_blocked_domain(domain.strip())

    return scorer


def clear_domain_scorer():
    """Clear cached scorer (useful for testing)."""
    get_domain_scorer.cache_clear()


__all__ = [
    "DomainReputationScorer",
    "get_domain_scorer",
    "clear_domain_scorer",
    "DEFAULT_TRUSTED_DOMAINS",
    "DEFAULT_BLOCKED_DOMAINS",
]
