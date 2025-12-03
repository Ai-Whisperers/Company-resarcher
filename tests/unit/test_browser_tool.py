"""
Unit tests for BrowserTool.

Tests the browser tool functionality including:
- Source type classification
- Metadata extraction
- URL validation
- Concurrent fetching with semaphore
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from bs4 import BeautifulSoup

from src.tools.browser import BrowserTool, FETCH_OVERALL_TIMEOUT
from src.core.types.base import ResearchSource


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def browser_tool():
    """Create a BrowserTool instance."""
    return BrowserTool(max_concurrent=5)


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page Title</title>
        <meta name="description" content="This is a test description">
        <meta name="keywords" content="test, keywords, sample">
        <meta name="author" content="Test Author">
        <meta property="article:published_time" content="2024-01-15">
    </head>
    <body>
        <header>Header content</header>
        <nav>Navigation</nav>
        <main>
            <article>
                <h1>Main Article Title</h1>
                <p>This is the main content of the page.</p>
                <p>More content here with important information.</p>
            </article>
        </main>
        <aside>Sidebar content</aside>
        <footer>Footer content</footer>
        <script>console.log('script');</script>
        <style>.hidden { display: none; }</style>
    </body>
    </html>
    """


@pytest.fixture
def soup(sample_html):
    """Create BeautifulSoup object from sample HTML."""
    return BeautifulSoup(sample_html, "html.parser")


# =============================================================================
# Initialization Tests
# =============================================================================


class TestBrowserToolInitialization:
    """Tests for BrowserTool initialization."""

    @pytest.mark.unit
    def test_initializes_with_default_concurrency(self):
        """Verify default max_concurrent is 5."""
        tool = BrowserTool()
        assert tool.max_concurrent == 5

    @pytest.mark.unit
    def test_initializes_with_custom_concurrency(self):
        """Verify custom max_concurrent is set."""
        tool = BrowserTool(max_concurrent=10)
        assert tool.max_concurrent == 10

    @pytest.mark.unit
    def test_browser_starts_as_none(self):
        """Verify browser is None before start."""
        tool = BrowserTool()
        assert tool.browser is None
        assert tool.playwright is None

    @pytest.mark.unit
    def test_semaphore_initialized(self):
        """Verify semaphore is initialized immediately."""
        tool = BrowserTool(max_concurrent=3)
        assert tool.semaphore is not None
        assert isinstance(tool._semaphore, asyncio.Semaphore)


# =============================================================================
# Metadata Extraction Tests
# =============================================================================


class TestMetadataExtraction:
    """Tests for _extract_metadata method."""

    @pytest.mark.unit
    def test_extracts_title(self, browser_tool, soup):
        """Verify title is extracted."""
        metadata = browser_tool._extract_metadata(soup)
        assert metadata.get("title") == "Test Page Title"

    @pytest.mark.unit
    def test_extracts_description(self, browser_tool, soup):
        """Verify description is extracted."""
        metadata = browser_tool._extract_metadata(soup)
        assert metadata.get("description") == "This is a test description"

    @pytest.mark.unit
    def test_extracts_keywords(self, browser_tool, soup):
        """Verify keywords are extracted."""
        metadata = browser_tool._extract_metadata(soup)
        assert metadata.get("keywords") == "test, keywords, sample"

    @pytest.mark.unit
    def test_extracts_author(self, browser_tool, soup):
        """Verify author is extracted."""
        metadata = browser_tool._extract_metadata(soup)
        assert metadata.get("author") == "Test Author"

    @pytest.mark.unit
    def test_extracts_published_date(self, browser_tool, soup):
        """Verify published date is extracted."""
        metadata = browser_tool._extract_metadata(soup)
        assert metadata.get("published") == "2024-01-15"

    @pytest.mark.unit
    def test_handles_missing_metadata(self, browser_tool):
        """Verify missing metadata fields are handled."""
        html = "<html><body><p>No metadata</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        metadata = browser_tool._extract_metadata(soup)

        assert "title" not in metadata
        assert "description" not in metadata


