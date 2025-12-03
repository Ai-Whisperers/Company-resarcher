"""
Unit tests for GitHubTool.

Tests the GitHub API tool functionality including:
- Organization lookup and search
- Repository fetching
- Tech stack analysis
- Activity metrics
- Error handling
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.github_tool import (
    GitHubTool,
    GitHubOrg,
    Repository,
    TechStackAnalysis,
    RecentActivity,
    GitHubPresence,
    get_shared_github_tool,
    reset_github_tool,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx AsyncClient."""
    mock_client = AsyncMock()
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def github_tool_with_token():
    """Create a GitHubTool with a mock token."""
    with patch("src.tools.github_tool.get_settings") as mock_settings:
        settings_instance = MagicMock()
        settings_instance.GITHUB_API_TOKEN = MagicMock()
        settings_instance.GITHUB_API_TOKEN.get_secret_value.return_value = "ghp_test_token"
        mock_settings.return_value = settings_instance
        tool = GitHubTool()
        return tool


@pytest.fixture
def github_tool_no_token():
    """Create a GitHubTool without a token."""
    with patch("src.tools.github_tool.get_settings") as mock_settings:
        settings_instance = MagicMock()
        settings_instance.GITHUB_API_TOKEN = None
        mock_settings.return_value = settings_instance
        tool = GitHubTool()
        return tool


@pytest.fixture
def sample_org_response():
    """Sample GitHub organization API response."""
    return {
        "login": "microsoft",
        "name": "Microsoft",
        "description": "Open source, from Microsoft with love",
        "public_repos": 5000,
        "followers": 50000,
        "created_at": "2013-12-10T19:06:48Z",
        "blog": "https://opensource.microsoft.com",
        "location": "Redmond, WA",
        "avatar_url": "https://avatars.githubusercontent.com/u/6154722?v=4",
        "html_url": "https://github.com/microsoft",
    }


@pytest.fixture
def sample_repos_response():
    """Sample GitHub repositories API response."""
    now = datetime.now(timezone.utc)
    return [
        {
            "name": "vscode",
            "full_name": "microsoft/vscode",
            "description": "Visual Studio Code",
            "language": "TypeScript",
            "stargazers_count": 150000,
            "forks_count": 25000,
            "open_issues_count": 5000,
            "created_at": "2015-09-03T20:00:00Z",
            "updated_at": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
            "topics": ["editor", "typescript", "electron"],
            "fork": False,
            "html_url": "https://github.com/microsoft/vscode",
            "license": {"name": "MIT License"},
            "size": 500000,
        },
        {
            "name": "TypeScript",
            "full_name": "microsoft/TypeScript",
            "description": "TypeScript is a superset of JavaScript",
            "language": "TypeScript",
            "stargazers_count": 90000,
            "forks_count": 12000,
            "open_issues_count": 6000,
            "created_at": "2014-06-17T15:30:00Z",
            "updated_at": (now - timedelta(days=5)).isoformat().replace("+00:00", "Z"),
            "topics": ["typescript", "javascript", "compiler"],
            "fork": False,
            "html_url": "https://github.com/microsoft/TypeScript",
            "license": {"name": "Apache License 2.0"},
            "size": 300000,
        },
        {
            "name": "react-native-windows",
            "full_name": "microsoft/react-native-windows",
            "description": "React Native for Windows",
            "language": "C++",
            "stargazers_count": 15000,
            "forks_count": 1000,
            "open_issues_count": 500,
            "created_at": "2016-02-01T10:00:00Z",
            "updated_at": (now - timedelta(days=200)).isoformat().replace("+00:00", "Z"),
            "topics": ["react", "windows"],
            "fork": False,
            "html_url": "https://github.com/microsoft/react-native-windows",
            "license": {"name": "MIT License"},
            "size": 200000,
        },
    ]


