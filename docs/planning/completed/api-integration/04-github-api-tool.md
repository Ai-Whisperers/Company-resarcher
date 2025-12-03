# Task: Build GitHub API Tool for Tech Stack Analysis

## Priority: 2 (High Value)
## Effort: Medium (New Implementation)
## Impact: +10% research quality (tech companies)
## Status: IMPLEMENTED

---

## Current State

### What Exists
- **API Key**: `GITHUB_API_TOKEN` in `.env` (documented in `.env.example`)
- **Status**: FULLY IMPLEMENTED

### Implementation Complete
- [x] `src/tools/github_tool.py` - Full GitHubTool class with:
  - Organization lookup (direct + search fallback)
  - Repository fetching with pagination
  - Tech stack analysis (languages, frameworks, topics)
  - Activity metrics (recent updates, most active repos)
  - Formatted markdown output for research reports
- [x] `src/core/config.py` - GITHUB_API_TOKEN setting added
- [x] `src/pipeline/orchestrator.py` - `research_github_presence()` method
- [x] `src/tools/__init__.py` - Singleton pattern integration
- [x] `tests/unit/test_github_tool.py` - Comprehensive unit tests

---

## Why This Matters

### Use Cases
1. **Tech Stack Discovery**: What languages, frameworks does the company use?
2. **Engineering Team Size**: How many developers? How active?
3. **Open Source Activity**: Do they contribute? What projects?
4. **Technical Maturity**: Code quality indicators, CI/CD adoption
5. **Hiring Signals**: Recent activity spikes = growth

### Value for Research
- Competitive technical analysis
- Technology due diligence
- Engineering culture assessment
- Technical debt indicators

---

## Implementation Plan

### Step 1: Create GitHub Tool
**File**: `src/tools/github_tool.py`

```python
"""
GitHub API Tool for company tech stack and engineering analysis.

Uses GitHub REST API v3 and GraphQL API v4.
https://docs.github.com/en/rest
"""

import os
import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.logger import setup_logger
from ..core.config import get_settings

logger = setup_logger("tools.github")


@dataclass
class GitHubOrg:
    """GitHub organization data."""
    name: str
    login: str
    description: Optional[str]
    public_repos: int
    followers: int
    created_at: datetime
    blog: Optional[str]
    location: Optional[str]


@dataclass
class Repository:
    """Repository data."""
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    open_issues: int
    created_at: datetime
    updated_at: datetime
    topics: List[str]
    is_fork: bool


@dataclass
class TechStackAnalysis:
    """Tech stack analysis results."""
    primary_languages: Dict[str, int]  # language -> repo count
    frameworks: List[str]
    topics: Dict[str, int]  # topic -> count
    total_repos: int
    total_stars: int
    active_repos: int  # updated in last 6 months
    contributors_estimate: int


class GitHubTool:
    """Tool for analyzing company GitHub presence."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self._token = token
        self.settings = get_settings()

    @property
    def token(self) -> Optional[str]:
        if self._token:
            return self._token
        token = getattr(self.settings, "GITHUB_API_TOKEN", None)
        if token:
            return token.get_secret_value() if hasattr(token, "get_secret_value") else token
        return None

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CompanyResearcher/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def find_organization(self, company_name: str) -> Optional[GitHubOrg]:
        """
        Find GitHub organization for a company.

        Tries multiple strategies:
        1. Direct org name lookup
        2. Search by company name
        3. Search by domain
        """
        # Strategy 1: Direct lookup (lowercase, no spaces)
        org_name = company_name.lower().replace(" ", "").replace("-", "")
        org = await self._get_organization(org_name)
        if org:
            return org

        # Strategy 2: Search organizations
        search_results = await self._search_organizations(company_name)
        if search_results:
            return search_results[0]

        return None

    async def _get_organization(self, org_name: str) -> Optional[GitHubOrg]:
        """Get organization by exact name."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/orgs/{org_name}",
                headers=self._headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_org(data)
                return None

    async def _search_organizations(self, query: str) -> List[GitHubOrg]:
        """Search for organizations."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/search/users",
                params={"q": f"{query} type:org", "per_page": 5},
                headers=self._headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    orgs = []
                    for item in data.get("items", []):
                        org = await self._get_organization(item["login"])
                        if org:
                            orgs.append(org)
                    return orgs
                return []

    async def get_organization_repos(
        self,
        org_name: str,
        limit: int = 100
    ) -> List[Repository]:
        """Get all public repositories for an organization."""
        repos = []
        page = 1

        async with aiohttp.ClientSession() as session:
            while len(repos) < limit:
                async with session.get(
                    f"{self.BASE_URL}/orgs/{org_name}/repos",
                    params={"per_page": 100, "page": page, "sort": "updated"},
                    headers=self._headers()
                ) as response:
                    if response.status != 200:
                        break
                    data = await response.json()
                    if not data:
                        break
                    repos.extend([self._parse_repo(r) for r in data])
                    page += 1

        return repos[:limit]

    async def analyze_tech_stack(self, org_name: str) -> TechStackAnalysis:
        """Analyze technology stack for an organization."""
        repos = await self.get_organization_repos(org_name)

        languages = {}
        topics = {}
        total_stars = 0
        active_count = 0
        six_months_ago = datetime.now() - timedelta(days=180)

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
            if repo.updated_at > six_months_ago:
                active_count += 1

        # Infer frameworks from topics
        framework_indicators = {
            "react", "angular", "vue", "django", "flask", "rails",
            "spring", "express", "fastapi", "nextjs", "kubernetes",
            "docker", "terraform", "aws", "gcp", "azure"
        }
        frameworks = [t for t in topics.keys() if t.lower() in framework_indicators]

        return TechStackAnalysis(
            primary_languages=dict(sorted(languages.items(), key=lambda x: -x[1])[:10]),
            frameworks=frameworks,
            topics=dict(sorted(topics.items(), key=lambda x: -x[1])[:20]),
            total_repos=len([r for r in repos if not r.is_fork]),
            total_stars=total_stars,
            active_repos=active_count,
            contributors_estimate=0,  # Would need additional API calls
        )

    async def get_recent_activity(
        self,
        org_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get recent activity summary."""
        repos = await self.get_organization_repos(org_name, limit=50)
        cutoff = datetime.now() - timedelta(days=days)

        recently_updated = [r for r in repos if r.updated_at > cutoff]
        recently_created = [r for r in repos if r.created_at > cutoff]

        return {
            "repos_updated": len(recently_updated),
            "repos_created": len(recently_created),
            "most_active": [r.name for r in sorted(
                recently_updated,
                key=lambda x: x.updated_at,
                reverse=True
            )[:5]],
        }

    def _parse_org(self, data: dict) -> GitHubOrg:
        return GitHubOrg(
            name=data.get("name") or data["login"],
            login=data["login"],
            description=data.get("description"),
            public_repos=data.get("public_repos", 0),
            followers=data.get("followers", 0),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            blog=data.get("blog"),
            location=data.get("location"),
        )

    def _parse_repo(self, data: dict) -> Repository:
        return Repository(
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description"),
            language=data.get("language"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            open_issues=data.get("open_issues_count", 0),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            topics=data.get("topics", []),
            is_fork=data.get("fork", False),
        )

    def is_available(self) -> bool:
        """Check if GitHub API is available."""
        return bool(self.token)
```

