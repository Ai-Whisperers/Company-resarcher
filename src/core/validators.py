"""
Consolidated Validators Module.

Provides centralized validation for:
- Research requests (VAL-001)
- Search queries (VAL-002)
- Prompt paths (VAL-003)
- Vault filenames (VAL-004)
- URL revalidation (VAL-005)
- General input sanitization
"""

import re
from typing import Optional, List, Tuple, Any, Union
from pathlib import Path
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from enum import Enum

from .exceptions import InputValidationError, ValidationError, ConfigValidationError


# =============================================================================
# Constants and Patterns
# =============================================================================


# Company name validation
COMPANY_NAME_PATTERN = re.compile(r'^[\w\s\-\.\,\&\'\"\(\)\+\/\:]+$', re.UNICODE)
COMPANY_NAME_MIN_LENGTH = 1
COMPANY_NAME_MAX_LENGTH = 200

# Industry validation
INDUSTRY_PATTERN = re.compile(r'^[\w\s\-\/\&\,\.]+$', re.UNICODE)
INDUSTRY_MAX_LENGTH = 100

# Country validation
COUNTRY_PATTERN = re.compile(r'^[\w\s\-\.\']+$', re.UNICODE)
COUNTRY_MAX_LENGTH = 100

# Search query validation
SEARCH_QUERY_MAX_LENGTH = 500
SEARCH_OPERATOR_PATTERN = re.compile(
    r'(site:|inurl:|filetype:|intitle:|intext:|cache:|related:|define:)',
    re.IGNORECASE
)

# URL validation
ALLOWED_URL_SCHEMES = {'http', 'https'}
BLOCKED_URL_PATTERNS = [
    r'localhost',
    r'127\.0\.0\.1',
    r'0\.0\.0\.0',
    r'::1',
    r'169\.254\.',  # Link-local
    r'10\.\d+\.\d+\.\d+',  # Private
    r'172\.(1[6-9]|2\d|3[01])\.',  # Private
    r'192\.168\.',  # Private
]

# Path validation
DANGEROUS_PATH_CHARS = ['..', '\x00', ':', '*', '?', '"', '<', '>', '|']
PATH_TRAVERSAL_PATTERN = re.compile(r'\.{2,}[/\\]')

# Prompt path validation
ALLOWED_PROMPT_EXTENSIONS = {'.txt', '.md', '.jinja2', '.j2'}
PROMPT_PATH_PATTERN = re.compile(r'^[\w\-\/]+(\.(txt|md|jinja2|j2))?$')

# Vault filename validation
VAULT_FILENAME_PATTERN = re.compile(r'^[\w\-\.]+$')
VAULT_FILENAME_MAX_LENGTH = 255


# =============================================================================
# Validation Result
# =============================================================================


class ValidationStatus(Enum):
    """Validation result status."""
    VALID = "valid"
    INVALID = "invalid"
    SANITIZED = "sanitized"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    status: ValidationStatus
    value: Any
    original: Any
    errors: List[str]
    warnings: List[str]

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.status in (ValidationStatus.VALID, ValidationStatus.SANITIZED, ValidationStatus.WARNING)

    @property
    def was_modified(self) -> bool:
        """Check if value was modified during validation."""
        return self.value != self.original

    def raise_if_invalid(self) -> None:
        """Raise ValidationError if not valid."""
        if not self.is_valid:
            raise InputValidationError(
                message="; ".join(self.errors),
                field="input",
                value=self.original
            )


# =============================================================================
# Research Request Validation (VAL-001)
# =============================================================================


def validate_company_name(name: str) -> ValidationResult:
    """
    Validate company name.

    Args:
        name: Company name to validate

    Returns:
        ValidationResult with validated/sanitized name
    """
    errors = []
    warnings = []
    original = name

    # Strip whitespace
    name = name.strip() if name else ""

    # Check for empty
    if not name:
        errors.append("Company name cannot be empty")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value=name,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check length
    if len(name) < COMPANY_NAME_MIN_LENGTH:
        errors.append(f"Company name must be at least {COMPANY_NAME_MIN_LENGTH} character(s)")

    if len(name) > COMPANY_NAME_MAX_LENGTH:
        errors.append(f"Company name cannot exceed {COMPANY_NAME_MAX_LENGTH} characters")
        name = name[:COMPANY_NAME_MAX_LENGTH]
        warnings.append("Company name was truncated")

    # Check pattern
    if not COMPANY_NAME_PATTERN.match(name):
        errors.append(
            "Company name contains invalid characters. "
            "Allowed: letters, numbers, spaces, and common punctuation (-.,'\"()&+/:)"
        )

    status = ValidationStatus.INVALID if errors else ValidationStatus.VALID
    if not errors and warnings:
        status = ValidationStatus.WARNING

    return ValidationResult(
        status=status,
        value=name,
        original=original,
        errors=errors,
        warnings=warnings
    )


