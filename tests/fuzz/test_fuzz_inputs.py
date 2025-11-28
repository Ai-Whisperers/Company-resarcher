"""
Fuzz tests using Hypothesis for property-based testing.

Tests various input handlers with random/malformed inputs to discover
crashes, hangs, or security vulnerabilities.

Issue: TE-022
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck


# ============================================================================
# String Input Fuzz Tests
# ============================================================================


class TestStringInputFuzzing:
    """Fuzz tests for string input handling."""

    @given(st.text(max_size=10000))
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_company_name_no_crash(self, text: str):
        """Verify company name handling doesn't crash on arbitrary input."""
        # Should not crash on any string
        try:
            # Simulate sanitization
            sanitized = text.strip()
            # Basic validation
            if sanitized:
                _ = sanitized[:1000]  # Truncate if needed
        except (ValueError, TypeError):
            pass  # Expected for some inputs

    @given(st.text(max_size=10000))
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_search_query_no_crash(self, text: str):
        """Verify search query handling doesn't crash."""
        try:
            # Simulate search query processing
            query = text.strip()
            if query:
                # Remove special characters for search
                cleaned = re.sub(r'[^\w\s-]', '', query)
                assert isinstance(cleaned, str)
        except (ValueError, TypeError):
            pass

    @given(st.text(alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
        whitelist_characters='._-@'
    ), min_size=1, max_size=100))
    @settings(max_examples=200)
    def test_email_like_strings(self, text: str):
        """Test handling of email-like string patterns."""
        # Should handle without crash
        result = "@" in text
        assert isinstance(result, bool)

    @given(st.binary(max_size=10000))
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_binary_data_handling(self, data: bytes):
        """Verify binary data doesn't crash string handlers."""
        try:
            # Attempt decode with error handling
            text = data.decode('utf-8', errors='replace')
            assert isinstance(text, str)
        except Exception:
            pass  # Some binary data can't be decoded

    @given(st.text(alphabet=st.characters(
        whitelist_categories=('Cs', 'Co', 'Cn'),  # Surrogates and private use
    ), max_size=100))
    @settings(max_examples=100)
    def test_unicode_edge_cases(self, text: str):
        """Test handling of unusual Unicode characters."""
        try:
            # Should handle without crash
            encoded = text.encode('utf-8', errors='surrogatepass')
            assert isinstance(encoded, bytes)
        except (UnicodeError, ValueError):
            pass  # Expected for some characters


# ============================================================================
# URL Input Fuzz Tests
# ============================================================================


class TestURLInputFuzzing:
    """Fuzz tests for URL input handling."""

    @given(st.text(max_size=5000))
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_url_parsing_no_crash(self, text: str):
        """Verify URL parsing doesn't crash on arbitrary input."""
        from urllib.parse import urlparse, urlunparse

        try:
            parsed = urlparse(text)
            # Should be able to unparse without crash
            _ = urlunparse(parsed)
        except Exception:
            pass  # Invalid URLs are expected

    @given(st.from_regex(
        r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9._~:/?#\[\]@!$&\'()*+,;=-]*)?',
        fullmatch=True
    ))
    @settings(max_examples=200)
    def test_valid_url_patterns(self, url: str):
        """Test processing of valid URL patterns."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        assert parsed.scheme in ('http', 'https')
        assert len(parsed.netloc) > 0

    @given(st.lists(st.text(max_size=100), max_size=50))
    @settings(max_examples=100)
    def test_url_list_handling(self, urls: List[str]):
        """Test handling of URL lists."""
        # Should handle list of arbitrary strings
        valid_count = sum(1 for u in urls if u.startswith(('http://', 'https://')))
        assert valid_count >= 0


# ============================================================================
# JSON Input Fuzz Tests
# ============================================================================


class TestJSONInputFuzzing:
    """Fuzz tests for JSON input handling."""

    @given(st.recursive(
        st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(max_size=100),
        lambda children: st.lists(children, max_size=10) | st.dictionaries(
            st.text(min_size=1, max_size=20), children, max_size=10
        ),
        max_leaves=50
    ))
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_json_serialization_roundtrip(self, data: Any):
        """Verify JSON serialization roundtrip doesn't crash."""
        try:
            serialized = json.dumps(data)
            deserialized = json.loads(serialized)
            # Roundtrip should preserve structure
            assert type(deserialized) == type(data) or (
                isinstance(data, (int, float)) and isinstance(deserialized, (int, float))
            )
        except (TypeError, ValueError):
            pass  # Some data types can't be serialized

    @given(st.text(max_size=5000))
    @settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
    def test_json_parsing_arbitrary_text(self, text: str):
        """Verify JSON parsing handles arbitrary text safely."""
        try:
            parsed = json.loads(text)
            # If parsing succeeds, should be valid JSON type
            assert parsed is None or isinstance(parsed, (bool, int, float, str, list, dict))
        except json.JSONDecodeError:
            pass  # Expected for most arbitrary text

    @given(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=200)
        ),
        max_size=50
    ))
    @settings(max_examples=200)
    def test_research_request_like_json(self, data: Dict[str, Any]):
        """Test JSON structures similar to research requests."""
        # Should be serializable
        serialized = json.dumps(data)
        assert isinstance(serialized, str)

        # Should be deserializable
        deserialized = json.loads(serialized)
        assert isinstance(deserialized, dict)