### Step 2: Add Configuration
**File**: `src/core/config.py`

```python
# Add to Settings class
GITHUB_API_TOKEN: Optional[SecretStr] = None
```

### Step 3: Create Pipeline Integration
**File**: `src/pipeline/comprehensive_research.py`

```python
async def _research_github_presence(
    self,
    company_name: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Analyze company's GitHub presence."""
    from src.tools.github_tool import GitHubTool

    github = GitHubTool()
    if not github.is_available():
        self.logger.warning("GitHub API not configured")
        return {"skipped": True}

    # Find organization
    org = await github.find_organization(company_name)
    if not org:
        self.logger.info(f"No GitHub organization found for {company_name}")
        return {"found": False}

    # Analyze tech stack
    tech_stack = await github.analyze_tech_stack(org.login)

    # Get recent activity
    activity = await github.get_recent_activity(org.login)

    # Generate report
    await self._write_github_report(output_dir, org, tech_stack, activity)

    return {
        "found": True,
        "org": org.login,
        "repos": tech_stack.total_repos,
        "languages": list(tech_stack.primary_languages.keys())[:5],
    }
```

### Step 4: Add Output Templates

```markdown
# GitHub Presence Analysis

## Organization: {{ org.name }}
- **GitHub**: [{{ org.login }}](https://github.com/{{ org.login }})
- **Public Repos**: {{ org.public_repos }}
- **Followers**: {{ org.followers }}
- **Location**: {{ org.location or "Not specified" }}

## Technology Stack

### Primary Languages
{% for lang, count in tech_stack.primary_languages.items() %}
- {{ lang }}: {{ count }} repositories
{% endfor %}

### Frameworks & Tools
{% for framework in tech_stack.frameworks %}
- {{ framework }}
{% endfor %}

## Activity Metrics
- **Total Repositories**: {{ tech_stack.total_repos }}
- **Active Repos (6 months)**: {{ tech_stack.active_repos }}
- **Total Stars**: {{ tech_stack.total_stars }}

## Recent Activity (30 days)
- Repos Updated: {{ activity.repos_updated }}
- Repos Created: {{ activity.repos_created }}

### Most Active Projects
{% for repo in activity.most_active %}
- {{ repo }}
{% endfor %}
```

---

## Output Structure

```
outputs/Company_Name/
├── tech_intelligence/
│   ├── 01-GitHub-Presence.md     # Org overview
│   ├── 02-Tech-Stack.md          # Languages, frameworks
│   └── 03-Engineering-Activity.md # Recent commits, activity
```

---

## API Limits (GitHub)

### With Token (Configured)
- **5,000 requests/hour**
- GraphQL: 5,000 points/hour

### Per Company Analysis
- 1 request: Organization lookup
- 1-3 requests: Repository list (paginated)
- ~5 requests total per company

### Rate Limit Strategy
```python
# Check remaining quota
async def check_rate_limit(self):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{self.BASE_URL}/rate_limit",
            headers=self._headers()
        ) as response:
            data = await response.json()
            return data["rate"]["remaining"]
```

---

## Testing Checklist

- [ ] GitHubTool class imports correctly
- [ ] Token loads from environment
- [ ] find_organization works for "microsoft"
- [ ] get_organization_repos returns results
- [ ] analyze_tech_stack produces valid output
- [ ] Handles non-existent orgs gracefully
- [ ] Rate limiting respected

---

## Example Companies to Test

| Company | Expected GitHub Org |
|---------|-------------------|
| Microsoft | `microsoft` |
| Google | `google` |
| Meta | `facebook` |
| América Móvil | `americamovil` (may not exist) |
| Telecom Argentina | Unknown |

---

## Related Files

- `src/tools/github_tool.py` - New tool to create
- `src/pipeline/comprehensive_research.py` - Integration point
- `.env` - GITHUB_API_TOKEN configuration