@pytest.fixture
def sample_search_response():
    """Sample GitHub search API response."""
    return {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "login": "microsoft",
                "id": 6154722,
                "type": "Organization",
            }
        ],
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestGitHubToolInitialization:
    """Tests for GitHubTool initialization."""

    @pytest.mark.unit
    def test_initializes_with_token_from_settings(self, github_tool_with_token):
        """Verify GitHubTool initializes with token from settings."""
        assert github_tool_with_token.token == "ghp_test_token"
        assert github_tool_with_token.is_available() is True

    @pytest.mark.unit
    def test_initializes_without_token(self, github_tool_no_token):
        """Verify GitHubTool initializes without token."""
        assert github_tool_no_token.token is None
        assert github_tool_no_token.is_available() is False

    @pytest.mark.unit
    def test_direct_token_overrides_settings(self):
        """Verify direct token parameter overrides settings."""
        with patch("src.tools.github_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.GITHUB_API_TOKEN = MagicMock()
            settings_instance.GITHUB_API_TOKEN.get_secret_value.return_value = "settings_token"
            mock_settings.return_value = settings_instance

            tool = GitHubTool(token="direct_token")
            assert tool.token == "direct_token"


# =============================================================================
# Organization Lookup Tests
# =============================================================================


class TestOrganizationLookup:
    """Tests for organization lookup methods."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_organization_success(
        self, github_tool_with_token, mock_httpx_client, sample_org_response
    ):
        """Verify successful organization lookup."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_org_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        org = await github_tool_with_token._get_organization("microsoft")

        assert org is not None
        assert org.login == "microsoft"
        assert org.name == "Microsoft"
        assert org.public_repos == 5000
        assert org.followers == 50000

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_organization_not_found(self, github_tool_with_token, mock_httpx_client):
        """Verify 404 response returns None."""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        org = await github_tool_with_token._get_organization("nonexistent-org")

        assert org is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_organization_rate_limited(self, github_tool_with_token, mock_httpx_client):
        """Verify 403 rate limit response returns None."""
        mock_response = AsyncMock()
        mock_response.status_code = 403
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        org = await github_tool_with_token._get_organization("microsoft")

        assert org is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_organization_direct_lookup(
        self, github_tool_with_token, mock_httpx_client, sample_org_response
    ):
        """Verify find_organization tries direct lookup first."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_org_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        org = await github_tool_with_token.find_organization("Microsoft")

        assert org is not None
        assert org.login == "microsoft"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_find_organization_search_fallback(
        self, github_tool_with_token, mock_httpx_client, sample_org_response, sample_search_response
    ):
        """Verify find_organization falls back to search."""
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = AsyncMock()

            # First calls are direct lookups (should fail)
            if call_count <= 4:  # 4 normalized name variations
                mock_response.status_code = 404
            elif "search/users" in args[0]:
                # Search call
                mock_response.status_code = 200
                mock_response.json.return_value = sample_search_response
            else:
                # Follow-up org lookup from search result
                mock_response.status_code = 200
                mock_response.json.return_value = sample_org_response

            return mock_response

        mock_httpx_client.get.side_effect = mock_get
        github_tool_with_token._client = mock_httpx_client

        org = await github_tool_with_token.find_organization("Obscure Company Name")

        assert org is not None


# =============================================================================
# Repository Fetching Tests
# =============================================================================


class TestRepositoryFetching:
    """Tests for repository fetching."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_repos_success(
        self, github_tool_with_token, mock_httpx_client, sample_repos_response
    ):
        """Verify successful repository fetching."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_repos_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        repos = await github_tool_with_token.get_organization_repos("microsoft", limit=10)

        assert len(repos) == 3
        assert repos[0].name == "vscode"
        assert repos[0].language == "TypeScript"
        assert repos[0].stars == 150000

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_repos_respects_limit(
        self, github_tool_with_token, mock_httpx_client, sample_repos_response
    ):
        """Verify limit parameter is respected."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_repos_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        repos = await github_tool_with_token.get_organization_repos("microsoft", limit=2)

        assert len(repos) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_repos_handles_error(self, github_tool_with_token, mock_httpx_client):
        """Verify error handling in repository fetching."""
        mock_httpx_client.get.side_effect = Exception("Network error")
        github_tool_with_token._client = mock_httpx_client

        repos = await github_tool_with_token.get_organization_repos("microsoft")

        assert repos == []


