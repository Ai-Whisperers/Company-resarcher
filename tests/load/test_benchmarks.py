"""
Performance benchmarks using pytest-benchmark.

Run with:
    pytest tests/load/test_benchmarks.py --benchmark-only
"""

import pytest
from unittest.mock import MagicMock, patch
import json
import hashlib


# =============================================================================
# Benchmark Fixtures
# =============================================================================


@pytest.fixture
def sample_data():
    """Sample data for benchmarks."""
    return {
        "company_name": "Test Corporation",
        "website": "https://testcorp.com",
        "financial_data": {"revenue": 1000000, "profit": 150000},
        "market_data": {"size": "5B", "growth": "10%"},
    }


# =============================================================================
# API Model Benchmarks
# =============================================================================


class TestModelBenchmarks:
    """Benchmarks for Pydantic model operations."""

    @pytest.mark.benchmark(group="models")
    def test_research_request_creation(self, benchmark):
        """Benchmark ResearchRequest creation."""
        from src.api.models import ResearchRequest

        def create_request():
            return ResearchRequest(
                company_name="Test Corporation",
                url="https://testcorp.com",
                industry="Technology",
                country="USA",
            )

        result = benchmark(create_request)
        assert result.company_name == "Test Corporation"

    @pytest.mark.benchmark(group="models")
    def test_research_request_validation(self, benchmark):
        """Benchmark ResearchRequest validation."""
        from src.api.models import ResearchRequest

        def validate_request():
            try:
                ResearchRequest(company_name="")
                return False
            except Exception:
                return True

        result = benchmark(validate_request)
        assert result is True

    @pytest.mark.benchmark(group="models")
    def test_research_response_serialization(self, benchmark):
        """Benchmark ResearchResponse serialization."""
        from src.api.models import ResearchResponse

        response = ResearchResponse(
            task_id="task-123",
            status="completed",
            message="Research completed",
        )

        result = benchmark(lambda: response.model_dump_json())
        assert "task-123" in result


# =============================================================================
# State Model Benchmarks
# =============================================================================


class TestStateBenchmarks:
    """Benchmarks for state model operations."""

    @pytest.mark.benchmark(group="state")
    def test_research_state_creation(self, benchmark):
        """Benchmark ResearchState creation."""
        from src.graph.state import ResearchState

        def create_state():
            return ResearchState(
                company_name="Test Corp",
                website="https://test.com",
            )

        result = benchmark(create_state)
        assert result.company_name == "Test Corp"

    @pytest.mark.benchmark(group="state")
    def test_research_state_with_data(self, benchmark, sample_data):
        """Benchmark ResearchState creation with data."""
        from src.graph.state import ResearchState

        def create_state():
            return ResearchState(
                company_name=sample_data["company_name"],
                website=sample_data["website"],
                financial_data=sample_data["financial_data"],
                market_data=sample_data["market_data"],
            )

        result = benchmark(create_state)
        assert result.financial_data["revenue"] == 1000000

    @pytest.mark.benchmark(group="state")
    def test_research_state_serialization(self, benchmark, sample_data):
        """Benchmark ResearchState serialization."""
        from src.graph.state import ResearchState

        state = ResearchState(
            company_name=sample_data["company_name"],
            website=sample_data["website"],
            financial_data=sample_data["financial_data"],
            market_data=sample_data["market_data"],
        )

        result = benchmark(lambda: state.model_dump())
        assert isinstance(result, dict)


# =============================================================================
# Cache Benchmarks
# =============================================================================


class TestCacheBenchmarks:
    """Benchmarks for caching operations."""

    @pytest.mark.benchmark(group="cache")
    def test_cache_key_generation(self, benchmark):
        """Benchmark cache key generation."""

        def generate_key():
            data = "test prompt with some content"
            return hashlib.sha256(data.encode()).hexdigest()

        result = benchmark(generate_key)
        assert len(result) == 64

    @pytest.mark.benchmark(group="cache")
    def test_json_serialization(self, benchmark, sample_data):
        """Benchmark JSON serialization for caching."""

        result = benchmark(lambda: json.dumps(sample_data))
        assert "Test Corporation" in result

    @pytest.mark.benchmark(group="cache")
    def test_json_deserialization(self, benchmark, sample_data):
        """Benchmark JSON deserialization."""
        json_str = json.dumps(sample_data)

        result = benchmark(lambda: json.loads(json_str))
        assert result["company_name"] == "Test Corporation"


# =============================================================================
# URL Validation Benchmarks
# =============================================================================


class TestURLValidationBenchmarks:
    """Benchmarks for URL validation."""

    @pytest.mark.benchmark(group="validation")
    def test_url_validation_valid(self, benchmark):
        """Benchmark valid URL validation."""
        from src.core.validation.url_validator import URLValidator

        result = benchmark(lambda: URLValidator.validate_url("https://example.com"))
        assert result is not None

    @pytest.mark.benchmark(group="validation")
    def test_url_validation_invalid(self, benchmark):
        """Benchmark invalid URL validation."""
        from src.core.validation.url_validator import URLValidator, URLValidationError

        def validate_invalid():
            try:
                URLValidator.validate_url("http://localhost")
                return False
            except URLValidationError:
                return True

        result = benchmark(validate_invalid)
        assert result is True


# =============================================================================
# Source Classification Benchmarks
# =============================================================================


class TestClassificationBenchmarks:
    """Benchmarks for source classification."""

    @pytest.mark.benchmark(group="classification")
    def test_source_type_classification(self, benchmark):
        """Benchmark source type classification."""
        from src.tools.browser import BrowserTool

        tool = BrowserTool()
        url = "https://news.example.com/article/test"
        content = "This is a news article about the company."

        result = benchmark(lambda: tool.classify_source_type(url, content))
        assert result is not None


# =============================================================================
# String Processing Benchmarks
# =============================================================================


class TestStringProcessingBenchmarks:
    """Benchmarks for string processing operations."""

    @pytest.mark.benchmark(group="strings")
    def test_company_name_normalization(self, benchmark):
        """Benchmark company name normalization."""

        def normalize(name):
            return name.strip().lower().replace(" ", "_")

        result = benchmark(lambda: normalize("  Test Corporation  "))
        assert result == "test_corporation"

    @pytest.mark.benchmark(group="strings")
    def test_markdown_header_extraction(self, benchmark):
        """Benchmark markdown header extraction."""
        content = """
        # Main Title

        Some content here.

        ## Section 1

        More content.

        ## Section 2

        Even more content.
        """

        def extract_headers():
            import re
            return re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)

        result = benchmark(extract_headers)
        assert len(result) == 3


# =============================================================================
# Data Factory Benchmarks
# =============================================================================


class TestFactoryBenchmarks:
    """Benchmarks for test data factories."""

    @pytest.mark.benchmark(group="factories")
    def test_company_factory_creation(self, benchmark):
        """Benchmark company factory."""
        from tests.factories import CompanyFactory

        result = benchmark(CompanyFactory.create)
        assert "name" in result

    @pytest.mark.benchmark(group="factories")
    def test_company_factory_batch(self, benchmark):
        """Benchmark batch company creation."""
        from tests.factories import CompanyFactory

        result = benchmark(lambda: CompanyFactory.create_batch(10))
        assert len(result) == 10

    @pytest.mark.benchmark(group="factories")
    def test_research_source_factory(self, benchmark):
        """Benchmark research source factory."""
        from tests.factories import ResearchSourceFactory

        result = benchmark(ResearchSourceFactory.create)
        assert "url" in result
