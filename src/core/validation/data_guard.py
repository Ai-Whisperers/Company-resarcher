"""
Data Exfiltration Prevention (SEC-010-B) and Output Sanitization (SEC-010-D).

This module provides:
- Detection and redaction of sensitive data (PII, credentials, internal info)
- Output sanitization for LLM responses
- XSS prevention in markdown outputs
- Audit logging for compliance

Usage:
    from src.core.validation.data_guard import DataExfiltrationGuard, OutputSanitizer

    guard = DataExfiltrationGuard()
    matches = guard.scan(text)
    safe_text = guard.redact(text)

    sanitizer = OutputSanitizer()
    safe_output = sanitizer.sanitize(llm_output)
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from src.core.logging import setup_logger


logger = setup_logger("security.data_guard")


# =============================================================================
# Data Exfiltration Prevention (SEC-010-B)
# =============================================================================


@dataclass
class SensitiveDataMatch:
    """Information about detected sensitive data."""
    pattern_type: str  # e.g., "credit_card", "ssn", "api_key"
    value_preview: str  # Partially masked preview of the value
    position: int  # Position in text
    redacted_form: str  # What it will be replaced with


class DataExfiltrationGuard:
    """
    Detects and redacts sensitive data from outputs (SEC-010-B).

    Detects:
    - Credit card numbers (Visa, Mastercard, Amex, Discover)
    - Social Security Numbers (SSN)
    - Employer Identification Numbers (EIN)
    - API keys (OpenAI, Anthropic, Google, AWS, GitHub)
    - Email addresses
    - Phone numbers (US and international)
    - Internal file paths (Windows and Unix)
    - Internal/private network URLs
    - Passwords and tokens in text

    Usage:
        guard = DataExfiltrationGuard()

        # Scan for sensitive data
        matches = guard.scan(text)

        # Redact all sensitive data
        safe_text = guard.redact(text)

        # Audit output for compliance
        report = guard.audit_output(text, context="research_output")
    """

    # Patterns for sensitive data detection
    PATTERNS = {
        # Financial data
        "credit_card": re.compile(
            r"\b(?:"
            r"4[0-9]{12}(?:[0-9]{3})?|"  # Visa
            r"5[1-5][0-9]{14}|"  # Mastercard
            r"3[47][0-9]{13}|"  # Amex
            r"6(?:011|5[0-9]{2})[0-9]{12}"  # Discover
            r")\b"
        ),

        # Personal identifiers
        "ssn": re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
        "ein": re.compile(r"\b\d{2}[-\s]?\d{7}\b"),

        # Contact information
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            re.IGNORECASE
        ),
        "phone_us": re.compile(
            r"\b(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
        ),
        "phone_intl": re.compile(r"\b\+[0-9]{1,3}[-.\s]?[0-9]{6,14}\b"),

        # API keys and tokens
        "openai_key": re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"),
        "openai_project_key": re.compile(r"\bsk-proj-[a-zA-Z0-9_-]{20,}\b"),
        "anthropic_key": re.compile(r"\bsk-ant-[a-zA-Z0-9_-]{20,}\b"),
        "google_api_key": re.compile(r"\bAIza[a-zA-Z0-9_-]{35}\b"),
        "aws_access_key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        "github_token": re.compile(r"\b(?:ghp|gho|ghu|ghs)_[a-zA-Z0-9]{36}\b"),
        "stripe_key": re.compile(r"\b(?:pk|sk)_(?:live|test)_[a-zA-Z0-9]{24,}\b"),
        "tavily_key": re.compile(r"\btvly-[a-zA-Z0-9]{20,}\b"),
        "serper_key": re.compile(r"\b[a-f0-9]{40,}\b"),  # Generic long hex (Serper uses this)

        # Generic patterns
        "generic_api_key": re.compile(
            r"(?:api[_-]?key|apikey|api_secret|secret[_-]?key|auth[_-]?token)"
            r"\s*[=:]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
            re.IGNORECASE
        ),
        "bearer_token": re.compile(r"\bBearer\s+[a-zA-Z0-9_.-]{20,}\b", re.IGNORECASE),
        "password_in_config": re.compile(
            r"(?:password|passwd|pwd|secret)\s*[=:]\s*['\"]?([^\s'\"]{8,})['\"]?",
            re.IGNORECASE
        ),

        # Internal paths and URLs
        "windows_path": re.compile(
            r"\b[A-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]+"
        ),
        "unix_sensitive_path": re.compile(
            r"(?:/(?:home|root|etc|var/(?:log|lib)|tmp)/[^\s]+)"
        ),
        "internal_url": re.compile(
            r"\bhttps?://(?:"
            r"localhost|"
            r"127\.0\.0\.1|"
            r"0\.0\.0\.0|"
            r"192\.168\.[0-9]{1,3}\.[0-9]{1,3}|"
            r"10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|"
            r"172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}"
            r")[:/][^\s]*",
            re.IGNORECASE
        ),
    }

    # Redaction text for each pattern type
    REDACTION_FORMATS = {
        "credit_card": "[CREDIT-CARD-REDACTED]",
        "ssn": "[SSN-REDACTED]",
        "ein": "[EIN-REDACTED]",
        "email": "[EMAIL-REDACTED]",
        "phone_us": "[PHONE-REDACTED]",
        "phone_intl": "[PHONE-REDACTED]",
        "openai_key": "[OPENAI-KEY-REDACTED]",
        "openai_project_key": "[OPENAI-KEY-REDACTED]",
        "anthropic_key": "[ANTHROPIC-KEY-REDACTED]",
        "google_api_key": "[GOOGLE-KEY-REDACTED]",
        "aws_access_key": "[AWS-KEY-REDACTED]",
        "github_token": "[GITHUB-TOKEN-REDACTED]",
        "stripe_key": "[STRIPE-KEY-REDACTED]",
        "tavily_key": "[TAVILY-KEY-REDACTED]",
        "serper_key": "[API-KEY-REDACTED]",
        "generic_api_key": "[API-KEY-REDACTED]",
        "bearer_token": "[BEARER-TOKEN-REDACTED]",
        "password_in_config": "[PASSWORD-REDACTED]",
        "windows_path": "[PATH-REDACTED]",
        "unix_sensitive_path": "[PATH-REDACTED]",
        "internal_url": "[INTERNAL-URL-REDACTED]",
    }

    # Categorization for reporting
    CATEGORIES = {
        "financial": ["credit_card"],
        "pii": ["ssn", "ein", "email", "phone_us", "phone_intl"],
        "credentials": [
            "openai_key", "openai_project_key", "anthropic_key", "google_api_key",
            "aws_access_key", "github_token", "stripe_key", "tavily_key", "serper_key",
            "generic_api_key", "bearer_token", "password_in_config"
        ],
        "internal": ["windows_path", "unix_sensitive_path", "internal_url"],
    }

    def __init__(
        self,
        redact_emails: bool = True,
        redact_phones: bool = True,
        redact_paths: bool = True,
        log_detections: bool = True,
    ):
        """
        Initialize the data exfiltration guard.

        Args:
            redact_emails: Whether to redact email addresses
            redact_phones: Whether to redact phone numbers
            redact_paths: Whether to redact file paths
            log_detections: Whether to log detections
        """
        self.redact_emails = redact_emails
        self.redact_phones = redact_phones
        self.redact_paths = redact_paths
        self.log_detections = log_detections
        self._logger = setup_logger("security.exfiltration")

    def _should_check_pattern(self, pattern_type: str) -> bool:
        """Determine if a pattern type should be checked based on config."""
        if pattern_type == "email" and not self.redact_emails:
            return False
        if pattern_type in ("phone_us", "phone_intl") and not self.redact_phones:
            return False
        if pattern_type in ("windows_path", "unix_sensitive_path") and not self.redact_paths:
            return False
        return True

    def scan(self, text: str) -> List[SensitiveDataMatch]:
        """
        Scan text for sensitive data.

        Args:
            text: Text to scan

        Returns:
            List of SensitiveDataMatch objects for each detection
        """
        if not text:
            return []

        matches = []

        for pattern_type, pattern in self.PATTERNS.items():
            if not self._should_check_pattern(pattern_type):
                continue

            for match in pattern.finditer(text):
                value = match.group(0)
                # Create masked preview (show first 4 chars + ***)
                preview = value[:4] + "***" if len(value) > 4 else "***"
                redacted_form = self.REDACTION_FORMATS.get(pattern_type, "[REDACTED]")

                matches.append(SensitiveDataMatch(
                    pattern_type=pattern_type,
                    value_preview=preview,
                    position=match.start(),
                    redacted_form=redacted_form,
                ))

        if matches and self.log_detections:
            types_found = set(m.pattern_type for m in matches)
            self._logger.warning(
                f"Sensitive data detected: {len(matches)} matches "
                f"(types: {', '.join(sorted(types_found))})"
            )

        return matches

    def redact(self, text: str) -> str:
        """
        Redact all sensitive data from text.

        Args:
            text: Text containing potentially sensitive data

        Returns:
            Text with all sensitive data replaced by redaction markers
        """
        if not text:
            return text

        result = text

        for pattern_type, pattern in self.PATTERNS.items():
            if not self._should_check_pattern(pattern_type):
                continue

            redaction = self.REDACTION_FORMATS.get(pattern_type, "[REDACTED]")
            result = pattern.sub(redaction, result)

        return result

    def audit_output(
        self,
        output: str,
        context: str = "unknown",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Audit an output for sensitive data and return compliance report.

        Args:
            output: Text to audit
            context: Description of where this output came from
            request_id: Request ID for tracing

        Returns:
            Dict with audit results including recommendations
        """
        matches = self.scan(output)

        # Categorize detections
        categories_found = {}
        for category, pattern_types in self.CATEGORIES.items():
            category_matches = [m for m in matches if m.pattern_type in pattern_types]
            if category_matches:
                categories_found[category] = len(category_matches)

        report = {
            "has_sensitive_data": len(matches) > 0,
            "total_matches": len(matches),
            "categories": categories_found,
            "pattern_types": sorted(set(m.pattern_type for m in matches)),
            "context": context,
            "request_id": request_id,
            "recommendation": "redact" if matches else "allow",
        }

        if matches:
            self._logger.info(
                f"[AUDIT] Output scan for '{context}': "
                f"{len(matches)} sensitive items detected",
                extra={"audit_report": report}
            )

        return report


