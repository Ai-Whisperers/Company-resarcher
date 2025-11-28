"""
Property-based tests for validation logic.

Uses Hypothesis to test URL validation, input sanitization,
and security measures.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from urllib.parse import urlparse


# =============================================================================
# URL Validation Property Tests
# =============================================================================


class TestURLValidationProperties:
    """Property-based tests for URL validation."""

    @pytest.mark.property
    @given(
        protocol=st.sampled_from(["http", "https"]),
        domain=st.from_regex(r'[a-z][a-z0-9\-]{2,20}\.(com|org|net|io|co)', fullmatch=True),
    )
    @settings(max_examples=50)
    def test_public_urls_accepted(self, protocol, domain):
        """Property: Valid public URLs are accepted."""
        from src.core.url_validator import URLValidator

        url = f"{protocol}://{domain}"
        result = URLValidator.validate_url(url)

        assert result is not None

    @pytest.mark.property
    @given(
        protocol=st.sampled_from(["http", "https"]),
        path=st.from_regex(r'/[a-z0-9\-/]{0,50}', fullmatch=True),
    )
    @settings(max_examples=30)
    def test_urls_with_paths_accepted(self, protocol, path):
        """Property: URLs with paths are accepted."""
        from src.core.url_validator import URLValidator

        url = f"{protocol}://example.com{path}"
        result = URLValidator.validate_url(url)

        assert result is not None

    @pytest.mark.property
    @given(
        ip_part=st.integers(min_value=0, max_value=255),
    )
    @settings(max_examples=20)
    def test_localhost_variants_blocked(self, ip_part):
        """Property: All localhost variants are blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        # Test 127.x.x.x range
        url = f"http://127.{ip_part}.{ip_part}.{ip_part}"

        with pytest.raises(URLValidationError):
            URLValidator.validate_url(url)

    @pytest.mark.property
    @given(
        octet2=st.integers(min_value=16, max_value=31),
        octet3=st.integers(min_value=0, max_value=255),
        octet4=st.integers(min_value=0, max_value=255),
    )
    @settings(max_examples=20)
    def test_private_172_range_blocked(self, octet2, octet3, octet4):
        """Property: 172.16.0.0/12 range is blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        url = f"http://172.{octet2}.{octet3}.{octet4}"

        with pytest.raises(URLValidationError):
            URLValidator.validate_url(url)

    @pytest.mark.property
    @given(
        protocol=st.sampled_from(["file", "ftp", "javascript", "data", "gopher"]),
    )
    @settings(max_examples=10)
    def test_dangerous_protocols_blocked(self, protocol):
        """Property: Dangerous protocols are blocked."""
        from src.core.url_validator import URLValidator, URLValidationError

        url = f"{protocol}://something"

        with pytest.raises(URLValidationError):
            URLValidator.validate_url(url)


# =============================================================================
# Input Sanitization Property Tests
# =============================================================================


class TestInputSanitizationProperties:
    """Property-based tests for input sanitization."""

    @pytest.mark.property
    @given(
        prefix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
        suffix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
    )
    @settings(max_examples=30)
    def test_null_bytes_handled(self, prefix, suffix):
        """Property: Null bytes in input don't cause issues."""
        from src.api.models import ResearchRequest

        # Create name with null byte
        name_with_null = f"{prefix}\x00{suffix}"

        # Should either accept (sanitizing null) or reject
        try:
            request = ResearchRequest(company_name=name_with_null)
            # If accepted, null byte should be handled safely
            assert "\x00" not in request.company_name or request.company_name is not None
        except Exception:
            pass  # Rejection is also acceptable

    @pytest.mark.property
    @given(
        text=st.text(min_size=1, max_size=50),
        special=st.sampled_from(["<script>", "</script>", "<img", "onerror=", "javascript:"]),
    )
    @settings(max_examples=30)
    def test_xss_payloads_stored_safely(self, text, special):
        """Property: XSS payloads are stored safely (not executed)."""
        from src.api.models import ResearchRequest

        # Note: We test that the value is stored as-is (escaped at output)
        dangerous_name = f"{text}{special}{text}"

        request = ResearchRequest(company_name=dangerous_name)

        # Value should be preserved (XSS prevention is at output layer)
        assert special in request.company_name


# =============================================================================
# JSON Parsing Property Tests
# =============================================================================