def validate_industry(industry: Optional[str]) -> ValidationResult:
    """
    Validate industry field.

    Args:
        industry: Industry to validate

    Returns:
        ValidationResult with validated industry
    """
    errors = []
    warnings = []
    original = industry

    if industry is None:
        return ValidationResult(
            status=ValidationStatus.VALID,
            value=None,
            original=original,
            errors=errors,
            warnings=warnings
        )

    industry = industry.strip()
    if not industry:
        return ValidationResult(
            status=ValidationStatus.VALID,
            value=None,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check length
    if len(industry) > INDUSTRY_MAX_LENGTH:
        errors.append(f"Industry cannot exceed {INDUSTRY_MAX_LENGTH} characters")
        industry = industry[:INDUSTRY_MAX_LENGTH]

    # Check pattern
    if not INDUSTRY_PATTERN.match(industry):
        errors.append(
            "Industry contains invalid characters. "
            "Allowed: letters, numbers, spaces, and basic punctuation (-/&,.)"
        )

    status = ValidationStatus.INVALID if errors else ValidationStatus.VALID

    return ValidationResult(
        status=status,
        value=industry,
        original=original,
        errors=errors,
        warnings=warnings
    )


def validate_country(country: Optional[str]) -> ValidationResult:
    """
    Validate country field.

    Args:
        country: Country to validate

    Returns:
        ValidationResult with validated country
    """
    errors = []
    warnings = []
    original = country

    if country is None:
        return ValidationResult(
            status=ValidationStatus.VALID,
            value=None,
            original=original,
            errors=errors,
            warnings=warnings
        )

    country = country.strip()
    if not country:
        return ValidationResult(
            status=ValidationStatus.VALID,
            value=None,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check length
    if len(country) > COUNTRY_MAX_LENGTH:
        errors.append(f"Country cannot exceed {COUNTRY_MAX_LENGTH} characters")
        country = country[:COUNTRY_MAX_LENGTH]

    # Check pattern
    if not COUNTRY_PATTERN.match(country):
        errors.append(
            "Country contains invalid characters. "
            "Allowed: letters, numbers, spaces, hyphens, periods, and apostrophes"
        )

    status = ValidationStatus.INVALID if errors else ValidationStatus.VALID

    return ValidationResult(
        status=status,
        value=country,
        original=original,
        errors=errors,
        warnings=warnings
    )


def validate_research_request(
    company_name: str,
    url: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None
) -> Tuple[bool, dict, List[str]]:
    """
    Validate a complete research request.

    Args:
        company_name: Company name
        url: Optional company URL
        industry: Optional industry
        country: Optional country

    Returns:
        Tuple of (is_valid, validated_data, errors)
    """
    errors = []
    validated = {}

    # Validate company name
    company_result = validate_company_name(company_name)
    if not company_result.is_valid:
        errors.extend(company_result.errors)
    validated["company_name"] = company_result.value

    # Validate URL
    if url:
        url_result = validate_url(url)
        if not url_result.is_valid:
            errors.extend(url_result.errors)
        validated["url"] = url_result.value
    else:
        validated["url"] = None

    # Validate industry
    industry_result = validate_industry(industry)
    if not industry_result.is_valid:
        errors.extend(industry_result.errors)
    validated["industry"] = industry_result.value

    # Validate country
    country_result = validate_country(country)
    if not country_result.is_valid:
        errors.extend(country_result.errors)
    validated["country"] = country_result.value

    return len(errors) == 0, validated, errors


# =============================================================================
# Search Query Validation (VAL-002)
# =============================================================================


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent injection and abuse.

    Args:
        query: Raw search query

    Returns:
        Sanitized query string
    """
    if not query or not isinstance(query, str):
        return ""

    # Limit length
    query = query[:SEARCH_QUERY_MAX_LENGTH]

    # Remove control characters
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)

    # Remove search operators
    query = SEARCH_OPERATOR_PATTERN.sub('', query)

    # Normalize whitespace
    query = ' '.join(query.split())

    return query


def validate_search_query(query: str) -> ValidationResult:
    """
    Validate and sanitize a search query.

    Args:
        query: Search query to validate

    Returns:
        ValidationResult with sanitized query
    """
    errors = []
    warnings = []
    original = query

    if not query or not isinstance(query, str):
        errors.append("Search query cannot be empty")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value="",
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Sanitize
    sanitized = sanitize_search_query(query)

    if not sanitized:
        errors.append("Search query is empty after sanitization")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value="",
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check if operators were removed
    if SEARCH_OPERATOR_PATTERN.search(original):
        warnings.append("Search operators were removed from query")

    # Check if truncated
    if len(original) > SEARCH_QUERY_MAX_LENGTH:
        warnings.append(f"Query was truncated to {SEARCH_QUERY_MAX_LENGTH} characters")

    status = ValidationStatus.SANITIZED if warnings else ValidationStatus.VALID

    return ValidationResult(
        status=status,
        value=sanitized,
        original=original,
        errors=errors,
        warnings=warnings
    )


# =============================================================================
# Prompt Path Validation (VAL-003)
# =============================================================================


def validate_prompt_path(
    path: str,
    base_dir: Optional[Path] = None
) -> ValidationResult:
    """
    Validate a prompt template path.

    Args:
        path: Prompt path to validate
        base_dir: Base directory for relative paths

    Returns:
        ValidationResult with validated path
    """
    errors = []
    warnings = []
    original = path

    if not path:
        errors.append("Prompt path cannot be empty")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value=path,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check for path traversal
    if PATH_TRAVERSAL_PATTERN.search(path) or '..' in path:
        errors.append("Path traversal detected in prompt path")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value=path,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check extension
    path_obj = Path(path)
    if path_obj.suffix and path_obj.suffix.lower() not in ALLOWED_PROMPT_EXTENSIONS:
        errors.append(f"Invalid prompt extension. Allowed: {', '.join(ALLOWED_PROMPT_EXTENSIONS)}")

    # Validate against base directory
    if base_dir:
        try:
            full_path = (base_dir / path).resolve()
            if not str(full_path).startswith(str(base_dir.resolve())):
                errors.append("Prompt path escapes base directory")
        except Exception as e:
            errors.append(f"Invalid path: {e}")

    status = ValidationStatus.INVALID if errors else ValidationStatus.VALID

    return ValidationResult(
        status=status,
        value=str(path),
        original=original,
        errors=errors,
        warnings=warnings
    )


# =============================================================================
# Vault Filename Validation (VAL-004)
# =============================================================================


def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename for safe filesystem use.

    Args:
        name: Filename to sanitize

    Returns:
        Sanitized filename
    """
    if not name:
        return ""

    # Remove dangerous characters
    for char in DANGEROUS_PATH_CHARS:
        name = name.replace(char, '_')

    # Strip whitespace
    name = name.strip()

    # Truncate if too long
    if len(name) > VAULT_FILENAME_MAX_LENGTH:
        name = name[:VAULT_FILENAME_MAX_LENGTH]

    return name


def validate_vault_filename(filename: str) -> ValidationResult:
    """
    Validate a vault filename.

    Args:
        filename: Filename to validate

    Returns:
        ValidationResult with validated filename
    """
    errors = []
    warnings = []
    original = filename

    if not filename:
        errors.append("Filename cannot be empty")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value=filename,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Sanitize
    sanitized = sanitize_filename(filename)

    if not sanitized:
        errors.append("Filename is empty after sanitization")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value="",
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check if modified
    if sanitized != original:
        warnings.append("Filename contained invalid characters that were sanitized")

    # Check pattern
    if not VAULT_FILENAME_PATTERN.match(sanitized):
        warnings.append("Filename contains non-standard characters")

    status = ValidationStatus.SANITIZED if warnings else ValidationStatus.VALID

    return ValidationResult(
        status=status,
        value=sanitized,
        original=original,
        errors=errors,
        warnings=warnings
    )


# =============================================================================
# URL Validation (VAL-005)
# =============================================================================


def validate_url(url: str, allow_internal: bool = False) -> ValidationResult:
    """
    Validate a URL for security and correctness.

    Args:
        url: URL to validate
        allow_internal: Whether to allow internal/private URLs

    Returns:
        ValidationResult with validated URL
    """
    errors = []
    warnings = []
    original = url

    if not url:
        errors.append("URL cannot be empty")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value=url,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Strip whitespace
    url = url.strip()

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        errors.append(f"Invalid URL format: {e}")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value=url,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check scheme
    if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
        errors.append(f"URL scheme must be one of: {', '.join(ALLOWED_URL_SCHEMES)}")

    # Check for host
    if not parsed.netloc:
        errors.append("URL must include a host")

    # Check for blocked patterns (internal IPs, etc.)
    if not allow_internal:
        for pattern in BLOCKED_URL_PATTERNS:
            if re.search(pattern, parsed.netloc):
                errors.append("URL points to internal/private address")
                break

    # Check for suspicious patterns
    if parsed.username or parsed.password:
        errors.append("URL cannot contain credentials")

    # Check for path traversal in URL path
    if '..' in parsed.path:
        warnings.append("URL path contains potential traversal characters")

    status = ValidationStatus.INVALID if errors else ValidationStatus.VALID
    if not errors and warnings:
        status = ValidationStatus.WARNING

    return ValidationResult(
        status=status,
        value=url,
        original=original,
        errors=errors,
        warnings=warnings
    )


def revalidate_search_result_urls(results: List[dict]) -> List[dict]:
    """
    Revalidate URLs from search results before use.

    Args:
        results: List of search result dictionaries with 'url' key

    Returns:
        Filtered list with only valid URLs
    """
    valid_results = []

    for result in results:
        url = result.get("url", "")
        validation = validate_url(url)

        if validation.is_valid:
            valid_results.append(result)

    return valid_results


# =============================================================================
# General Validation Utilities
# =============================================================================


def is_safe_string(value: str, max_length: int = 1000) -> bool:
    """
    Check if a string is safe for general use.

    Args:
        value: String to check
        max_length: Maximum allowed length

    Returns:
        True if string is safe
    """
    if not isinstance(value, str):
        return False

    if len(value) > max_length:
        return False

    # Check for null bytes
    if '\x00' in value:
        return False

    # Check for excessive control characters
    control_count = sum(1 for c in value if ord(c) < 32 and c not in '\t\n\r')
    if control_count > len(value) * 0.1:  # More than 10% control chars
        return False

    return True


def sanitize_for_logging(value: Any, max_length: int = 500) -> str:
    """
    Sanitize a value for safe logging.

    Args:
        value: Value to sanitize
        max_length: Maximum length

    Returns:
        Safe string for logging
    """
    if value is None:
        return "None"

    str_value = str(value)

    # Remove control characters
    str_value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str_value)

    # Truncate
    if len(str_value) > max_length:
        str_value = str_value[:max_length] + "...[truncated]"

    return str_value


def validate_config_value(
    key: str,
    value: Any,
    expected_type: type,
    constraints: Optional[dict] = None
) -> ValidationResult:
    """
    Validate a configuration value.

    Args:
        key: Configuration key name
        value: Value to validate
        expected_type: Expected Python type
        constraints: Optional constraints (min, max, choices, etc.)

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    original = value
    constraints = constraints or {}

    # Check type
    if not isinstance(value, expected_type):
        errors.append(f"Config '{key}' must be of type {expected_type.__name__}")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            value=value,
            original=original,
            errors=errors,
            warnings=warnings
        )

    # Check numeric constraints
    if expected_type in (int, float):
        if "min" in constraints and value < constraints["min"]:
            errors.append(f"Config '{key}' must be >= {constraints['min']}")
        if "max" in constraints and value > constraints["max"]:
            errors.append(f"Config '{key}' must be <= {constraints['max']}")

    # Check string constraints
    if expected_type == str:
        if "min_length" in constraints and len(value) < constraints["min_length"]:
            errors.append(f"Config '{key}' must be at least {constraints['min_length']} characters")
        if "max_length" in constraints and len(value) > constraints["max_length"]:
            errors.append(f"Config '{key}' cannot exceed {constraints['max_length']} characters")
        if "pattern" in constraints and not re.match(constraints["pattern"], value):
            errors.append(f"Config '{key}' does not match required pattern")

    # Check choices
    if "choices" in constraints and value not in constraints["choices"]:
        errors.append(f"Config '{key}' must be one of: {', '.join(map(str, constraints['choices']))}")

    status = ValidationStatus.INVALID if errors else ValidationStatus.VALID

    return ValidationResult(
        status=status,
        value=value,
        original=original,
        errors=errors,
        warnings=warnings
    )
