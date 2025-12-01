# SEC-003: URL Validation Incomplete

## Priority: High
## Category: Security
## Status: Backlog

## Summary

URL validation exists but has gaps that could allow SSRF attacks through query parameters, fragments, or edge cases.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/tools/browser.py` | 90-101 | URL validation doesn't check all components |
| `src/core/url_validator.py` | 156-159 | DNS resolution blocks event loop |
| `src/pipeline/stages/fetch.py` | 169 | URLs from search not re-validated |

## Current Gaps

1. **Query parameter injection**: `http://safe.com?redirect=http://internal`
2. **Fragment bypass**: `http://safe.com#@internal.server`
3. **DNS rebinding**: Initial check passes, DNS changes before request
4. **IPv6 localhost**: `http://[::1]/` might bypass checks
5. **URL encoding**: `http://127.0.0.%31/` (encoded 1)

## Proposed Fix

```python
# src/core/url_validator.py

import ipaddress
from urllib.parse import urlparse, parse_qs, unquote
import socket

class URLValidator:
    BLOCKED_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0', '::1', '[::1]'}
    BLOCKED_SCHEMES = {'file', 'ftp', 'data', 'javascript', 'vbscript'}
    PRIVATE_RANGES = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),
        ipaddress.ip_network('169.254.0.0/16'),
        ipaddress.ip_network('fc00::/7'),
        ipaddress.ip_network('fe80::/10'),
        ipaddress.ip_network('::1/128'),
    ]

    @classmethod
    def validate_url_strict(cls, url: str) -> tuple[bool, str]:
        """Comprehensive URL validation for SSRF prevention."""
        # Decode URL to catch encoding bypasses
        url = unquote(url)

        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"URL parse error: {e}"

        # Check scheme
        if parsed.scheme.lower() in cls.BLOCKED_SCHEMES:
            return False, f"Blocked scheme: {parsed.scheme}"

        if parsed.scheme.lower() not in ('http', 'https'):
            return False, f"Only http/https allowed, got: {parsed.scheme}"

        # Check for credentials in URL
        if parsed.username or parsed.password:
            return False, "Credentials in URL not allowed"

        # Get hostname
        host = parsed.hostname
        if not host:
            return False, "No hostname in URL"

        # Normalize and check against blocklist
        host_lower = host.lower().strip('[]')
        if host_lower in cls.BLOCKED_HOSTS:
            return False, f"Blocked host: {host}"

        # Check if IP address
        try:
            ip = ipaddress.ip_address(host_lower)
            for network in cls.PRIVATE_RANGES:
                if ip in network:
                    return False, f"Private/internal IP: {ip}"
        except ValueError:
            # Not an IP, do DNS check
            pass

        # Check query parameters for URL injection
        if parsed.query:
            params = parse_qs(parsed.query)
            for key, values in params.items():
                for value in values:
                    if value.startswith(('http://', 'https://', '//')):
                        return False, f"URL in query parameter: {key}"

        return True, ""

    @classmethod
    async def validate_url_async(cls, url: str) -> tuple[bool, str]:
        """Async URL validation with DNS check."""
        import aiodns

        is_valid, error = cls.validate_url_strict(url)
        if not is_valid:
            return False, error

        # Async DNS resolution
        parsed = urlparse(url)
        resolver = aiodns.DNSResolver()

        try:
            result = await resolver.gethostbyname(parsed.hostname, socket.AF_INET)
            for ip_str in result.addresses:
                ip = ipaddress.ip_address(ip_str)
                for network in cls.PRIVATE_RANGES:
                    if ip in network:
                        return False, f"DNS resolves to private IP: {ip}"
        except Exception as e:
            return False, f"DNS resolution failed: {e}"

        return True, ""
```

## Implementation Tasks

- [ ] Add comprehensive URL decoding before validation
- [ ] Check query parameters for embedded URLs
- [ ] Add IPv6 localhost detection
- [ ] Install `aiodns` for async DNS resolution
- [ ] Add DNS rebinding protection (pin resolved IP)
- [ ] Create security tests for all bypass techniques
- [ ] Re-validate URLs from search results before fetch

## Success Criteria

- All URL bypass techniques blocked
- Async DNS resolution doesn't block event loop
- Security tests cover OWASP SSRF checklist
- No false positives on legitimate URLs
