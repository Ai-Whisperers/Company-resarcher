"""
Security utilities for input sanitization and prompt injection prevention.
"""

import re
from typing import Optional


# Maximum lengths for different input types
MAX_COMPANY_NAME_LENGTH = 500
MAX_QUERY_LENGTH = 1000
MAX_CONTEXT_LENGTH = 50000

# Patterns that might indicate prompt injection attempts
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|above|all)\s+(instructions?|prompts?)", re.I),
    re.compile(r"disregard\s+(previous|above|all)", re.I),
    re.compile(r"forget\s+(everything|previous|above)", re.I),
    re.compile(r"new\s+instructions?:", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"<\s*system\s*>", re.I),
    re.compile(r"\[\s*INST\s*\]", re.I),
    re.compile(r"</?\s*s\s*>", re.I),  # Common LLM tokens
]


def sanitize_for_prompt(
    text: str,
    max_length: int = MAX_QUERY_LENGTH,
    strip_control_chars: bool = True,
    check_injection: bool = True,
) -> str:
    """
    Sanitize user input before including in AI prompts.

    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length (truncates if exceeded)
        strip_control_chars: Remove non-printable control characters
        check_injection: Log warning if injection patterns detected

    Returns:
        Sanitized text safe for prompt inclusion
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    sanitized = text.strip()

    # Remove control characters (keep printable + common whitespace)
    if strip_control_chars:
        sanitized = "".join(
            c for c in sanitized if c.isprintable() or c in "\n\t"
        )

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Check for injection patterns (log but don't block - could be legitimate)
    if check_injection:
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(sanitized):
                # Import here to avoid circular imports
                from ...core.logging import setup_logger
                logger = setup_logger("security")
                logger.warning(
                    f"Potential prompt injection pattern detected in input "
                    f"(length={len(sanitized)})"
                )
                break

    return sanitized


def sanitize_company_name(name: str) -> str:
    """
    Sanitize a company name for use in prompts.

    More restrictive than general sanitization - only allows
    alphanumeric characters, spaces, and common punctuation.
    """
    if not name:
        return ""

    # First apply general sanitization
    sanitized = sanitize_for_prompt(
        name,
        max_length=MAX_COMPANY_NAME_LENGTH,
        check_injection=True,
    )

    # Allow only safe characters for company names
    # Alphanumeric, spaces, common punctuation
    sanitized = re.sub(r"[^\w\s.,&'\"-]", "", sanitized)

    # Collapse multiple spaces
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    return sanitized


def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize and validate a URL for use in prompts.

    Returns None if URL is invalid or potentially malicious.
    """
    if not url:
        return None

    url = url.strip()

    # Must start with http:// or https://
    if not url.startswith(("http://", "https://")):
        return None

    # Check for suspicious patterns
    suspicious_patterns = [
        r"javascript:",
        r"data:",
        r"vbscript:",
        r"file://",
        r"<script",
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, url, re.I):
            return None

    # Truncate very long URLs
    if len(url) > 2000:
        url = url[:2000]

    return url


def escape_for_prompt(text: str) -> str:
    """
    Escape special characters that might be interpreted by LLMs.

    Use this for user-provided content that should be treated as literal text.
    """
    if not text:
        return ""

    # Escape common delimiter patterns
    escaped = text.replace("```", "` ` `")
    escaped = escaped.replace("---", "- - -")
    escaped = escaped.replace("===", "= = =")

    return escaped
