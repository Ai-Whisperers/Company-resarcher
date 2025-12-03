"""
URL validation utilities to prevent SSRF and other URL-based attacks.
"""

import asyncio
import ipaddress
import os
import socket
from typing import Set, Optional
from urllib.parse import urlparse, parse_qs, unquote

from ..logging import setup_logger

logger = setup_logger("url_validator")

# DNS resolution timeout in seconds (configurable)
DNS_TIMEOUT_SECONDS = int(os.getenv("DNS_TIMEOUT_SECONDS", "5"))


class URLValidationError(Exception):
    """Raised when URL validation fails."""

    def __init__(self, message: str, url: str):
        self.url = url
        super().__init__(message)


class URLValidator:
    """
    Validates URLs to prevent SSRF attacks.
    Blocks access to internal networks, cloud metadata endpoints, and dangerous protocols.
    """

    # Blocked IP ranges (private networks, localhost, link-local, cloud metadata)
    BLOCKED_IP_RANGES = [
        ipaddress.ip_network("127.0.0.0/8"),  # Localhost IPv4
        ipaddress.ip_network("10.0.0.0/8"),  # Private Class A
        ipaddress.ip_network("172.16.0.0/12"),  # Private Class B
        ipaddress.ip_network("192.168.0.0/16"),  # Private Class C
        ipaddress.ip_network("169.254.0.0/16"),  # Link-local / Cloud metadata
        ipaddress.ip_network("0.0.0.0/8"),  # Current network
        ipaddress.ip_network("100.64.0.0/10"),  # Shared address space (CGN)
        ipaddress.ip_network("192.0.0.0/24"),  # IETF protocol assignments
        ipaddress.ip_network("192.0.2.0/24"),  # Documentation (TEST-NET-1)
        ipaddress.ip_network("198.51.100.0/24"),  # Documentation (TEST-NET-2)
        ipaddress.ip_network("203.0.113.0/24"),  # Documentation (TEST-NET-3)
        ipaddress.ip_network("224.0.0.0/4"),  # Multicast
        ipaddress.ip_network("240.0.0.0/4"),  # Reserved
        ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
        # IPv6
        ipaddress.ip_network("::1/128"),  # Localhost IPv6
        ipaddress.ip_network("fc00::/7"),  # Unique local addresses
        ipaddress.ip_network("fe80::/10"),  # Link-local IPv6
        ipaddress.ip_network("ff00::/8"),  # Multicast IPv6
    ]

    # Allowed URL schemes
    ALLOWED_SCHEMES: Set[str] = {"http", "https"}

    # Blocked hostnames (partial matches)
    # NOTE: Patterns like ".lan" must NOT match legitimate domains like "lanacion.com.py"
    # We check for exact TLD match, not substring match
    BLOCKED_HOSTNAME_PATTERNS = [
        "localhost",
        "metadata",
        "internal",
        "kubernetes",
        "docker",
        ".local",
        ".internal",
        # Removed ".lan" - was causing false positives on domains like lanacion.com.py
    ]

    # TLDs that indicate local/internal networks (checked as exact suffix match)
    BLOCKED_TLDS = {
        ".lan",
        ".local",
        ".internal",
        ".localhost",
        ".home",
        ".corp",
        ".private",
    }

    # Known cloud metadata endpoints
    BLOCKED_HOSTNAMES = {
        "metadata.google.internal",
        "metadata.gcp.internal",
        "169.254.169.254",
        "fd00:ec2::254",
        "metadata.azure.internal",
        "100.100.100.200",  # Alibaba Cloud
    }

    @classmethod
    def _check_hostname_blocked(cls, hostname: str, url: str) -> None:
        """Check if hostname matches any blocked patterns."""
        hostname_normalized = hostname.strip("[]").lower()

        if hostname in cls.BLOCKED_HOSTNAMES or hostname_normalized in cls.BLOCKED_HOSTNAMES:
            raise URLValidationError(f"Blocked hostname: {hostname}", url)

        # Check for blocked TLDs (exact suffix match to avoid false positives)
        # e.g., ".lan" should block "server.lan" but NOT "lanacion.com.py"
        for blocked_tld in cls.BLOCKED_TLDS:
            if hostname_normalized.endswith(blocked_tld):
                raise URLValidationError(
                    f"Hostname has blocked TLD '{blocked_tld}'", url
                )

        # Check other blocked patterns (substring match)
        for pattern in cls.BLOCKED_HOSTNAME_PATTERNS:
            if pattern in hostname:
                raise URLValidationError(
                    f"Hostname matches blocked pattern '{pattern}'", url
                )

    @classmethod
    def _check_query_params(cls, query: str, url: str) -> None:
        """Check query parameters for URL injection attacks."""
        if not query:
            return

        try:
            params = parse_qs(query)
            for key, values in params.items():
                for value in values:
                    if value.startswith(("http://", "https://", "//")):
                        raise URLValidationError(
                            f"URL detected in query parameter '{key}'", url
                        )
                    if "://" in value:
                        raise URLValidationError(
                            f"Potential URL injection in parameter '{key}'", url
                        )
        except URLValidationError:
            raise
        except Exception as e:
            logger.debug(f"Could not parse query params: {e}")

    @classmethod
    def validate_url(cls, url: str, allow_redirects: bool = False) -> str:
        """
        Validate a URL for safety before making requests.

        Args:
            url: The URL to validate
            allow_redirects: Whether redirects will be followed (affects logging)

        Returns:
            The validated URL (unchanged if valid)

        Raises:
            URLValidationError: If the URL fails validation
        """
        if not url or not isinstance(url, str):
            raise URLValidationError("URL is empty or not a string", url or "")

        url = url.strip()

        # Decode URL to catch encoding bypasses (e.g., %31%32%37 for 127)
        try:
            decoded_url = unquote(url)
        except Exception:
            decoded_url = url

        try:
            parsed = urlparse(decoded_url)
        except Exception as e:
            raise URLValidationError(f"Failed to parse URL: {e}", url)

        # Validate scheme
        if parsed.scheme not in cls.ALLOWED_SCHEMES:
            raise URLValidationError(
                f"Blocked scheme '{parsed.scheme}'. Allowed: {cls.ALLOWED_SCHEMES}",
                url,
            )

        # Block credentials in URL (potential for auth bypass/injection)
        if parsed.username or parsed.password:
            raise URLValidationError("Credentials in URL not allowed", url)

        # Validate hostname exists
        if not parsed.hostname:
            raise URLValidationError("URL has no hostname", url)

        hostname = parsed.hostname.lower()
        hostname_normalized = hostname.strip("[]")

        # Check hostname against blocklists
        cls._check_hostname_blocked(hostname, url)

        # Check query parameters for injection
        cls._check_query_params(parsed.query, url)

        # Resolve hostname to IP and validate
        try:
            ip_str = cls._resolve_hostname(hostname_normalized)
            if ip_str:
                cls._validate_ip(ip_str, url)
        except URLValidationError:
            raise
        except Exception as e:
            logger.warning(f"Could not resolve hostname {hostname}: {e}")

        logger.debug(f"URL validated successfully: {url}")
        return url

    @classmethod
    def _resolve_hostname(cls, hostname: str) -> Optional[str]:
        """
        Resolve a hostname to an IP address (synchronous version).

        Args:
            hostname: The hostname to resolve

        Returns:
            IP address as string, or None if resolution fails
        """
        try:
            # First check if hostname is already an IP
            ipaddress.ip_address(hostname)
            return hostname
        except ValueError:
            pass

        try:
            ip = socket.gethostbyname(hostname)
            return ip
        except socket.gaierror:
            return None

    @classmethod
    async def _resolve_hostname_async(cls, hostname: str) -> Optional[str]:
        """
        Resolve a hostname to an IP address asynchronously with timeout and caching.

        Uses asyncio.to_thread() to avoid blocking the event loop.

        Args:
            hostname: The hostname to resolve

        Returns:
            IP address as string, or None if resolution fails
        """
        try:
            # First check if hostname is already an IP
            ipaddress.ip_address(hostname)
            return hostname
        except ValueError:
            pass

        # Check cache first
        cached = _dns_cache_get(hostname)
        if cached is not None:
            return cached if cached != "" else None

        try:
            # Run blocking DNS lookup in thread pool with timeout
            ip = await asyncio.wait_for(
                asyncio.to_thread(socket.gethostbyname, hostname),
                timeout=DNS_TIMEOUT_SECONDS
            )
            _dns_cache_set(hostname, ip)
            return ip
        except asyncio.TimeoutError:
            logger.warning(f"DNS resolution timed out for {hostname} after {DNS_TIMEOUT_SECONDS}s")
            _dns_cache_set(hostname, "")  # Cache negative result
            return None
        except socket.gaierror as e:
            logger.debug(f"DNS resolution failed for {hostname}: {e}")
            _dns_cache_set(hostname, "")  # Cache negative result
            return None


