"""
Unit tests for TechStackTool.

Tests the tech stack tool including:
- URL analysis
- Technology detection
- Security validation
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch

from src.tools.specialized.tech_stack import TechStackTool


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_webtech():
    """Create a mock webtech instance."""
    with patch("src.tools.tech_stack_tool.webtech") as mock_module:
        mock_wt = MagicMock()
        mock_module.WebTech.return_value = mock_wt
        yield mock_wt


@pytest.fixture
def tech_stack_tool(mock_webtech):
    """Create a TechStackTool instance with mocked webtech."""
    return TechStackTool()


# =============================================================================
# Initialization Tests
# =============================================================================


class TestTechStackToolInitialization:
    """Tests for TechStackTool initialization."""

    @pytest.mark.unit
    def test_creates_webtech_instance(self):
        """Verify WebTech instance is created."""
        with patch("src.tools.tech_stack_tool.webtech") as mock_module:
            TechStackTool()
            mock_module.WebTech.assert_called_once_with(options={"json": True})

    @pytest.mark.unit
    def test_stores_webtech_instance(self, mock_webtech):
        """Verify WebTech instance is stored."""
        tool = TechStackTool()
        assert tool.wt is not None


# =============================================================================
# URL Analysis Tests
# =============================================================================


class TestAnalyzeUrl:
    """Tests for analyze_url method."""

    @pytest.mark.unit
    def test_returns_report_for_valid_url(self, tech_stack_tool, mock_webtech):
        """Verify report is returned for valid URL."""
        mock_webtech.start_from_url.return_value = {
            "tech": ["React", "Node.js", "nginx"],
            "headers": {"Server": "nginx"},
        }

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com")

            assert "tech" in result
            assert "React" in result["tech"]

    @pytest.mark.unit
    def test_calls_webtech_with_url(self, tech_stack_tool, mock_webtech):
        """Verify webtech is called with correct URL."""
        mock_webtech.start_from_url.return_value = {}

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            tech_stack_tool.analyze_url("https://example.com")

            mock_webtech.start_from_url.assert_called_once_with("https://example.com")


# =============================================================================
# URL Validation Tests
# =============================================================================


class TestURLValidation:
    """Tests for URL validation in analyze_url."""

    @pytest.mark.unit
    @pytest.mark.security
    def test_validates_url_before_analysis(self, tech_stack_tool, mock_webtech):
        """Verify URL is validated before analysis."""
        mock_webtech.start_from_url.return_value = {}

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url") as mock_validate:
            tech_stack_tool.analyze_url("https://example.com")

            mock_validate.assert_called_once_with("https://example.com")

    @pytest.mark.unit
    @pytest.mark.security
    def test_blocks_invalid_url(self, tech_stack_tool, mock_webtech):
        """Verify invalid URLs are blocked."""
        from src.core.validation.url_validator import URLValidationError

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url") as mock_validate:
            mock_validate.side_effect = URLValidationError("Blocked URL")

            result = tech_stack_tool.analyze_url("http://localhost")

            assert "error" in result
            assert "security" in result["error"].lower()

    @pytest.mark.unit
    @pytest.mark.security
    def test_blocks_localhost(self, tech_stack_tool, mock_webtech):
        """Verify localhost URLs are blocked."""
        from src.core.validation.url_validator import URLValidationError

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url") as mock_validate:
            mock_validate.side_effect = URLValidationError("Localhost blocked")

            result = tech_stack_tool.analyze_url("http://127.0.0.1")

            assert "error" in result

    @pytest.mark.unit
    @pytest.mark.security
    def test_blocks_private_ip(self, tech_stack_tool, mock_webtech):
        """Verify private IPs are blocked."""
        from src.core.validation.url_validator import URLValidationError

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url") as mock_validate:
            mock_validate.side_effect = URLValidationError("Private IP blocked")

            result = tech_stack_tool.analyze_url("http://192.168.1.1")

            assert "error" in result


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in analyze_url."""

    @pytest.mark.unit
    def test_handles_webtech_exception(self, tech_stack_tool, mock_webtech):
        """Verify webtech exceptions are handled."""
        mock_webtech.start_from_url.side_effect = Exception("Connection failed")

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com")

            assert result == {}

    @pytest.mark.unit
    def test_handles_timeout(self, tech_stack_tool, mock_webtech):
        """Verify timeout is handled."""
        import socket
        mock_webtech.start_from_url.side_effect = socket.timeout("Timed out")

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://slow-site.com")

            assert result == {}

    @pytest.mark.unit
    def test_handles_connection_error(self, tech_stack_tool, mock_webtech):
        """Verify connection errors are handled."""
        mock_webtech.start_from_url.side_effect = ConnectionError("No connection")

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://offline-site.com")

            assert result == {}