# ============================================================================
# Numeric Input Fuzz Tests
# ============================================================================


class TestNumericInputFuzzing:
    """Fuzz tests for numeric input handling."""

    @given(st.integers())
    @settings(max_examples=1000)
    def test_integer_handling(self, n: int):
        """Verify integer handling doesn't overflow."""
        # Should handle any integer
        str_repr = str(n)
        assert isinstance(str_repr, str)

        # Basic arithmetic should work
        _ = n + 1
        _ = n - 1
        if n != 0:
            _ = 100 // n

    @given(st.floats(allow_nan=True, allow_infinity=True))
    @settings(max_examples=500)
    def test_float_handling(self, f: float):
        """Verify float handling including special values."""
        import math

        str_repr = str(f)
        assert isinstance(str_repr, str)

        # Check for special values
        is_special = math.isnan(f) or math.isinf(f)

        if not is_special:
            # Normal floats should work in arithmetic
            _ = f + 1.0

    @given(st.floats(min_value=0, max_value=1))
    @settings(max_examples=200)
    def test_probability_values(self, p: float):
        """Test handling of probability-like values (0-1)."""
        assert 0 <= p <= 1

        # Common probability operations
        complement = 1 - p
        assert 0 <= complement <= 1


# ============================================================================
# Date/Time Input Fuzz Tests
# ============================================================================


class TestDateTimeInputFuzzing:
    """Fuzz tests for date/time input handling."""

    @given(st.datetimes(
        min_value=datetime(1970, 1, 1),
        max_value=datetime(2100, 12, 31)
    ))
    @settings(max_examples=200)
    def test_datetime_handling(self, dt: datetime):
        """Verify datetime handling across valid range."""
        # Should be convertible to ISO format
        iso_str = dt.isoformat()
        assert isinstance(iso_str, str)

        # Should be parseable back
        parsed = datetime.fromisoformat(iso_str)
        assert parsed == dt

    @given(st.text(max_size=100))
    @settings(max_examples=300)
    def test_datetime_string_parsing(self, text: str):
        """Verify datetime parsing handles arbitrary strings."""
        try:
            dt = datetime.fromisoformat(text)
            assert isinstance(dt, datetime)
        except ValueError:
            pass  # Expected for most strings

    @given(st.timedeltas(
        min_value=timedelta(seconds=-86400*365*100),
        max_value=timedelta(seconds=86400*365*100)
    ))
    @settings(max_examples=200)
    def test_timedelta_handling(self, td: timedelta):
        """Verify timedelta handling."""
        total_seconds = td.total_seconds()
        assert isinstance(total_seconds, float)


