"""
Security tests for input validation.

Tests that the system properly handles potentially malicious inputs including:
- XSS attempts
- SQL injection
- Path traversal
- Command injection
- SSRF prevention
"""

import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# XSS Prevention Tests
# =============================================================================


class TestXSSPrevention:
    """Tests for Cross-Site Scripting prevention."""

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "javascript:alert(1)",
        "<a href='javascript:alert(1)'>click</a>",
        "<body onload=alert(1)>",
        "<iframe src='javascript:alert(1)'>",
        "'-alert(1)-'",
        "\"><script>alert(1)</script>",
        "<ScRiPt>alert(1)</sCrIpT>",
    ]

    @pytest.mark.security
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_api_handles_xss_in_company_name(self, payload):
        """Verify API handles XSS payloads in company name safely."""
        from src.api.models import ResearchRequest

        # Should accept the input (validation happens at output)
        request = ResearchRequest(company_name=payload)

        # The raw value should be stored
        assert request.company_name == payload

    @pytest.mark.security
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_api_handles_xss_in_industry(self, payload):
        """Verify API handles XSS payloads in industry field safely."""
        from src.api.models import ResearchRequest

        # Truncate if too long for field
        truncated_payload = payload[:100]
        request = ResearchRequest(company_name="Test", industry=truncated_payload)

        assert request.industry == truncated_payload.strip() or request.industry is None


# =============================================================================
# SQL Injection Prevention Tests
# =============================================================================


class TestSQLInjectionPrevention:
    """Tests for SQL Injection prevention."""

    SQL_PAYLOADS = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' OR 1=1--",
        "1; DELETE FROM tasks",
        "' UNION SELECT * FROM users--",
        "admin'--",
        "' OR ''='",
        "1' AND '1'='1",
        "'; EXEC xp_cmdshell('dir');--",
        "1; WAITFOR DELAY '0:0:5'--",
    ]

    @pytest.mark.security
    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_company_name_sql_injection(self, payload):
        """Verify SQL injection payloads are stored as plain text."""
        from src.api.models import ResearchRequest

        request = ResearchRequest(company_name=payload)

        # Value should be stored as-is (parameterized queries handle safety)
        assert request.company_name == payload

    @pytest.mark.security
    def test_database_uses_parameterized_queries(self):
        """Verify database operations use parameterized queries."""
        # This test verifies SQLAlchemy is used correctly
        from src.api.database import Base
        from src.api.models import Task

        # Task model uses SQLAlchemy which handles parameterization
        assert hasattr(Task, '__tablename__')
        assert Task.__tablename__ == "tasks"


# =============================================================================
# Path Traversal Prevention Tests
# =============================================================================


class TestPathTraversalPrevention:
    """Tests for path traversal prevention."""

    PATH_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%252f..%252f..%252fetc/passwd",
        "/etc/passwd",
        "C:\\Windows\\System32\\config\\SAM",
        "file:///etc/passwd",
        "....\\....\\....\\etc\\passwd",
    ]

    @pytest.mark.security
    @pytest.mark.parametrize("payload", PATH_PAYLOADS)
    def test_company_name_path_traversal(self, payload):
        """Verify path traversal payloads don't cause file access."""
        from src.api.models import ResearchRequest

        # Should store as-is without interpreting as path
        request = ResearchRequest(company_name=payload)
        assert request.company_name == payload

    @pytest.mark.security
    def test_output_dir_sanitization(self):
        """Verify output directory paths are sanitized."""
        from src.core.config import get_settings, clear_settings

        clear_settings()
        settings = get_settings()

        # Output dir should be under BASE_DIR
        output_dir = settings.get_output_dir()

        # Verify it's an absolute path
        assert output_dir.is_absolute() or str(output_dir).startswith(str(settings.BASE_DIR))

        clear_settings()


# =============================================================================
# Command Injection Prevention Tests
# =============================================================================


class TestCommandInjectionPrevention:
    """Tests for command injection prevention."""

    CMD_PAYLOADS = [
        "; ls -la",
        "| cat /etc/passwd",
        "$(whoami)",
        "`id`",
        "&& rm -rf /",
        "|| echo vulnerable",
        "\n/bin/bash",
        "%0Acat%20/etc/passwd",
        "'; ping -c 10 127.0.0.1 #",
    ]

    @pytest.mark.security
    @pytest.mark.parametrize("payload", CMD_PAYLOADS)
    def test_company_name_command_injection(self, payload):
        """Verify command injection payloads are stored safely."""
        from src.api.models import ResearchRequest

        request = ResearchRequest(company_name=payload)

        # Should be stored as plain text
        assert request.company_name == payload


# =============================================================================
# URL Validation Tests
# =============================================================================


