"""
Core security utilities for Company Researcher.

This module provides:
- Enhanced prompt injection detection and blocking
- Input sanitization for all external inputs
- Security configuration and policies
- Audit logging for sensitive operations

Usage:
    from src.core.security.security_core import SecurityManager, get_security_manager

    security = get_security_manager()
    result = security.validate_input(user_input)
    if not result.is_safe:
        raise SecurityError(result.reason)
"""

import re
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from ..logging import setup_logger


logger = setup_logger("security")


class ThreatLevel(str, Enum):
    """Threat level classification for security events."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityAction(str, Enum):
    """Actions taken by security system."""
    ALLOW = "allow"
    SANITIZE = "sanitize"
    BLOCK = "block"
    WARN = "warn"


@dataclass(frozen=True)
class ValidationResult:
    """Result of security validation."""
    is_safe: bool
    action: SecurityAction
    threat_level: ThreatLevel = ThreatLevel.NONE
    reason: Optional[str] = None
    sanitized_value: Optional[str] = None
    matched_patterns: List[str] = field(default_factory=list)

    @classmethod
    def safe(cls, value: str = None) -> "ValidationResult":
        """Create a safe validation result."""
        return cls(
            is_safe=True,
            action=SecurityAction.ALLOW,
            sanitized_value=value,
        )

    @classmethod
    def sanitized(cls, original: str, sanitized: str, reason: str) -> "ValidationResult":
        """Create a sanitized validation result."""
        return cls(
            is_safe=True,
            action=SecurityAction.SANITIZE,
            threat_level=ThreatLevel.LOW,
            reason=reason,
            sanitized_value=sanitized,
        )

    @classmethod
    def blocked(cls, reason: str, threat_level: ThreatLevel, patterns: List[str] = None) -> "ValidationResult":
        """Create a blocked validation result."""
        return cls(
            is_safe=False,
            action=SecurityAction.BLOCK,
            threat_level=threat_level,
            reason=reason,
            matched_patterns=patterns or [],
        )


@dataclass
class SecurityEvent:
    """Security event for audit logging."""
    timestamp: datetime
    event_type: str
    threat_level: ThreatLevel
    action: SecurityAction
    source: str  # IP, user ID, or request ID
    target: str  # What was being accessed/modified
    details: Dict[str, Any]
    request_id: Optional[str] = None


class AuditLogger:
    """Audit logger for security-sensitive operations."""

    def __init__(self, max_events: int = 10000):
        self._events: List[SecurityEvent] = []
        self._max_events = max_events
        self._logger = setup_logger("security.audit")

    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        # Always log to structured logger
        self._logger.info(
            f"[AUDIT] {event.event_type} - {event.action.value}",
            extra={
                "security_event": {
                    "type": event.event_type,
                    "threat_level": event.threat_level.value,
                    "action": event.action.value,
                    "source": event.source,
                    "target": event.target,
                    "request_id": event.request_id,
                    "details": event.details,
                }
            }
        )

        # Keep in-memory buffer for recent events
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def log_access(
        self,
        source: str,
        target: str,
        action: SecurityAction,
        request_id: str = None,
        details: Dict[str, Any] = None,
    ) -> None:
        """Log an access event."""
        event = SecurityEvent(
            timestamp=datetime.now(timezone.utc),
            event_type="access",
            threat_level=ThreatLevel.NONE,
            action=action,
            source=source,
            target=target,
            details=details or {},
            request_id=request_id,
        )
        self.log_event(event)

    def log_threat(
        self,
        source: str,
        threat_level: ThreatLevel,
        description: str,
        request_id: str = None,
        details: Dict[str, Any] = None,
    ) -> None:
        """Log a threat detection event."""
        event = SecurityEvent(
            timestamp=datetime.now(timezone.utc),
            event_type="threat_detected",
            threat_level=threat_level,
            action=SecurityAction.BLOCK,
            source=source,
            target="input_validation",
            details={"description": description, **(details or {})},
            request_id=request_id,
        )
        self.log_event(event)

        # High/Critical threats get extra logging
        if threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
            self._logger.warning(
                f"[SECURITY ALERT] {threat_level.value.upper()}: {description} from {source}"
            )

    def get_recent_events(self, count: int = 100) -> List[SecurityEvent]:
        """Get recent security events."""
        return self._events[-count:]


class PromptInjectionDetector:
    """Detects and blocks prompt injection attempts."""

    # Injection patterns with threat levels
    PATTERNS = [
        # High severity - direct instruction override attempts
        (re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)", re.I), ThreatLevel.HIGH, "instruction_override"),
        (re.compile(r"disregard\s+(all\s+)?(previous|above|prior|everything)", re.I), ThreatLevel.HIGH, "instruction_override"),
        (re.compile(r"forget\s+(all\s+)?(previous|above|prior|everything|your\s+instructions?)", re.I), ThreatLevel.HIGH, "instruction_override"),
        (re.compile(r"override\s+(your\s+)?(instructions?|programming|rules?)", re.I), ThreatLevel.HIGH, "instruction_override"),
        (re.compile(r"new\s+instructions?\s*[:\-]", re.I), ThreatLevel.HIGH, "instruction_injection"),
        (re.compile(r"your\s+new\s+(role|purpose|instructions?)\s+(is|are)", re.I), ThreatLevel.HIGH, "role_hijack"),

        # Medium severity - role/persona manipulation
        (re.compile(r"you\s+are\s+now\s+(a|an|the)?\s*\w+", re.I), ThreatLevel.MEDIUM, "role_manipulation"),
        (re.compile(r"act\s+as\s+(a|an|if\s+you\s+are)", re.I), ThreatLevel.MEDIUM, "role_manipulation"),
        (re.compile(r"pretend\s+(to\s+be|you\s+are)", re.I), ThreatLevel.MEDIUM, "role_manipulation"),
        (re.compile(r"roleplay\s+as", re.I), ThreatLevel.MEDIUM, "role_manipulation"),

        # Medium severity - system message injection
        (re.compile(r"<\s*system\s*>", re.I), ThreatLevel.MEDIUM, "system_tag_injection"),
        (re.compile(r"\[\s*INST\s*\]", re.I), ThreatLevel.MEDIUM, "instruction_tag_injection"),
        (re.compile(r"</?\s*s\s*>", re.I), ThreatLevel.MEDIUM, "token_injection"),
        (re.compile(r"<<\s*SYS\s*>>", re.I), ThreatLevel.MEDIUM, "system_tag_injection"),
        (re.compile(r"\[/?\s*INST\s*\]", re.I), ThreatLevel.MEDIUM, "instruction_tag_injection"),

        # Medium severity - output manipulation
        (re.compile(r"print\s+(only|just|exactly)", re.I), ThreatLevel.MEDIUM, "output_manipulation"),
        (re.compile(r"respond\s+with\s+(only|just|exactly)", re.I), ThreatLevel.MEDIUM, "output_manipulation"),
        (re.compile(r"output\s+(only|just|exactly)", re.I), ThreatLevel.MEDIUM, "output_manipulation"),

        # Low severity - potential but uncertain
        (re.compile(r"system\s*:\s*", re.I), ThreatLevel.LOW, "potential_system_prefix"),
        (re.compile(r"assistant\s*:\s*", re.I), ThreatLevel.LOW, "potential_assistant_prefix"),
        (re.compile(r"user\s*:\s*", re.I), ThreatLevel.LOW, "potential_user_prefix"),
    ]

    def __init__(self, block_on_detection: bool = True, min_block_level: ThreatLevel = ThreatLevel.MEDIUM):
        self.block_on_detection = block_on_detection
        self.min_block_level = min_block_level

    def detect(self, text: str) -> ValidationResult:
        """Detect prompt injection attempts in text."""
        if not text:
            return ValidationResult.safe("")

        detected_patterns = []
        max_threat_level = ThreatLevel.NONE

        for pattern, threat_level, pattern_name in self.PATTERNS:
            if pattern.search(text):
                detected_patterns.append(pattern_name)
                if self._threat_level_value(threat_level) > self._threat_level_value(max_threat_level):
                    max_threat_level = threat_level

        if not detected_patterns:
            return ValidationResult.safe(text)

        # Determine action based on threat level and configuration
        should_block = (
            self.block_on_detection and
            self._threat_level_value(max_threat_level) >= self._threat_level_value(self.min_block_level)
        )

        if should_block:
            return ValidationResult.blocked(
                reason=f"Prompt injection detected: {', '.join(detected_patterns)}",
                threat_level=max_threat_level,
                patterns=detected_patterns,
            )
        else:
            return ValidationResult(
                is_safe=True,
                action=SecurityAction.WARN,
                threat_level=max_threat_level,
                reason=f"Potential prompt injection: {', '.join(detected_patterns)}",
                sanitized_value=text,
                matched_patterns=detected_patterns,
            )

    @staticmethod
    def _threat_level_value(level: ThreatLevel) -> int:
        """Convert threat level to numeric value for comparison."""
        return {
            ThreatLevel.NONE: 0,
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4,
        }[level]


class InputSanitizer:
    """Sanitizes various types of user input."""

    # Maximum lengths for different input types
    MAX_COMPANY_NAME = 500
    MAX_QUERY = 1000
    MAX_URL = 2000
    MAX_CONTEXT = 50000

    # Allowed patterns
    COMPANY_NAME_PATTERN = re.compile(r"^[\w\s.,&'\"()\-]+$", re.UNICODE)
    SAFE_URL_PATTERN = re.compile(r"^https?://[\w\-.]+(:\d+)?(/[\w\-./]*)?(\?[\w\-=&]*)?$")

    # Dangerous patterns
    DANGEROUS_URL_SCHEMES = ["javascript:", "data:", "vbscript:", "file://"]
    DANGEROUS_URL_PATTERNS = [re.compile(r"<script", re.I)]

    def sanitize_text(
        self,
        text: str,
        max_length: int = MAX_QUERY,
        strip_control_chars: bool = True,
    ) -> str:
        """Sanitize general text input."""
        if not text:
            return ""

        # Strip whitespace
        sanitized = text.strip()

        # Remove control characters (keep printable + common whitespace)
        if strip_control_chars:
            sanitized = "".join(
                c for c in sanitized if c.isprintable() or c in "\n\t"
            )

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    def sanitize_company_name(self, name: str) -> ValidationResult:
        """Sanitize a company name with strict validation."""
        if not name:
            return ValidationResult.blocked("Company name is required", ThreatLevel.LOW)

        # Basic sanitization
        sanitized = self.sanitize_text(name, max_length=self.MAX_COMPANY_NAME)

        # Remove characters not allowed in company names
        sanitized = re.sub(r"[^\w\s.,&'\"()\-]", "", sanitized, flags=re.UNICODE)

        # Collapse multiple spaces
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        if not sanitized:
            return ValidationResult.blocked("Company name contains no valid characters", ThreatLevel.LOW)

        if sanitized != name.strip():
            return ValidationResult.sanitized(
                original=name,
                sanitized=sanitized,
                reason="Company name contained invalid characters that were removed",
            )

        return ValidationResult.safe(sanitized)

    def sanitize_url(self, url: str) -> ValidationResult:
        """Sanitize and validate a URL."""
        if not url:
            return ValidationResult.blocked("URL is required", ThreatLevel.LOW)

        url = url.strip()

        # Check for dangerous schemes
        url_lower = url.lower()
        for scheme in self.DANGEROUS_URL_SCHEMES:
            if url_lower.startswith(scheme):
                return ValidationResult.blocked(
                    f"Dangerous URL scheme: {scheme}",
                    ThreatLevel.HIGH,
                )

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_URL_PATTERNS:
            if pattern.search(url):
                return ValidationResult.blocked(
                    "URL contains dangerous content",
                    ThreatLevel.HIGH,
                )

        # Must start with http:// or https://
        if not url.startswith(("http://", "https://")):
            return ValidationResult.blocked(
                "URL must start with http:// or https://",
                ThreatLevel.LOW,
            )

        # Truncate very long URLs
        if len(url) > self.MAX_URL:
            url = url[:self.MAX_URL]
            return ValidationResult.sanitized(
                original=url,
                sanitized=url,
                reason=f"URL truncated to {self.MAX_URL} characters",
            )

        return ValidationResult.safe(url)

    def sanitize_search_query(self, query: str) -> ValidationResult:
        """Sanitize a search query."""
        if not query:
            return ValidationResult.blocked("Search query is required", ThreatLevel.LOW)

        sanitized = self.sanitize_text(query, max_length=self.MAX_QUERY)

        # Remove search operators that could be used for abuse
        operators = ["site:", "inurl:", "filetype:", "intitle:", "intext:", "cache:", "related:"]
        for op in operators:
            if op in sanitized.lower():
                sanitized = re.sub(re.escape(op), "", sanitized, flags=re.I)

        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        if not sanitized:
            return ValidationResult.blocked("Search query is empty after sanitization", ThreatLevel.LOW)

        return ValidationResult.safe(sanitized)


class SecurityManager:
    """Central security manager coordinating all security functions."""

    def __init__(
        self,
        block_injection: bool = True,
        min_block_level: ThreatLevel = ThreatLevel.MEDIUM,
        audit_enabled: bool = True,
    ):
        self.injection_detector = PromptInjectionDetector(
            block_on_detection=block_injection,
            min_block_level=min_block_level,
        )
        self.sanitizer = InputSanitizer()
        self.audit = AuditLogger() if audit_enabled else None
        self._block_injection = block_injection

    def validate_prompt_input(
        self,
        text: str,
        source: str = "unknown",
        request_id: str = None,
    ) -> ValidationResult:
        """Validate and sanitize input intended for AI prompts."""
        # First sanitize
        sanitized = self.sanitizer.sanitize_text(text)

        # Then check for injection
        result = self.injection_detector.detect(sanitized)

        # Audit log if threat detected
        if result.threat_level != ThreatLevel.NONE and self.audit:
            self.audit.log_threat(
                source=source,
                threat_level=result.threat_level,
                description=result.reason or "Unknown threat",
                request_id=request_id,
                details={
                    "input_length": len(text),
                    "patterns": result.matched_patterns,
                    "action": result.action.value,
                },
            )

        return result

    def validate_company_name(
        self,
        name: str,
        source: str = "unknown",
        request_id: str = None,
    ) -> ValidationResult:
        """Validate a company name with sanitization and injection detection."""
        # Sanitize first
        sanitize_result = self.sanitizer.sanitize_company_name(name)
        if not sanitize_result.is_safe:
            return sanitize_result

        sanitized_name = sanitize_result.sanitized_value

        # Check for injection in the sanitized name
        injection_result = self.injection_detector.detect(sanitized_name)
        if not injection_result.is_safe:
            if self.audit:
                self.audit.log_threat(
                    source=source,
                    threat_level=injection_result.threat_level,
                    description=f"Injection in company name: {injection_result.reason}",
                    request_id=request_id,
                )
            return injection_result

        # Return the sanitization result if there were changes
        if sanitize_result.action == SecurityAction.SANITIZE:
            return sanitize_result

        return ValidationResult.safe(sanitized_name)

    def validate_url(
        self,
        url: str,
        source: str = "unknown",
        request_id: str = None,
    ) -> ValidationResult:
        """Validate a URL with security checks."""
        result = self.sanitizer.sanitize_url(url)

        if not result.is_safe and self.audit:
            self.audit.log_threat(
                source=source,
                threat_level=result.threat_level,
                description=f"Invalid URL: {result.reason}",
                request_id=request_id,
                details={"url_preview": url[:100] if url else ""},
            )

        return result

    def validate_search_query(
        self,
        query: str,
        source: str = "unknown",
        request_id: str = None,
    ) -> ValidationResult:
        """Validate a search query."""
        sanitize_result = self.sanitizer.sanitize_search_query(query)
        if not sanitize_result.is_safe:
            return sanitize_result

        # Check for injection
        injection_result = self.injection_detector.detect(sanitize_result.sanitized_value)
        if not injection_result.is_safe:
            if self.audit:
                self.audit.log_threat(
                    source=source,
                    threat_level=injection_result.threat_level,
                    description=f"Injection in search query: {injection_result.reason}",
                    request_id=request_id,
                )
            return injection_result

        return sanitize_result

    def log_sensitive_access(
        self,
        source: str,
        target: str,
        action: str,
        request_id: str = None,
        details: Dict[str, Any] = None,
    ) -> None:
        """Log access to sensitive resources."""
        if self.audit:
            self.audit.log_access(
                source=source,
                target=target,
                action=SecurityAction.ALLOW,
                request_id=request_id,
                details={"operation": action, **(details or {})},
            )

    def generate_hash(self, data: str) -> str:
        """Generate a secure hash of data for comparison/caching."""
        return hashlib.sha256(data.encode()).hexdigest()


# Module-level instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def configure_security(
    block_injection: bool = True,
    min_block_level: ThreatLevel = ThreatLevel.MEDIUM,
    audit_enabled: bool = True,
) -> SecurityManager:
    """Configure and return the global security manager."""
    global _security_manager
    _security_manager = SecurityManager(
        block_injection=block_injection,
        min_block_level=min_block_level,
        audit_enabled=audit_enabled,
    )
    return _security_manager


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Classes
    "SecurityManager",
    "PromptInjectionDetector",
    "InputSanitizer",
    "AuditLogger",
    "ValidationResult",
    "SecurityEvent",
    # Enums
    "ThreatLevel",
    "SecurityAction",
    # Functions
    "get_security_manager",
    "configure_security",
]