# =============================================================================
# Output Sanitization (SEC-010-D)
# =============================================================================


class OutputSanitizer:
    """
    Sanitizes LLM outputs before storage or display (SEC-010-D).

    Features:
    - XSS prevention in markdown content
    - System information leak detection
    - Sensitive data redaction (via DataExfiltrationGuard)
    - URL validation

    Usage:
        sanitizer = OutputSanitizer()
        safe_output = sanitizer.sanitize(llm_response)
    """

    # XSS patterns that should be removed from markdown
    XSS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.I | re.DOTALL),
        re.compile(r"<script[^>]*>", re.I),
        re.compile(r"</script>", re.I),
        re.compile(r"javascript:", re.I),
        re.compile(r"vbscript:", re.I),
        re.compile(r"on\w+\s*=\s*['\"]?[^'\"]*['\"]?", re.I),  # onclick, onerror, etc.
        re.compile(r"<iframe[^>]*>", re.I),
        re.compile(r"</iframe>", re.I),
        re.compile(r"<object[^>]*>", re.I),
        re.compile(r"<embed[^>]*>", re.I),
        re.compile(r"<svg[^>]*onload[^>]*>", re.I),
        re.compile(r"<img[^>]*onerror[^>]*>", re.I),
    ]

    # Patterns that might indicate system info leakage
    SYSTEM_LEAK_PATTERNS = [
        re.compile(r"\b(?:internal|secret|private)\s+(?:key|token|password|api)", re.I),
        re.compile(r"\b(?:database|db|mongo|redis|postgres)_(?:password|user|host|uri)", re.I),
        re.compile(r"\b(?:ANTHROPIC|OPENAI|AWS|GOOGLE|STRIPE|TAVILY)_[A-Z_]+\s*=", re.I),
        re.compile(r"process\.env\.[A-Z_]+", re.I),
        re.compile(r"os\.environ\[['\"][A-Z_]+['\"]\]", re.I),
    ]

    def __init__(self, exfiltration_guard: Optional[DataExfiltrationGuard] = None):
        """
        Initialize the output sanitizer.

        Args:
            exfiltration_guard: Optional custom DataExfiltrationGuard instance
        """
        self.exfiltration_guard = exfiltration_guard or DataExfiltrationGuard()
        self._logger = setup_logger("security.output")

    def sanitize(
        self,
        output: str,
        redact_sensitive: bool = True,
        escape_xss: bool = True,
        check_system_leak: bool = True,
    ) -> str:
        """
        Sanitize LLM output for safe storage and display.

        Args:
            output: Raw LLM output text
            redact_sensitive: Redact PII, credentials, and internal info
            escape_xss: Remove potential XSS vectors from markdown
            check_system_leak: Check for and redact system info leaks

        Returns:
            Sanitized output safe for storage and display
        """
        if not output:
            return output

        result = output

        # Check for system info leakage
        if check_system_leak:
            for pattern in self.SYSTEM_LEAK_PATTERNS:
                if pattern.search(result):
                    self._logger.warning(
                        "Potential system info leak detected and redacted"
                    )
                    result = pattern.sub("[SYSTEM-INFO-REDACTED]", result)

        # Escape XSS patterns
        if escape_xss:
            for pattern in self.XSS_PATTERNS:
                result = pattern.sub("[UNSAFE-CONTENT-REMOVED]", result)

        # Redact sensitive data
        if redact_sensitive:
            result = self.exfiltration_guard.redact(result)

        return result

    def validate_urls(self, text: str) -> List[Dict[str, str]]:
        """
        Extract and validate URLs in text, identifying dangerous ones.

        Args:
            text: Text containing URLs to validate

        Returns:
            List of dicts with 'url' and 'issue' for each dangerous URL found
        """
        url_pattern = re.compile(r"https?://[^\s<>\"']+", re.I)
        dangerous_urls = []

        for match in url_pattern.finditer(text):
            url = match.group(0)
            issues = []

            # Check for javascript/data URIs
            if "javascript:" in url.lower():
                issues.append("javascript_uri")
            if "data:" in url.lower():
                issues.append("data_uri")

            # Check for credentials in URL
            if re.search(r"://[^/]*:[^/]*@", url):
                issues.append("credentials_in_url")

            # Check for internal/private network URLs
            if re.search(
                r"localhost|127\.0\.0\.1|192\.168\.|10\.|172\.(?:1[6-9]|2|3[01])\.",
                url
            ):
                issues.append("internal_network")

            if issues:
                dangerous_urls.append({
                    "url": url[:100] + "..." if len(url) > 100 else url,
                    "issues": issues,
                })

        return dangerous_urls

    def get_safety_report(self, output: str) -> Dict[str, Any]:
        """
        Generate a comprehensive safety report for an output.

        Args:
            output: Text to analyze

        Returns:
            Dict with detailed safety analysis
        """
        # Check for sensitive data
        audit = self.exfiltration_guard.audit_output(output)

        # Check for XSS
        xss_found = any(p.search(output) for p in self.XSS_PATTERNS)

        # Check for system leaks
        system_leak_found = any(p.search(output) for p in self.SYSTEM_LEAK_PATTERNS)

        # Check URLs
        dangerous_urls = self.validate_urls(output)

        return {
            "is_safe": not (
                audit["has_sensitive_data"] or xss_found or
                system_leak_found or dangerous_urls
            ),
            "sensitive_data": audit,
            "xss_detected": xss_found,
            "system_leak_detected": system_leak_found,
            "dangerous_urls": dangerous_urls,
            "recommendation": (
                "sanitize" if (audit["has_sensitive_data"] or xss_found or system_leak_found)
                else "allow"
            ),
        }


# =============================================================================
# Module-level convenience functions
# =============================================================================


_exfiltration_guard: Optional[DataExfiltrationGuard] = None
_output_sanitizer: Optional[OutputSanitizer] = None


def get_exfiltration_guard() -> DataExfiltrationGuard:
    """Get the global DataExfiltrationGuard instance."""
    global _exfiltration_guard
    if _exfiltration_guard is None:
        _exfiltration_guard = DataExfiltrationGuard()
    return _exfiltration_guard


def get_output_sanitizer() -> OutputSanitizer:
    """Get the global OutputSanitizer instance."""
    global _output_sanitizer
    if _output_sanitizer is None:
        _output_sanitizer = OutputSanitizer()
    return _output_sanitizer


def redact_sensitive_data(text: str) -> str:
    """Convenience function to redact sensitive data from text."""
    return get_exfiltration_guard().redact(text)


def sanitize_output(text: str) -> str:
    """Convenience function to sanitize LLM output."""
    return get_output_sanitizer().sanitize(text)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Classes
    "DataExfiltrationGuard",
    "OutputSanitizer",
    "SensitiveDataMatch",
    # Functions
    "get_exfiltration_guard",
    "get_output_sanitizer",
    "redact_sensitive_data",
    "sanitize_output",
]