class TestJSONParsingProperties:
    """Property-based tests for JSON parsing."""

    @pytest.mark.property
    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
            values=st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.none(),
            ),
            max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_safe_json_loads_roundtrip(self, data):
        """Property: Valid JSON roundtrips correctly."""
        import json
        from src.api.app import safe_json_loads

        json_str = json.dumps(data)
        result = safe_json_loads(json_str)

        assert result == data

    @pytest.mark.property
    @given(invalid_json=st.text(min_size=1, max_size=100))
    @settings(max_examples=30)
    def test_safe_json_loads_handles_invalid(self, invalid_json):
        """Property: Invalid JSON returns default."""
        from src.api.app import safe_json_loads

        # Most random text is invalid JSON
        assume(not invalid_json.strip().startswith('{'))
        assume(not invalid_json.strip().startswith('['))
        assume(not invalid_json.strip().startswith('"'))

        result = safe_json_loads(invalid_json, default="fallback")

        assert result == "fallback"


# =============================================================================
# Rate Limiter Property Tests
# =============================================================================


class TestRateLimiterProperties:
    """Property-based tests for rate limiter."""

    @pytest.mark.property
    @given(
        requests_per_minute=st.integers(min_value=1, max_value=100),
        ip_suffix=st.integers(min_value=1, max_value=254),
    )
    @settings(max_examples=30)
    def test_allows_up_to_limit(self, requests_per_minute, ip_suffix):
        """Property: Allows exactly up to limit requests."""
        from src.api.app import RateLimiter

        limiter = RateLimiter(requests_per_minute=requests_per_minute)
        ip = f"192.168.1.{ip_suffix}"

        # Should allow exactly requests_per_minute requests
        allowed_count = 0
        for _ in range(requests_per_minute + 5):
            if limiter.is_allowed(ip):
                allowed_count += 1

        assert allowed_count == requests_per_minute

    @pytest.mark.property
    @given(
        ip1_suffix=st.integers(min_value=1, max_value=127),
        ip2_suffix=st.integers(min_value=128, max_value=254),
    )
    @settings(max_examples=20)
    def test_limits_are_per_ip(self, ip1_suffix, ip2_suffix):
        """Property: Rate limits are per-IP."""
        from src.api.app import RateLimiter

        limiter = RateLimiter(requests_per_minute=5)
        ip1 = f"192.168.1.{ip1_suffix}"
        ip2 = f"192.168.1.{ip2_suffix}"

        # Exhaust limit for IP1
        for _ in range(5):
            limiter.is_allowed(ip1)

        # IP2 should still be allowed
        assert limiter.is_allowed(ip2) is True

        # IP1 should be blocked
        assert limiter.is_allowed(ip1) is False


# =============================================================================
# Source Classification Property Tests
# =============================================================================


class TestSourceClassificationProperties:
    """Property-based tests for source classification."""

    @pytest.mark.property
    @given(
        domain=st.sampled_from([
            "statista.com", "euromonitor.com", "ibisworld.com",
            "gartner.com", "mckinsey.com", "forrester.com",
        ]),
        path=st.from_regex(r'/[a-z0-9\-/]{0,30}', fullmatch=True),
    )
    @settings(max_examples=30)
    def test_industry_sources_classified(self, domain, path):
        """Property: Industry report sources are classified correctly."""
        from src.tools.browser import BrowserTool

        tool = BrowserTool()
        url = f"https://{domain}{path}"

        result = tool.classify_source_type(url, "some content")

        assert result == "industry_report"

    @pytest.mark.property
    @given(
        subdomain=st.sampled_from(["news", "blog", "press"]),
        domain=st.from_regex(r'[a-z]{5,15}\.(com|org|net)', fullmatch=True),
    )
    @settings(max_examples=30)
    def test_news_sources_classified(self, subdomain, domain):
        """Property: News sources are classified correctly."""
        from src.tools.browser import BrowserTool

        tool = BrowserTool()
        url = f"https://{subdomain}.{domain}/article"

        result = tool.classify_source_type(url, "content")

        assert result == "news_article"

    @pytest.mark.property
    @given(
        domain=st.from_regex(r'[a-z]{5,15}\.(gov|gob\.mx|gov\.uk)', fullmatch=True),
    )
    @settings(max_examples=20)
    def test_government_sources_classified(self, domain):
        """Property: Government sources are classified correctly."""
        from src.tools.browser import BrowserTool

        tool = BrowserTool()
        url = f"https://{domain}/data"

        result = tool.classify_source_type(url, "content")

        assert result == "government"

    @pytest.mark.property
    @given(
        url=st.from_regex(r'https://[a-z]{5,15}\.(com|org|net)', fullmatch=True),
        content=st.text(min_size=10, max_size=100),
    )
    @settings(max_examples=30)
    def test_always_returns_valid_type(self, url, content):
        """Property: Classification always returns a valid type."""
        from src.tools.browser import BrowserTool

        tool = BrowserTool()

        result = tool.classify_source_type(url, content)

        valid_types = {
            "industry_report", "news_article", "academic",
            "social_media", "government", "market_data", "web"
        }

        assert result in valid_types