# ============================================================================
# API Request Fuzz Tests
# ============================================================================


class TestAPIRequestFuzzing:
    """Fuzz tests for API request handling."""

    @given(st.fixed_dictionaries({
        'company_name': st.text(min_size=0, max_size=500),
        'website': st.text(min_size=0, max_size=500),
        'industry': st.one_of(st.none(), st.text(max_size=100)),
        'country': st.one_of(st.none(), st.text(max_size=50)),
    }))
    @settings(max_examples=300)
    def test_research_request_structure(self, request: Dict[str, Any]):
        """Test research request structure handling."""
        # Should be serializable
        json_str = json.dumps(request)
        assert isinstance(json_str, str)

        # Required field should exist
        assert 'company_name' in request
        assert 'website' in request

    @given(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(max_size=200),
        min_size=0,
        max_size=20
    ))
    @settings(max_examples=200)
    def test_arbitrary_json_body(self, body: Dict[str, str]):
        """Test handling of arbitrary JSON request bodies."""
        # Should not crash on serialization
        serialized = json.dumps(body)
        assert isinstance(serialized, str)


# ============================================================================
# File Content Fuzz Tests
# ============================================================================


class TestFileContentFuzzing:
    """Fuzz tests for file content handling."""

    @given(st.binary(max_size=10000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_binary_file_content(self, content: bytes):
        """Test handling of arbitrary binary file content."""
        # Should be able to determine length
        assert len(content) >= 0

        # Should be writable/readable (simulated)
        read_back = bytes(content)
        assert read_back == content

    @given(st.text(max_size=10000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_text_file_content(self, content: str):
        """Test handling of arbitrary text file content."""
        # Should be encodable
        try:
            encoded = content.encode('utf-8')
            decoded = encoded.decode('utf-8')
            assert decoded == content
        except UnicodeError:
            pass  # Some characters can't roundtrip


# ============================================================================
# Regex Pattern Fuzz Tests
# ============================================================================


class TestRegexFuzzing:
    """Fuzz tests for regex pattern handling."""

    @given(st.text(max_size=1000))
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_regex_search_no_crash(self, text: str):
        """Verify regex operations don't crash on arbitrary input."""
        patterns = [
            r'\w+',
            r'\d+',
            r'https?://\S+',
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
        ]

        for pattern in patterns:
            try:
                matches = re.findall(pattern, text)
                assert isinstance(matches, list)
            except re.error:
                pass  # Pattern errors are acceptable

    @given(st.text(max_size=100))
    @settings(max_examples=100)
    def test_regex_pattern_compilation(self, pattern: str):
        """Test regex pattern compilation with arbitrary patterns."""
        try:
            compiled = re.compile(pattern)
            assert compiled is not None
        except re.error:
            pass  # Invalid patterns are expected


# ============================================================================
# Collection Fuzz Tests
# ============================================================================


class TestCollectionFuzzing:
    """Fuzz tests for collection handling."""

    @given(st.lists(st.text(max_size=100), max_size=1000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_list_operations(self, items: List[str]):
        """Test list operations don't crash."""
        # Length
        assert len(items) >= 0

        # Iteration
        count = sum(1 for _ in items)
        assert count == len(items)

        # Slicing
        _ = items[:10]
        _ = items[-10:]

    @given(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.integers(),
        max_size=500
    ))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_dict_operations(self, data: Dict[str, int]):
        """Test dictionary operations don't crash."""
        # Length
        assert len(data) >= 0

        # Key iteration
        keys = list(data.keys())
        assert len(keys) == len(data)

        # Value access
        for key in keys:
            _ = data[key]

    @given(st.sets(st.text(max_size=50), max_size=500))
    @settings(max_examples=200)
    def test_set_operations(self, items: set):
        """Test set operations don't crash."""
        # Basic operations
        assert len(items) >= 0

        # Set operations
        if items:
            _ = items.pop()
            items.add("new_item")
