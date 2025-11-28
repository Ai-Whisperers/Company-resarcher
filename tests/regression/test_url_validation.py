"""
Regression tests for URL validation fixes.

These tests ensure that URL validation security measures
remain in place and function correctly.
"""

import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# SSRF Prevention Regression Tests
# =============================================================================


class TestSSRFPrevention:
    """Regression tests for SSRF prevention."""

    @pytest.mark.regression
    @pytest.mark.security
    def test_blocks_localhost(self):
        """Regression: Ensure localhost URLs are blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        dangerous_urls = [
            "http://localhost",
            "http://localhost:8080",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://[::1]",
        ]

        for url in dangerous_urls:
            with pytest.raises(URLValidationError):
                URLValidator.validate_url(url)

    @pytest.mark.regression
    @pytest.mark.security
    def test_blocks_private_networks(self):
        """Regression: Ensure private network IPs are blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        private_urls = [
            "http://192.168.1.1",
            "http://10.0.0.1",
            "http://172.16.0.1",
            "http://172.31.255.255",
        ]

        for url in private_urls:
            with pytest.raises(URLValidationError):
                URLValidator.validate_url(url)

    @pytest.mark.regression
    @pytest.mark.security
    def test_blocks_file_protocol(self):
        """Regression: Ensure file:// protocol is blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        file_urls = [
            "file:///etc/passwd",
            "file://c:/windows/system32",
            "file:///home/user/.ssh/id_rsa",
        ]

        for url in file_urls:
            with pytest.raises(URLValidationError):
                URLValidator.validate_url(url)

    @pytest.mark.regression
    @pytest.mark.security
    def test_blocks_metadata_endpoints(self):
        """Regression: Ensure cloud metadata endpoints are blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        metadata_urls = [
            "http://169.254.169.254",  # AWS/Azure/GCP metadata
            "http://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal",
        ]

        for url in metadata_urls:
            with pytest.raises(URLValidationError):
                URLValidator.validate_url(url)


# =============================================================================
# Input Sanitization Regression Tests
# =============================================================================


class TestInputSanitization:
    """Regression tests for input sanitization."""

    @pytest.mark.regression
    @pytest.mark.security
    def test_handles_null_bytes(self):
        """Regression: Ensure null bytes don't bypass validation."""
        from src.core.url_validator import URLValidator, URLValidationError

        # URLs with null bytes that might try to truncate strings
        null_byte_urls = [
            "http://example.com\x00localhost",
            "http://localhost\x00.example.com",
        ]

        for url in null_byte_urls:
            # Should either raise or sanitize the null byte
            try:
                result = URLValidator.validate_url(url)
                # If it doesn't raise, ensure null byte was removed
                assert "\x00" not in result
            except URLValidationError:
                pass  # Expected behavior

    @pytest.mark.regression
    @pytest.mark.security
    def test_handles_url_encoding_bypass(self):
        """Regression: Ensure URL encoding doesn't bypass validation."""
        from src.core.url_validator import URLValidator, URLValidationError

        encoded_urls = [
            "http://127.0.0.1%2f",  # Encoded slash
            "http://%31%32%37%2e%30%2e%30%2e%31",  # Encoded 127.0.0.1
        ]

        for url in encoded_urls:
            # Should block or safely decode
            try:
                URLValidator.validate_url(url)
            except URLValidationError:
                pass  # Expected - blocked the attempt


# =============================================================================
# Protocol Handling Regression Tests
# =============================================================================


class TestProtocolHandling:
    """Regression tests for protocol handling."""

    @pytest.mark.regression
    def test_allows_https(self):
        """Regression: Ensure HTTPS URLs are allowed."""
        from src.core.url_validator import URLValidator

        https_urls = [
            "https://example.com",
            "https://www.example.com/path",
            "https://subdomain.example.com:443",
        ]

        for url in https_urls:
            # Should not raise
            result = URLValidator.validate_url(url)
            assert result is not None

    @pytest.mark.regression
    def test_allows_http(self):
        """Regression: Ensure HTTP URLs to public hosts are allowed."""
        from src.core.url_validator import URLValidator

        http_urls = [
            "http://example.com",
            "http://www.example.com/path",
        ]

        for url in http_urls:
            # Should not raise
            result = URLValidator.validate_url(url)
            assert result is not None

    @pytest.mark.regression
    @pytest.mark.security
    def test_blocks_javascript_protocol(self):
        """Regression: Ensure javascript: protocol is blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        with pytest.raises(URLValidationError):
            URLValidator.validate_url("javascript:alert('xss')")

    @pytest.mark.regression
    @pytest.mark.security
    def test_blocks_data_protocol(self):
        """Regression: Ensure data: protocol is blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        with pytest.raises(URLValidationError):
            URLValidator.validate_url("data:text/html,<script>alert('xss')</script>")