# =============================================================================
# Source Type Classification Tests
# =============================================================================


class TestSourceTypeClassification:
    """Tests for classify_source_type method."""

    @pytest.mark.unit
    @pytest.mark.parametrize("url,expected", [
        ("https://statista.com/report", "industry_report"),
        ("https://euromonitor.com/data", "industry_report"),
        ("https://ibisworld.com/industry", "industry_report"),
    ])
    def test_classifies_industry_reports(self, browser_tool, url, expected):
        """Verify industry report URLs are classified correctly."""
        result = browser_tool.classify_source_type(url, "content")
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("url,expected", [
        ("https://news.example.com/article", "news_article"),
        ("https://example.com/press-release", "news_article"),
        ("https://blog.example.com/post", "news_article"),
    ])
    def test_classifies_news_articles(self, browser_tool, url, expected):
        """Verify news article URLs are classified correctly."""
        result = browser_tool.classify_source_type(url, "content")
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("url,expected", [
        ("https://journal.example.com/study", "academic"),
        ("https://research.example.com/paper", "academic"),
        ("https://academic.example.com/article", "academic"),
    ])
    def test_classifies_academic_sources(self, browser_tool, url, expected):
        """Verify academic URLs are classified correctly."""
        result = browser_tool.classify_source_type(url, "content")
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("url,expected", [
        ("https://twitter.com/company", "social_media"),
        ("https://linkedin.com/company/test", "social_media"),
        ("https://facebook.com/testpage", "social_media"),
    ])
    def test_classifies_social_media(self, browser_tool, url, expected):
        """Verify social media URLs are classified correctly."""
        result = browser_tool.classify_source_type(url, "content")
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("url,expected", [
        ("https://example.gov/data", "government"),
        ("https://example.gob.mx/info", "government"),
    ])
    def test_classifies_government_sources(self, browser_tool, url, expected):
        """Verify government URLs are classified correctly."""
        result = browser_tool.classify_source_type(url, "content")
        assert result == expected

    @pytest.mark.unit
    def test_classifies_market_data_by_content(self, browser_tool):
        """Verify market data is classified by content."""
        content = "The market size grew by 15% with revenue of $1B"
        result = browser_tool.classify_source_type("https://example.com", content)
        assert result == "market_data"

    @pytest.mark.unit
    def test_defaults_to_web(self, browser_tool):
        """Verify unknown sources default to 'web'."""
        result = browser_tool.classify_source_type(
            "https://example.com/page",
            "Generic content without markers"
        )
        assert result == "web"


# =============================================================================
# URL Validation Tests
# =============================================================================