# =============================================================================
# Tech Stack Analysis Tests
# =============================================================================


class TestTechStackAnalysis:
    """Tests for tech stack analysis."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_tech_stack(
        self, github_tool_with_token, mock_httpx_client, sample_repos_response
    ):
        """Verify tech stack analysis."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_repos_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        analysis = await github_tool_with_token.analyze_tech_stack("microsoft")

        assert "TypeScript" in analysis.primary_languages
        assert analysis.primary_languages["TypeScript"] == 2
        assert "C++" in analysis.primary_languages
        assert analysis.total_repos == 3
        assert analysis.total_stars == 255000  # 150000 + 90000 + 15000

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_tech_stack_detects_frameworks(
        self, github_tool_with_token, mock_httpx_client, sample_repos_response
    ):
        """Verify framework detection from topics."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_repos_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        analysis = await github_tool_with_token.analyze_tech_stack("microsoft")

        # "react" should be detected from react-native-windows topics
        assert "react" in analysis.frameworks

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_tech_stack_counts_active_repos(
        self, github_tool_with_token, mock_httpx_client, sample_repos_response
    ):
        """Verify active repo counting (updated in last 6 months)."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_repos_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        analysis = await github_tool_with_token.analyze_tech_stack("microsoft")

        # Two repos were updated recently, one is old
        assert analysis.active_repos == 2


# =============================================================================
# Activity Analysis Tests
# =============================================================================


class TestActivityAnalysis:
    """Tests for activity analysis."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_recent_activity(
        self, github_tool_with_token, mock_httpx_client, sample_repos_response
    ):
        """Verify recent activity analysis."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_repos_response
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        activity = await github_tool_with_token.get_recent_activity("microsoft", days=30)

        assert activity.period_days == 30
        assert activity.repos_updated == 2
        assert "vscode" in activity.most_active


# =============================================================================
# GitHub Presence Tests
# =============================================================================


