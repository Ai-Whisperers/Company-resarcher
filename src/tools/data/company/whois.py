"""
WHOIS API Tool.

INT-006: Provides domain registration and ownership data.
https://www.whoisxmlapi.com/documentation/whois-api

Useful for verifying domain ownership and getting registration details.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class DomainInfo:
    """Domain registration information from WHOIS."""

    domain_name: str
    registrar: str = ""
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    status: List[str] = field(default_factory=list)
    name_servers: List[str] = field(default_factory=list)
    registrant_name: Optional[str] = None
    registrant_organization: Optional[str] = None
    registrant_country: Optional[str] = None
    registrant_state: Optional[str] = None
    registrant_city: Optional[str] = None
    admin_email: Optional[str] = None
    tech_email: Optional[str] = None
    dnssec: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class DomainVerification:
    """Result of domain ownership verification."""

    verified: bool
    domain: str
    expected_owner: str
    matched_field: Optional[str] = None
    registrant: Optional[str] = None
    reason: Optional[str] = None
    confidence: float = 0.0


@dataclass
class DomainAnalysis:
    """Complete domain analysis results."""

    info: Optional[DomainInfo] = None
    age_years: Optional[int] = None
    is_active: bool = False
    found: bool = False
    error: Optional[str] = None


class WhoisTool:
    """
    Tool for domain ownership lookup via WHOIS.

    Uses WHOISXML API for reliable WHOIS data. Provides domain
    registration details, registrant information, and verification.

    Usage:
        tool = WhoisTool()
        info = await tool.lookup_domain("claro.com.py")
        age = await tool.get_domain_age("example.com")
    """

    BASE_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize WHOIS tool.

        Args:
            api_key: WHOISXML API key (required for lookups)
        """
        self._api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._settings = get_settings()

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from settings or constructor."""
        if self._api_key:
            return self._api_key
        key = getattr(self._settings, "WHOIS_API_KEY", None)
        if key:
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    def is_available(self) -> bool:
        """Check if API is configured with a key."""
        return bool(self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not HAS_HTTPX:
            raise ImportError("httpx required. Install with: pip install httpx")

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def _extract_domain(self, url_or_domain: str) -> str:
        """Extract clean domain from URL or domain string."""
        # Handle URLs
        if url_or_domain.startswith(("http://", "https://")):
            parsed = urlparse(url_or_domain)
            domain = parsed.netloc
        else:
            domain = url_or_domain

        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Remove trailing slashes and paths
        domain = domain.split("/")[0]

        return domain.lower().strip()

    async def lookup_domain(self, domain: str) -> Optional[DomainInfo]:
        """
        Look up domain registration information.

        Args:
            domain: Domain name or URL (e.g., "claro.com.py" or "https://claro.com.py")

        Returns:
            DomainInfo if found, None otherwise
        """
        if not self.api_key:
            logger.warning("WHOIS API key not configured")
            return None

        clean_domain = self._extract_domain(domain)

        try:
            client = await self._get_client()
            response = await client.get(
                self.BASE_URL,
                params={
                    "apiKey": self.api_key,
                    "domainName": clean_domain,
                    "outputFormat": "JSON",
                },
            )

            if response.status_code != 200:
                logger.error(f"WHOIS API error: {response.status_code}")
                return None

            data = response.json()
            return self._parse_whois(data, clean_domain)

        except Exception as e:
            logger.error(f"WHOIS lookup failed for {domain}: {e}")
            return None

    async def get_domain_age(self, domain: str) -> Optional[int]:
        """
        Get domain age in years.

        Args:
            domain: Domain name to check

        Returns:
            Age in years, or None if not found
        """
        info = await self.lookup_domain(domain)
        if info and info.creation_date:
            age_days = (datetime.now() - info.creation_date).days
            return age_days // 365
        return None

    async def verify_domain_ownership(
        self,
        domain: str,
        expected_owner: str,
    ) -> DomainVerification:
        """
        Verify if domain is owned by expected organization.

        Checks registrant name/organization against expected owner.

        Args:
            domain: Domain to verify
            expected_owner: Expected owner name/organization

        Returns:
            DomainVerification with match result and details
        """
        info = await self.lookup_domain(domain)

        if not info:
            return DomainVerification(
                verified=False,
                domain=domain,
                expected_owner=expected_owner,
                reason="lookup_failed",
            )

        expected_lower = expected_owner.lower()
        org = info.registrant_organization or ""
        name = info.registrant_name or ""

        # Check organization match
        if org and expected_lower in org.lower():
            return DomainVerification(
                verified=True,
                domain=domain,
                expected_owner=expected_owner,
                matched_field="registrant_organization",
                registrant=org,
                confidence=0.9,
            )

        # Check name match
        if name and expected_lower in name.lower():
            return DomainVerification(
                verified=True,
                domain=domain,
                expected_owner=expected_owner,
                matched_field="registrant_name",
                registrant=name,
                confidence=0.8,
            )

        # No match
        registrant = org or name or "PRIVATE/REDACTED"
        return DomainVerification(
            verified=False,
            domain=domain,
            expected_owner=expected_owner,
            reason="no_match",
            registrant=registrant,
            confidence=0.0,
        )

    async def analyze_domain(self, domain: str) -> DomainAnalysis:
        """
        Get complete domain analysis.

        Args:
            domain: Domain to analyze

        Returns:
            DomainAnalysis with info, age, and status
        """
        if not self.is_available():
            return DomainAnalysis(
                found=False,
                error="WHOIS API key not configured",
            )

        try:
            info = await self.lookup_domain(domain)

            if not info:
                return DomainAnalysis(found=False)

            age_years = None
            if info.creation_date:
                age_days = (datetime.now() - info.creation_date).days
                age_years = age_days // 365

            # Check if domain is active (not expired)
            is_active = True
            if info.expiration_date and info.expiration_date < datetime.now():
                is_active = False

            return DomainAnalysis(
                info=info,
                age_years=age_years,
                is_active=is_active,
                found=True,
            )

        except Exception as e:
            logger.error(f"Domain analysis failed for {domain}: {e}")
            return DomainAnalysis(found=False, error=str(e))

    def _parse_whois(self, data: Dict[str, Any], domain: str) -> Optional[DomainInfo]:
        """Parse WHOIS API response into DomainInfo."""
        whois = data.get("WhoisRecord", {})
        if not whois:
            return None

        registrant = whois.get("registrant", {})
        admin = whois.get("administrativeContact", {})
        tech = whois.get("technicalContact", {})

        # Parse status list
        status_str = whois.get("status", "")
        status_list = status_str.split() if status_str else []

        # Parse name servers
        ns_data = whois.get("nameServers", {})
        name_servers = ns_data.get("hostNames", []) if isinstance(ns_data, dict) else []

        return DomainInfo(
            domain_name=domain,
            registrar=whois.get("registrarName", ""),
            creation_date=self._parse_date(whois.get("createdDate")),
            expiration_date=self._parse_date(whois.get("expiresDate")),
            updated_date=self._parse_date(whois.get("updatedDate")),
            status=status_list,
            name_servers=name_servers,
            registrant_name=registrant.get("name"),
            registrant_organization=registrant.get("organization"),
            registrant_country=registrant.get("country"),
            registrant_state=registrant.get("state"),
            registrant_city=registrant.get("city"),
            admin_email=admin.get("email"),
            tech_email=tech.get("email"),
            dnssec=whois.get("dnssec"),
            raw_text=whois.get("rawText"),
        )

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse various date formats from WHOIS response."""
        if not date_str:
            return None

        # Common date formats in WHOIS data
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d",
            "%d-%b-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str[:len(fmt) + 5], fmt)
            except (ValueError, TypeError):
                continue

        logger.debug(f"Could not parse date: {date_str}")
        return None

    def format_for_research(self, analysis: DomainAnalysis) -> str:
        """
        Format domain analysis for research reports.

        Args:
            analysis: DomainAnalysis to format

        Returns:
            Formatted markdown string
        """
        if not analysis.found:
            if analysis.error:
                return f"## Domain Ownership\n\n*Error: {analysis.error}*\n"
            return "## Domain Ownership\n\n*No WHOIS data found.*\n"

        info = analysis.info
        lines = []

        lines.append(f"## Domain Ownership: {info.domain_name}\n")

        # Registration details
        lines.append(f"- **Registrar**: {info.registrar or 'Unknown'}")

        if info.creation_date:
            lines.append(f"- **Created**: {info.creation_date.strftime('%Y-%m-%d')}")
        if analysis.age_years is not None:
            lines.append(f"- **Age**: {analysis.age_years} years")
        if info.expiration_date:
            lines.append(f"- **Expires**: {info.expiration_date.strftime('%Y-%m-%d')}")

        status = "Active" if analysis.is_active else "Expired"
        lines.append(f"- **Status**: {status}")

        # Registrant info
        if info.registrant_organization or info.registrant_name:
            lines.append("\n### Registrant\n")
            if info.registrant_organization:
                lines.append(f"- **Organization**: {info.registrant_organization}")
            if info.registrant_name:
                lines.append(f"- **Name**: {info.registrant_name}")
            if info.registrant_country:
                location = info.registrant_country
                if info.registrant_state:
                    location = f"{info.registrant_state}, {location}"
                if info.registrant_city:
                    location = f"{info.registrant_city}, {location}"
                lines.append(f"- **Location**: {location}")

        # Name servers
        if info.name_servers:
            lines.append("\n### Name Servers\n")
            for ns in info.name_servers[:4]:
                lines.append(f"- {ns}")

        return "\n".join(lines)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance management
_whois_tool_instance: Optional[WhoisTool] = None
_whois_tool_lock = None

try:
    import threading

    _whois_tool_lock = threading.Lock()
except ImportError:
    pass


def get_shared_whois_tool() -> WhoisTool:
    """Get or create the shared WhoisTool instance (thread-safe)."""
    global _whois_tool_instance
    if _whois_tool_instance is None:
        if _whois_tool_lock:
            with _whois_tool_lock:
                if _whois_tool_instance is None:
                    _whois_tool_instance = WhoisTool()
        else:
            _whois_tool_instance = WhoisTool()
    return _whois_tool_instance


def reset_whois_tool():
    """Reset the shared WhoisTool instance (useful for testing)."""
    global _whois_tool_instance
    if _whois_tool_lock:
        with _whois_tool_lock:
            _whois_tool_instance = None
    else:
        _whois_tool_instance = None