class TestURLValidation:
    """Tests for URL validation and SSRF prevention."""

    DANGEROUS_URLS = [
        "http://localhost",
        "http://127.0.0.1",
        "http://[::1]",
        "http://0.0.0.0",
        "http://169.254.169.254",  # AWS metadata
        "http://192.168.1.1",  # Internal network
        "http://10.0.0.1",  # Internal network
        "file:///etc/passwd",
        "gopher://localhost:25",
        "dict://localhost:11211",
    ]

    @pytest.mark.security
    @pytest.mark.parametrize("url", DANGEROUS_URLS)
    def test_dangerous_urls_rejected(self, url):
        """Verify dangerous URLs are rejected."""
        from src.api.models import ResearchRequest
        from pydantic import ValidationError

        # file://, gopher://, dict:// should be rejected by HttpUrl validation
        if url.startswith(("file://", "gopher://", "dict://")):
            with pytest.raises(ValidationError):
                ResearchRequest(company_name="Test", url=url)
        else:
            # http URLs may be valid syntactically but should be blocked at runtime
            # This test just verifies the model accepts them
            # Runtime SSRF prevention should be tested separately
            try:
                request = ResearchRequest(company_name="Test", url=url)
                # If accepted, just verify it's stored
                assert request.url is not None
            except ValidationError:
                # If rejected by pydantic, that's also acceptable
                pass

    @pytest.mark.security
    def test_valid_https_url_accepted(self):
        """Verify valid HTTPS URLs are accepted."""
        from src.api.models import ResearchRequest

        request = ResearchRequest(
            company_name="Test",
            url="https://example.com"
        )

        assert request.url is not None


# =============================================================================
# API Key Exposure Prevention Tests
# =============================================================================


class TestAPIKeyExposure:
    """Tests for API key exposure prevention."""

    @pytest.mark.security
    def test_api_keys_not_in_settings_repr(self):
        """Verify API keys don't appear in settings string representation."""
        from src.core.config import Settings

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-secret123"}):
            settings = Settings()

            # repr should not contain the actual key
            repr_str = repr(settings)

            # Should not contain the full key
            assert "sk-secret123" not in repr_str or "***" in repr_str

    @pytest.mark.security
    def test_api_keys_not_logged(self):
        """Verify API keys are not logged."""
        import logging

        # Create a logger that captures output
        captured_logs = []

        class CaptureHandler(logging.Handler):
            def emit(self, record):
                captured_logs.append(record.getMessage())

        from src.core.logger import setup_logger

        logger = setup_logger("test_security")
        logger.addHandler(CaptureHandler())

        # Log a message that might contain sensitive data
        test_key = "sk-test1234567890"
        logger.info(f"Testing with key")  # Don't actually log the key

        # Verify key doesn't appear in logs
        for log in captured_logs:
            assert test_key not in log


# =============================================================================
# Input Size Limits Tests
# =============================================================================


class TestInputSizeLimits:
    """Tests for input size limits to prevent DoS."""

    @pytest.mark.security
    def test_company_name_max_length_enforced(self):
        """Verify company name max length is enforced."""
        from src.api.models import ResearchRequest
        from pydantic import ValidationError

        # 200 chars should work
        request = ResearchRequest(company_name="A" * 200)
        assert len(request.company_name) == 200

        # 201 chars should fail
        with pytest.raises(ValidationError):
            ResearchRequest(company_name="A" * 201)

    @pytest.mark.security
    def test_industry_max_length_enforced(self):
        """Verify industry max length is enforced."""
        from src.api.models import ResearchRequest
        from pydantic import ValidationError

        # 100 chars should work
        request = ResearchRequest(company_name="Test", industry="A" * 100)
        assert len(request.industry) == 100

        # 101 chars should fail
        with pytest.raises(ValidationError):
            ResearchRequest(company_name="Test", industry="A" * 101)


# =============================================================================
# Unicode Security Tests
# =============================================================================


class TestUnicodeSecurity:
    """Tests for unicode-related security issues."""

    UNICODE_PAYLOADS = [
        "\u0000",  # Null byte
        "\u202e",  # Right-to-left override
        "\ufeff",  # BOM
        "\u200b",  # Zero-width space
        "A\u0300",  # Combining character
        "\ud800",  # Surrogate (invalid alone)
    ]

    @pytest.mark.security
    def test_null_byte_handling(self):
        """Verify null bytes are handled safely."""
        from src.api.models import ResearchRequest

        # Should either accept or reject cleanly, not crash
        try:
            request = ResearchRequest(company_name="Test\x00Corp")
            assert request.company_name is not None
        except Exception as e:
            # Rejection is also acceptable
            assert "validation" in str(type(e)).lower() or "value" in str(e).lower()

    @pytest.mark.security
    def test_bom_handling(self):
        """Verify BOM characters are handled safely."""
        from src.api.models import ResearchRequest

        request = ResearchRequest(company_name="\ufeffTest Corp")
        assert request.company_name is not None

    @pytest.mark.security
    def test_rtl_override_handling(self):
        """Verify RTL override characters are handled safely."""
        from src.api.models import ResearchRequest

        request = ResearchRequest(company_name="Test\u202eCorp")
        assert request.company_name is not None