class TestGitHubPresence:
    """Tests for complete GitHub presence analysis."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_github_presence_success(
        self,
        github_tool_with_token,
        mock_httpx_client,
        sample_org_response,
        sample_repos_response,
    ):
        """Verify complete GitHub presence analysis."""
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = AsyncMock()
            mock_response.status_code = 200

            if "orgs/microsoft/repos" in args[0]:
                mock_response.json.return_value = sample_repos_response
            else:
                mock_response.json.return_value = sample_org_response

            return mock_response

        mock_httpx_client.get.side_effect = mock_get
        github_tool_with_token._client = mock_httpx_client

        presence = await github_tool_with_token.get_github_presence("Microsoft")

        assert presence.found is True
        assert presence.org is not None
        assert presence.org.login == "microsoft"
        assert presence.tech_stack is not None
        assert presence.activity is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_github_presence_not_found(self, github_tool_with_token, mock_httpx_client):
        """Verify GitHub presence when org not found."""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_httpx_client.get.return_value = mock_response

        github_tool_with_token._client = mock_httpx_client

        presence = await github_tool_with_token.get_github_presence("Nonexistent Company")

        assert presence.found is False
        assert presence.org is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_github_presence_no_token(self, github_tool_no_token):
        """Verify GitHub presence when no token configured."""
        presence = await github_tool_no_token.get_github_presence("Microsoft")

        assert presence.found is False
        assert presence.error == "API token not configured"


# =============================================================================
# Formatting Tests
# =============================================================================


class TestFormatting:
    """Tests for output formatting."""

    @pytest.mark.unit
    def test_format_for_research_success(self, github_tool_with_token):
        """Verify markdown formatting for successful presence."""
        presence = GitHubPresence(
            found=True,
            org=GitHubOrg(
                name="Microsoft",
                login="microsoft",
                description="Open source projects",
                public_repos=5000,
                followers=50000,
                location="Redmond, WA",
                blog="https://opensource.microsoft.com",
                html_url="https://github.com/microsoft",
            ),
            tech_stack=TechStackAnalysis(
                primary_languages={"TypeScript": 100, "Python": 50},
                frameworks=["react", "docker"],
                topics={"typescript": 80, "python": 40},
                total_repos=500,
                total_stars=1000000,
                active_repos=400,
            ),
            activity=RecentActivity(
                repos_updated=50,
                repos_created=5,
                most_active=["vscode", "TypeScript"],
                period_days=30,
            ),
        )

        markdown = github_tool_with_token.format_for_research(presence)

        assert "## GitHub Presence: Microsoft" in markdown
        assert "microsoft" in markdown
        assert "TypeScript" in markdown
        assert "1,000,000" in markdown  # formatted stars
        assert "vscode" in markdown

    @pytest.mark.unit
    def test_format_for_research_not_found(self, github_tool_with_token):
        """Verify markdown formatting when org not found."""
        presence = GitHubPresence(found=False)

        markdown = github_tool_with_token.format_for_research(presence)

        assert "No GitHub organization found" in markdown

    @pytest.mark.unit
    def test_format_for_research_error(self, github_tool_with_token):
        """Verify markdown formatting for error case."""
        presence = GitHubPresence(found=False, error="Rate limit exceeded")

        markdown = github_tool_with_token.format_for_research(presence)

        assert "Error: Rate limit exceeded" in markdown


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for singleton pattern."""

    @pytest.mark.unit
    def test_shared_instance_created(self):
        """Verify shared instance is created."""
        reset_github_tool()

        with patch("src.tools.github_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.GITHUB_API_TOKEN = None
            mock_settings.return_value = settings_instance

            tool1 = get_shared_github_tool()
            tool2 = get_shared_github_tool()

            assert tool1 is tool2

    @pytest.mark.unit
    def test_reset_clears_instance(self):
        """Verify reset clears the singleton instance."""
        with patch("src.tools.github_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.GITHUB_API_TOKEN = None
            mock_settings.return_value = settings_instance

            tool1 = get_shared_github_tool()
            reset_github_tool()
            tool2 = get_shared_github_tool()

            assert tool1 is not tool2


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.unit
    def test_normalized_names_generation(self, github_tool_with_token):
        """Verify normalized name generation."""
        names = github_tool_with_token._get_normalized_names("Acme Corp Inc.")

        assert "acmecorpinc" in names
        assert "acme-corp-inc." in names
        assert "acmecorp" in names  # With suffix removed

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_network_error(self, github_tool_with_token, mock_httpx_client):
        """Verify network errors are handled gracefully."""
        mock_httpx_client.get.side_effect = Exception("Connection refused")
        github_tool_with_token._client = mock_httpx_client

        org = await github_tool_with_token._get_organization("microsoft")

        assert org is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_close_client(self, github_tool_with_token, mock_httpx_client):
        """Verify client is closed properly."""
        github_tool_with_token._client = mock_httpx_client

        await github_tool_with_token.close()

        mock_httpx_client.aclose.assert_called_once()
        assert github_tool_with_token._client is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_rate_limit_check(self, github_tool_with_token, mock_httpx_client):
        """Verify rate limit checking."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rate": {
                "limit": 5000,
                "remaining": 4500,
                "reset": 1234567890,
                "used": 500,
            }
        }
        mock_httpx_client.get.return_value = mock_response
        github_tool_with_token._client = mock_httpx_client

        rate_info = await github_tool_with_token.check_rate_limit()

        assert rate_info["limit"] == 5000
        assert rate_info["remaining"] == 4500