# =============================================================================
# Return Value Tests
# =============================================================================


class TestReturnValues:
    """Tests for return value structure."""

    @pytest.mark.unit
    def test_returns_dict(self, tech_stack_tool, mock_webtech):
        """Verify analyze_url returns a dict."""
        mock_webtech.start_from_url.return_value = {"tech": []}

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com")

            assert isinstance(result, dict)

    @pytest.mark.unit
    def test_returns_empty_dict_on_error(self, tech_stack_tool, mock_webtech):
        """Verify empty dict is returned on error."""
        mock_webtech.start_from_url.side_effect = Exception("Error")

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com")

            assert result == {}

    @pytest.mark.unit
    def test_preserves_webtech_response_structure(self, tech_stack_tool, mock_webtech):
        """Verify webtech response structure is preserved."""
        expected_response = {
            "tech": ["React", "webpack"],
            "headers": {"X-Powered-By": "Express"},
            "meta": {"generator": "Next.js"},
        }
        mock_webtech.start_from_url.return_value = expected_response

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com")

            assert result == expected_response


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.unit
    def test_handles_empty_url(self, tech_stack_tool, mock_webtech):
        """Verify empty URL is handled."""
        from src.core.validation.url_validator import URLValidationError

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url") as mock_validate:
            mock_validate.side_effect = URLValidationError("Empty URL")

            result = tech_stack_tool.analyze_url("")

            assert "error" in result

    @pytest.mark.unit
    def test_handles_url_with_path(self, tech_stack_tool, mock_webtech):
        """Verify URL with path is handled."""
        mock_webtech.start_from_url.return_value = {"tech": ["WordPress"]}

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com/blog/post")

            mock_webtech.start_from_url.assert_called_once_with("https://example.com/blog/post")

    @pytest.mark.unit
    def test_handles_url_with_query_params(self, tech_stack_tool, mock_webtech):
        """Verify URL with query params is handled."""
        mock_webtech.start_from_url.return_value = {"tech": []}

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com?page=1")

            mock_webtech.start_from_url.assert_called_once()

    @pytest.mark.unit
    def test_handles_url_with_port(self, tech_stack_tool, mock_webtech):
        """Verify URL with port is handled."""
        mock_webtech.start_from_url.return_value = {"tech": []}

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com:8443")

            mock_webtech.start_from_url.assert_called_once()

    @pytest.mark.unit
    def test_handles_unicode_url(self, tech_stack_tool, mock_webtech):
        """Verify unicode URL is handled."""
        mock_webtech.start_from_url.return_value = {"tech": []}

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://例え.jp")

            mock_webtech.start_from_url.assert_called_once()

    @pytest.mark.unit
    def test_handles_none_response(self, tech_stack_tool, mock_webtech):
        """Verify None response from webtech is handled."""
        mock_webtech.start_from_url.return_value = None

        with patch("src.tools.tech_stack_tool.URLValidator.validate_url"):
            result = tech_stack_tool.analyze_url("https://example.com")

            # Should return None (the actual response)
            assert result is None