class TestURLValidation:
    """Tests for URL validation in fetch operations."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_validates_url_before_fetch(self, browser_tool):
        """Verify URL is validated before fetching."""
        with patch("src.tools.browser.URLValidator.validate_url") as mock_validate:
            mock_validate.side_effect = Exception("Invalid URL")

            # Mock browser to avoid actual network call
            browser_tool.browser = MagicMock()

            result = await browser_tool._fetch_page_internal("http://invalid")

            mock_validate.assert_called_once_with("http://invalid")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_error_for_invalid_url(self, browser_tool):
        """Verify error response for invalid URLs."""
        from src.core.validation.url_validator import URLValidationError

        with patch("src.tools.browser.URLValidator.validate_url") as mock_validate:
            mock_validate.side_effect = URLValidationError("Blocked URL")

            result = await browser_tool._fetch_page_internal("http://localhost")

            assert result.source_type == "error"
            assert "security" in result.content.lower() or "blocked" in result.content.lower()


# =============================================================================
# Concurrent Fetching Tests
# =============================================================================


class TestConcurrentFetching:
    """Tests for concurrent URL fetching."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fetch_multiple_uses_semaphore(self, browser_tool):
        """Verify fetch_multiple respects concurrency limit."""
        concurrent_count = 0
        max_concurrent = 0

        async def mock_fetch(url):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return ResearchSource(
                url=url,
                title="Test",
                content="Content",
                source_type="web",
                category="test",
            )

        browser_tool.fetch_page = mock_fetch

        urls = [f"https://example.com/{i}" for i in range(10)]
        await browser_tool.fetch_multiple(urls)

        assert max_concurrent <= browser_tool.max_concurrent

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fetch_multiple_handles_exceptions(self, browser_tool):
        """Verify fetch_multiple handles exceptions gracefully."""
        call_count = 0

        async def mock_fetch(url):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Network error")
            return ResearchSource(
                url=url,
                title="Test",
                content="Content",
                source_type="web",
                category="test",
            )

        browser_tool.fetch_page = mock_fetch

        urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
        results = await browser_tool.fetch_multiple(urls)

        # Should have 2 successful results (1 and 3)
        assert len(results) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fetch_multiple_filters_errors(self, browser_tool):
        """Verify error responses are filtered out."""
        async def mock_fetch(url):
            if "error" in url:
                return ResearchSource(
                    url=url,
                    title="Error",
                    content="Error occurred",
                    source_type="error",
                    category="error",
                )
            return ResearchSource(
                url=url,
                title="Success",
                content="Content",
                source_type="web",
                category="test",
            )

        browser_tool.fetch_page = mock_fetch

        urls = ["https://example.com/good", "https://example.com/error", "https://example.com/ok"]
        results = await browser_tool.fetch_multiple(urls)

        # Error response should be filtered
        assert len(results) == 2
        assert all(r.source_type != "error" for r in results)


# =============================================================================
# Timeout Tests
# =============================================================================


class TestTimeoutHandling:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fetch_page_has_overall_timeout(self, browser_tool):
        """Verify fetch_page has overall timeout."""
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(100)  # Very slow
            return ResearchSource(
                url="test",
                title="Test",
                content="Content",
                source_type="web",
                category="test",
            )

        browser_tool._fetch_page_internal = slow_fetch

        with patch("src.tools.browser.FETCH_OVERALL_TIMEOUT", 0.1):
            result = await browser_tool.fetch_page("https://example.com")

            assert result.source_type == "error"
            assert "timeout" in result.content.lower()


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_context_manager_starts_browser(self):
        """Verify context manager starts browser."""
        tool = BrowserTool()

        with patch.object(tool, 'start', new_callable=AsyncMock) as mock_start:
            with patch.object(tool, 'stop', new_callable=AsyncMock):
                async with tool:
                    mock_start.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_context_manager_stops_browser(self):
        """Verify context manager stops browser on exit."""
        tool = BrowserTool()

        with patch.object(tool, 'start', new_callable=AsyncMock):
            with patch.object(tool, 'stop', new_callable=AsyncMock) as mock_stop:
                async with tool:
                    pass

                mock_stop.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_context_manager_stops_on_exception(self):
        """Verify context manager stops browser even on exception."""
        tool = BrowserTool()

        with patch.object(tool, 'start', new_callable=AsyncMock):
            with patch.object(tool, 'stop', new_callable=AsyncMock) as mock_stop:
                try:
                    async with tool:
                        raise ValueError("Test error")
                except ValueError:
                    pass

                mock_stop.assert_called_once()


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.unit
    def test_classify_source_type_case_insensitive(self, browser_tool):
        """Verify classification is case-insensitive."""
        result = browser_tool.classify_source_type(
            "https://NEWS.EXAMPLE.COM/article",
            "content"
        )
        assert result == "news_article"

    @pytest.mark.unit
    def test_extract_metadata_empty_html(self, browser_tool):
        """Verify metadata extraction handles empty HTML."""
        soup = BeautifulSoup("", "html.parser")
        metadata = browser_tool._extract_metadata(soup)
        assert metadata == {}

    @pytest.mark.unit
    def test_classify_handles_empty_strings(self, browser_tool):
        """Verify classification handles empty strings."""
        result = browser_tool.classify_source_type("", "")
        assert result == "web"