# Simple DNS cache with TTL
_dns_cache: dict = {}
_dns_cache_ttl = 300  # 5 minutes


def _dns_cache_get(hostname: str) -> Optional[str]:
    """Get cached DNS result if not expired."""
    import time
    if hostname in _dns_cache:
        ip, timestamp = _dns_cache[hostname]
        if time.time() - timestamp < _dns_cache_ttl:
            return ip
        del _dns_cache[hostname]
    return None


def _dns_cache_set(hostname: str, ip: str) -> None:
    """Cache DNS result with timestamp."""
    import time
    _dns_cache[hostname] = (ip, time.time())


# Continue URLValidator class methods (placed here due to cache functions above)
# These are added back to the class via setattr at module load
def _validate_ip(cls, ip_str: str, url: str) -> None:
    """
    Validate an IP address against blocked ranges.

    Args:
        ip_str: IP address as string
        url: Original URL (for error messages)

    Raises:
        URLValidationError: If IP is in a blocked range
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError as e:
        raise URLValidationError(f"Invalid IP address '{ip_str}': {e}", url)

    for blocked_range in cls.BLOCKED_IP_RANGES:
        if ip_obj in blocked_range:
            raise URLValidationError(
                f"IP {ip_str} is in blocked range {blocked_range}", url
            )


def _validate_redirect_url(cls, original_url: str, redirect_url: str) -> str:
    """
    Validate a redirect URL, ensuring it doesn't redirect to blocked targets.

    Args:
        original_url: The original requested URL
        redirect_url: The redirect target URL

    Returns:
        The validated redirect URL

    Raises:
        URLValidationError: If the redirect URL fails validation
    """
    logger.debug(f"Validating redirect from {original_url} to {redirect_url}")
    return cls.validate_url(redirect_url, allow_redirects=True)


def _is_safe_url(cls, url: str) -> bool:
    """
    Check if a URL is safe without raising exceptions.

    Args:
        url: The URL to check

    Returns:
        True if the URL is safe, False otherwise
    """
    try:
        cls.validate_url(url)
        return True
    except URLValidationError:
        return False


# Re-attach methods to URLValidator class
URLValidator._validate_ip = classmethod(_validate_ip)
URLValidator.validate_redirect_url = classmethod(_validate_redirect_url)
URLValidator.is_safe_url = classmethod(_is_safe_url)
