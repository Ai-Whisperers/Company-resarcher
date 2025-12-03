"""
GitHub API Tool for company tech stack and engineering analysis.

INT-004: Provides GitHub organization analysis, tech stack detection,
and engineering activity metrics.

Uses GitHub REST API v3.
https://docs.github.com/en/rest
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class GitHubOrg:
    """GitHub organization data."""

    name: str
    login: str
    description: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    created_at: Optional[datetime] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None


@dataclass
class Repository:
    """Repository data."""

    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    topics: List[str] = field(default_factory=list)
    is_fork: bool = False
    html_url: Optional[str] = None
    license: Optional[str] = None
    size: int = 0


@dataclass
class TechStackAnalysis:
    """Tech stack analysis results."""

    primary_languages: Dict[str, int] = field(default_factory=dict)  # language -> repo count
    frameworks: List[str] = field(default_factory=list)
    topics: Dict[str, int] = field(default_factory=dict)  # topic -> count
    total_repos: int = 0
    total_stars: int = 0
    active_repos: int = 0  # updated in last 6 months
    contributors_estimate: int = 0


@dataclass
class RecentActivity:
    """Recent activity summary."""

    repos_updated: int = 0
    repos_created: int = 0
    most_active: List[str] = field(default_factory=list)
    period_days: int = 30


@dataclass
class GitHubPresence:
    """Complete GitHub presence data for a company."""

    org: Optional[GitHubOrg] = None
    tech_stack: Optional[TechStackAnalysis] = None
    activity: Optional[RecentActivity] = None
    found: bool = False
    error: Optional[str] = None


class GitHubTool:
    """
    Tool for analyzing company GitHub presence.

    Provides tech stack discovery, engineering team size estimation,
    and open source activity analysis.

    Usage:
        tool = GitHubTool()
        org = await tool.find_organization("microsoft")
        tech_stack = await tool.analyze_tech_stack("microsoft")
        activity = await tool.get_recent_activity("microsoft")
    """

    BASE_URL = "https://api.github.com"

    # Known framework indicators in topics
    FRAMEWORK_INDICATORS = {
        "react",
        "angular",
        "vue",
        "svelte",
        "django",
        "flask",
        "rails",
        "spring",
        "express",
        "fastapi",
        "nextjs",
        "nuxt",
        "gatsby",
        "kubernetes",
        "docker",
        "terraform",
        "aws",
        "gcp",
        "azure",
        "graphql",
        "rest",
        "grpc",
        "redis",
        "postgresql",
        "mongodb",
        "elasticsearch",
        "kafka",
        "rabbitmq",
        "nodejs",
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "pandas",
    }

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub tool.

        Args:
            token: GitHub API token (or set GITHUB_API_TOKEN env var)
        """
        self._token = token
        self._client: Optional[httpx.AsyncClient] = None
        self._settings = get_settings()

    @property
    def token(self) -> Optional[str]:
        """Get GitHub API token from settings or constructor."""
        if self._token:
            return self._token
        token = getattr(self._settings, "GITHUB_API_TOKEN", None)
        if token:
            return token.get_secret_value() if hasattr(token, "get_secret_value") else token
        return None

    def is_available(self) -> bool:
        """Check if GitHub API is available (token configured)."""
        return bool(self.token)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not HAS_HTTPX:
            raise ImportError("httpx required. Install with: pip install httpx")

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def _headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CompanyResearcher/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def find_organization(self, company_name: str) -> Optional[GitHubOrg]:
        """
        Find GitHub organization for a company.

        Tries multiple strategies:
        1. Direct org name lookup (normalized)
        2. Search by company name

        Args:
            company_name: Company name to search for

        Returns:
            GitHubOrg if found, None otherwise
        """
        # Strategy 1: Direct lookup (lowercase, no spaces, common variations)
        normalized_names = self._get_normalized_names(company_name)

        for org_name in normalized_names:
            org = await self._get_organization(org_name)
            if org:
                logger.info(f"Found GitHub org '{org.login}' for '{company_name}'")
                return org

        # Strategy 2: Search organizations
        search_results = await self._search_organizations(company_name)
        if search_results:
            logger.info(f"Found GitHub org '{search_results[0].login}' via search for '{company_name}'")
            return search_results[0]

        logger.info(f"No GitHub organization found for '{company_name}'")
        return None

    def _get_normalized_names(self, company_name: str) -> List[str]:
        """Generate normalized org name variations to try."""
        # Base normalization
        base = company_name.lower().replace(" ", "").replace("-", "").replace(".", "")

        variations = [
            base,
            company_name.lower().replace(" ", "-"),
            company_name.lower().replace(" ", ""),
            company_name.lower().replace(" ", "_"),
        ]

        # Handle common suffixes
        for suffix in ["inc", "corp", "llc", "ltd", "sa", "srl"]:
            if base.endswith(suffix):
                variations.append(base[: -len(suffix)])

        # Remove duplicates while preserving order
        seen = set()
        return [v for v in variations if not (v in seen or seen.add(v))]

    async def _get_organization(self, org_name: str) -> Optional[GitHubOrg]:
        """Get organization by exact name."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/orgs/{org_name}",
                headers=self._headers(),
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_org(data)
            elif response.status_code == 404:
                return None
            elif response.status_code == 403:
                logger.warning("GitHub API rate limit exceeded")
                return None
            else:
                logger.debug(f"GitHub API returned {response.status_code} for org {org_name}")
                return None

        except Exception as e:
            logger.error(f"Error fetching GitHub org {org_name}: {e}")
            return None

    async def _search_organizations(self, query: str) -> List[GitHubOrg]:
        """Search for organizations by name."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/search/users",
                params={"q": f"{query} type:org", "per_page": 5},
                headers=self._headers(),
            )

            if response.status_code == 200:
                data = response.json()
                orgs = []
                for item in data.get("items", []):
                    org = await self._get_organization(item["login"])
                    if org:
                        orgs.append(org)
                return orgs
            return []

        except Exception as e:
            logger.error(f"Error searching GitHub organizations: {e}")
            return []

    async def get_organization_repos(
        self,
        org_name: str,
        limit: int = 100,
    ) -> List[Repository]:
        """
        Get all public repositories for an organization.

        Args:
            org_name: Organization login name
            limit: Maximum number of repos to fetch

        Returns:
            List of Repository objects
        """
        repos: List[Repository] = []
        page = 1

        try:
            client = await self._get_client()

            while len(repos) < limit:
                response = await client.get(
                    f"{self.BASE_URL}/orgs/{org_name}/repos",
                    params={"per_page": 100, "page": page, "sort": "updated"},
                    headers=self._headers(),
                )

                if response.status_code != 200:
                    if response.status_code == 403:
                        logger.warning("GitHub API rate limit exceeded")
                    break

                data = response.json()
                if not data:
                    break

                repos.extend([self._parse_repo(r) for r in data])
                page += 1

                # Stop if we got fewer than requested (last page)
                if len(data) < 100:
                    break

        except Exception as e:
            logger.error(f"Error fetching repos for {org_name}: {e}")

        return repos[:limit]

    async def analyze_tech_stack(self, org_name: str) -> TechStackAnalysis:
        """
        Analyze technology stack for an organization.

        Args:
            org_name: Organization login name

        Returns:
            TechStackAnalysis with language, framework, and topic stats
        """
        repos = await self.get_organization_repos(org_name)

        languages: Dict[str, int] = {}
        topics: Dict[str, int] = {}
        total_stars = 0
        active_count = 0
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)

        for repo in repos:
            if repo.is_fork:
                continue

            # Count languages
            if repo.language:
                languages[repo.language] = languages.get(repo.language, 0) + 1

            # Count topics
            for topic in repo.topics:
                topics[topic] = topics.get(topic, 0) + 1

            total_stars += repo.stars

            # Check if active
            if repo.updated_at and repo.updated_at > six_months_ago:
                active_count += 1

        # Infer frameworks from topics
        frameworks = [t for t in topics.keys() if t.lower() in self.FRAMEWORK_INDICATORS]

        # Sort languages and topics by count
        sorted_languages = dict(sorted(languages.items(), key=lambda x: -x[1])[:10])
        sorted_topics = dict(sorted(topics.items(), key=lambda x: -x[1])[:20])

        return TechStackAnalysis(
            primary_languages=sorted_languages,
            frameworks=sorted(frameworks),
            topics=sorted_topics,
            total_repos=len([r for r in repos if not r.is_fork]),
            total_stars=total_stars,
            active_repos=active_count,
            contributors_estimate=0,  # Would need additional API calls
        )

    async def get_recent_activity(
        self,
        org_name: str,
        days: int = 30,
    ) -> RecentActivity:
        """
        Get recent activity summary for an organization.

        Args:
            org_name: Organization login name
            days: Number of days to look back

        Returns:
            RecentActivity summary
        """
        repos = await self.get_organization_repos(org_name, limit=50)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        recently_updated = [r for r in repos if r.updated_at and r.updated_at > cutoff]
        recently_created = [r for r in repos if r.created_at and r.created_at > cutoff]

        # Get most active repos (sorted by update time)
        most_active = sorted(
            recently_updated,
            key=lambda x: x.updated_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        return RecentActivity(
            repos_updated=len(recently_updated),
            repos_created=len(recently_created),
            most_active=[r.name for r in most_active[:5]],
            period_days=days,
        )

    async def get_github_presence(self, company_name: str) -> GitHubPresence:
        """
        Get complete GitHub presence analysis for a company.

        This is a convenience method that combines find_organization,
        analyze_tech_stack, and get_recent_activity.

        Args:
            company_name: Company name to search for

        Returns:
            GitHubPresence with all analysis data
        """
        if not self.is_available():
            logger.warning("GitHub API token not configured")
            return GitHubPresence(found=False, error="API token not configured")

        try:
            # Find organization
            org = await self.find_organization(company_name)
            if not org:
                return GitHubPresence(found=False)

            # Analyze tech stack
            tech_stack = await self.analyze_tech_stack(org.login)

            # Get recent activity
            activity = await self.get_recent_activity(org.login)

            return GitHubPresence(
                org=org,
                tech_stack=tech_stack,
                activity=activity,
                found=True,
            )

        except Exception as e:
            logger.error(f"Error analyzing GitHub presence for {company_name}: {e}")
            return GitHubPresence(found=False, error=str(e))

    async def check_rate_limit(self) -> Dict[str, Any]:
        """
        Check GitHub API rate limit status.

        Returns:
            Dict with rate limit info (limit, remaining, reset time)
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/rate_limit",
                headers=self._headers(),
            )

            if response.status_code == 200:
                data = response.json()
                rate = data.get("rate", {})
                return {
                    "limit": rate.get("limit", 0),
                    "remaining": rate.get("remaining", 0),
                    "reset": rate.get("reset", 0),
                    "used": rate.get("used", 0),
                }
            return {"error": f"Status {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    def _parse_org(self, data: dict) -> GitHubOrg:
        """Parse organization data from API response."""
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return GitHubOrg(
            name=data.get("name") or data["login"],
            login=data["login"],
            description=data.get("description"),
            public_repos=data.get("public_repos", 0),
            followers=data.get("followers", 0),
            created_at=created_at,
            blog=data.get("blog"),
            location=data.get("location"),
            avatar_url=data.get("avatar_url"),
            html_url=data.get("html_url"),
        )

    def _parse_repo(self, data: dict) -> Repository:
        """Parse repository data from API response."""
        created_at = None
        updated_at = None

        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        license_name = None
        if data.get("license") and isinstance(data["license"], dict):
            license_name = data["license"].get("name")

        return Repository(
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description"),
            language=data.get("language"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            open_issues=data.get("open_issues_count", 0),
            created_at=created_at,
            updated_at=updated_at,
            topics=data.get("topics", []),
            is_fork=data.get("fork", False),
            html_url=data.get("html_url"),
            license=license_name,
            size=data.get("size", 0),
        )

    def format_for_research(self, presence: GitHubPresence) -> str:
        """
        Format GitHub presence data for research context.

        Args:
            presence: GitHubPresence data

        Returns:
            Formatted markdown string
        """
        if not presence.found:
            if presence.error:
                return f"## GitHub Presence\n\n*Error: {presence.error}*\n"
            return "## GitHub Presence\n\n*No GitHub organization found for this company.*\n"

        lines = []
        org = presence.org
        tech = presence.tech_stack
        activity = presence.activity

        # Organization info
        lines.append(f"## GitHub Presence: {org.name}\n")
        lines.append(f"- **Organization**: [{org.login}]({org.html_url})")
        lines.append(f"- **Public Repos**: {org.public_repos}")
        lines.append(f"- **Followers**: {org.followers}")

        if org.location:
            lines.append(f"- **Location**: {org.location}")
        if org.blog:
            lines.append(f"- **Website**: {org.blog}")
        if org.description:
            lines.append(f"- **Description**: {org.description}")

        # Tech stack
        if tech:
            lines.append("\n### Technology Stack\n")
            lines.append("**Primary Languages:**")
            for lang, count in list(tech.primary_languages.items())[:5]:
                lines.append(f"- {lang}: {count} repositories")

            if tech.frameworks:
                lines.append(f"\n**Frameworks & Tools**: {', '.join(tech.frameworks[:10])}")

            lines.append(f"\n**Repository Stats:**")
            lines.append(f"- Total Repos (non-fork): {tech.total_repos}")
            lines.append(f"- Active Repos (6 months): {tech.active_repos}")
            lines.append(f"- Total Stars: {tech.total_stars:,}")

        # Activity
        if activity:
            lines.append(f"\n### Recent Activity ({activity.period_days} days)\n")
            lines.append(f"- Repos Updated: {activity.repos_updated}")
            lines.append(f"- Repos Created: {activity.repos_created}")
            if activity.most_active:
                lines.append(f"- Most Active: {', '.join(activity.most_active)}")

        return "\n".join(lines)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance management
_github_tool_instance: Optional[GitHubTool] = None
_github_tool_lock = None

try:
    import threading

    _github_tool_lock = threading.Lock()
except ImportError:
    pass


def get_shared_github_tool() -> GitHubTool:
    """Get or create the shared GitHubTool instance (thread-safe)."""
    global _github_tool_instance
    if _github_tool_instance is None:
        if _github_tool_lock:
            with _github_tool_lock:
                if _github_tool_instance is None:
                    _github_tool_instance = GitHubTool()
        else:
            _github_tool_instance = GitHubTool()
    return _github_tool_instance


def reset_github_tool():
    """Reset the shared GitHubTool instance (useful for testing)."""
    global _github_tool_instance
    if _github_tool_lock:
        with _github_tool_lock:
            _github_tool_instance = None
    else:
        _github_tool_instance = None
