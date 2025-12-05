# SEC-001: Input Validation Improvements

## Priority: Medium
## Category: Security
## Status: Backlog

## Summary

While basic input validation exists, there are opportunities to strengthen validation across the application to prevent edge cases and potential security issues.

## Current State

### Implemented (Good)
- URL validation via `src/core/url_validator.py` (SSRF protection)
- Pydantic models for API request validation
- SQL injection prevention via SQLAlchemy ORM
- SecretStr for sensitive configuration

### Needs Improvement

| Area | Issue | Risk |
|------|-------|------|
| Company name | No length limit | DoS via long strings |
| Search queries | No sanitization | Query injection |
| Industry field | No validation | Free-form input |
| URL paths | Basic validation | Potential edge cases |

## Proposed Improvements

### 1. Enhanced Pydantic Models

```python
# src/api/models.py
from pydantic import BaseModel, Field, HttpUrl, field_validator
import re

class ResearchRequest(BaseModel):
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Company name to research"
    )
    url: HttpUrl | None = Field(
        None,
        description="Company website URL"
    )
    industry: str | None = Field(
        None,
        max_length=100,
        description="Industry sector"
    )

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        # Remove potentially dangerous characters
        v = v.strip()
        if not re.match(r'^[\w\s\-\.\,\&\'\(\)]+$', v):
            raise ValueError("Company name contains invalid characters")
        return v

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Whitelist common industries or allow alphanumeric
        v = v.strip()
        if not re.match(r'^[\w\s\-\/]+$', v):
            raise ValueError("Industry contains invalid characters")
        return v
```

### 2. Search Query Sanitization

```python
# src/tools/search.py
import re

def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent injection.

    - Limit length
    - Remove special operators
    - Escape quotes
    """
    # Limit length
    query = query[:500]

    # Remove common search operators that could be abused
    query = re.sub(r'(site:|inurl:|filetype:|intitle:)', '', query)

    # Remove excessive whitespace
    query = ' '.join(query.split())

    return query
```

### 3. URL Validation Enhancement

```python
# src/core/url_validator.py (additions)

BLOCKED_TLDS = {'.local', '.internal', '.localhost'}
BLOCKED_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0', '::1'}

def validate_url_strict(url: str) -> tuple[bool, str]:
    """
    Strict URL validation for external resources.

    Returns:
        (is_valid, error_message)
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"

        # Must be http/https
        if parsed.scheme not in ('http', 'https'):
            return False, f"Invalid scheme: {parsed.scheme}"

        # Check blocked hosts
        host = parsed.hostname or ''
        if host.lower() in BLOCKED_HOSTS:
            return False, f"Blocked host: {host}"

        # Check blocked TLDs
        for tld in BLOCKED_TLDS:
            if host.endswith(tld):
                return False, f"Blocked TLD: {tld}"

        # Check for IP addresses (could be internal)
        import ipaddress
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                return False, f"Private/reserved IP: {host}"
        except ValueError:
            pass  # Not an IP, that's fine

        return True, ""

    except Exception as e:
        return False, f"URL validation error: {e}"
```

## Implementation Tasks

- [ ] Add length limits to all string inputs
- [ ] Implement company name character validation
- [ ] Add search query sanitization
- [ ] Enhance URL validation with IP checks
- [ ] Add industry field whitelist/validation
- [ ] Write tests for validation edge cases
- [ ] Document validation rules

## Success Criteria

- All string inputs have length limits
- Special characters properly handled
- Search queries sanitized
- URL validation blocks internal addresses
- Validation errors return clear messages
- 100% test coverage on validation logic
