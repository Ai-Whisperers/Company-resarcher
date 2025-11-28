# Usage Examples

Practical code examples for common Company Researcher tasks.

## Contents

1. [CLI Usage](#cli-usage)
2. [REST API Client](#rest-api-client)
3. [Programmatic Usage](#programmatic-usage)
4. [Custom Agents](#custom-agents)
5. [Custom Tools](#custom-tools)

---

## CLI Usage

### Basic Research

```bash
# Research by company name
python main.py --name "Apple"

# With industry context
python main.py --name "Tesla" --industry "Automotive"

# With website URL (recommended for better results)
python main.py --name "Stripe" --url "https://stripe.com"
```

### Local Mode (Free)

```bash
# Uses DuckDuckGo + Ollama (no API keys needed)
python main.py --name "Microsoft" --local
```

### Output Location

Results are saved to `output/{company_name}/`:
```
output/Apple/
├── 00-Strategic-Context/
│   ├── Company-Overview.md
│   └── Key-People.md
├── 01-Market-Intelligence/
│   ├── Market-Size.md
│   └── Industry-Trends.md
├── ...
└── 99-Sources/
    ├── raw/
    └── Source-Log.md
```

---

## REST API Client

### Python Client

```python
"""
Complete Python client for Company Researcher API.
Save as: client.py
"""
import requests
import time
from typing import Optional, Dict, Any


class ResearchClient:
    """Client for Company Researcher REST API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health/detailed")
        response.raise_for_status()
        return response.json()

    def start_research(
        self,
        company_name: str,
        url: Optional[str] = None,
        industry: Optional[str] = None,
        country: str = "USA"
    ) -> str:
        """
        Start a research task.

        Returns:
            task_id: UUID for tracking the task
        """
        payload = {
            "company_name": company_name,
            "country": country
        }
        if url:
            payload["url"] = url
        if industry:
            payload["industry"] = industry

        response = self.session.post(
            f"{self.base_url}/api/v1/research",
            json=payload
        )
        response.raise_for_status()
        return response.json()["task_id"]

    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and results."""
        response = self.session.get(
            f"{self.base_url}/api/v1/research/{task_id}"
        )
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 10,
        timeout: int = 1800
    ) -> Dict[str, Any]:
        """
        Poll until task completes or fails.

        Args:
            task_id: Task UUID
            poll_interval: Seconds between polls
            timeout: Maximum wait time in seconds

        Returns:
            Final task status with results
        """
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timed out")

            status = self.get_status(task_id)

            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise Exception(f"Task failed: {status.get('error')}")

            print(f"Status: {status['status']}, waiting...")
            time.sleep(poll_interval)

    def research(
        self,
        company_name: str,
        url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Complete research workflow: start and wait for results.

        Returns:
            Research results
        """
        task_id = self.start_research(company_name, url, **kwargs)
        print(f"Started task: {task_id}")
        return self.wait_for_completion(task_id)


# Usage example
if __name__ == "__main__":
    client = ResearchClient()

    # Check health
    print("Health:", client.health_check())

    # Run research
    result = client.research(
        company_name="Notion",
        url="https://notion.so",
        industry="Productivity Software"
    )

    print(f"Research completed!")
    print(f"Status: {result['status']}")
    if result.get('result'):
        print(f"Reports generated: {len(result['result'].get('reports', []))}")
```

### JavaScript/TypeScript Client

```typescript
/**
 * Company Researcher API Client
 * Save as: client.ts
 */

interface ResearchRequest {
  company_name: string;
  url?: string;
  industry?: string;
  country?: string;
}

interface TaskStatus {
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: Record<string, any>;
  error?: string;
}

class ResearchClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async healthCheck(): Promise<Record<string, any>> {
    const response = await fetch(`${this.baseUrl}/health/detailed`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }

  async startResearch(request: ResearchRequest): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/v1/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start research');
    }

    const data = await response.json();
    return data.task_id;
  }

  async getStatus(taskId: string): Promise<TaskStatus> {
    const response = await fetch(`${this.baseUrl}/api/v1/research/${taskId}`);
    if (!response.ok) throw new Error('Failed to get status');
    return response.json();
  }

  async waitForCompletion(
    taskId: string,
    pollInterval: number = 10000,
    timeout: number = 1800000
  ): Promise<TaskStatus> {
    const startTime = Date.now();

    while (true) {
      if (Date.now() - startTime > timeout) {
        throw new Error(`Task ${taskId} timed out`);
      }

      const status = await this.getStatus(taskId);

      if (status.status === 'completed') {
        return status;
      } else if (status.status === 'failed') {
        throw new Error(`Task failed: ${status.error}`);
      }

      console.log(`Status: ${status.status}, waiting...`);
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }

  async research(request: ResearchRequest): Promise<TaskStatus> {
    const taskId = await this.startResearch(request);
    console.log(`Started task: ${taskId}`);
    return this.waitForCompletion(taskId);
  }
}

// Usage
const client = new ResearchClient();

client.research({
  company_name: 'Figma',
  url: 'https://figma.com',
  industry: 'Design Tools'
}).then(result => {
  console.log('Research completed:', result);
}).catch(error => {
  console.error('Research failed:', error);
});
```

### cURL Examples

```bash
# Start research
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Slack", "url": "https://slack.com"}'

# Response: {"task_id": "abc-123", "status": "pending", ...}

# Check status
curl http://localhost:8000/api/v1/research/abc-123

# Health check
curl http://localhost:8000/health/detailed
```

---

## Programmatic Usage

### Direct Orchestrator Usage

```python
"""
Use the ResearchOrchestrator directly without API.
"""
import asyncio
from src.agents.orchestrator import ResearchOrchestrator


async def research_company(company_name: str, url: str = None):
    """Run research directly using the orchestrator."""

    # Initialize orchestrator
    orchestrator = ResearchOrchestrator()

    # Run research
    result = await orchestrator.conduct_research(
        company_name=company_name,
        url=url or ""
    )

    return result


# Run
if __name__ == "__main__":
    result = asyncio.run(research_company(
        company_name="Airbnb",
        url="https://airbnb.com"
    ))

    print(f"Research completed!")
    print(f"Output path: {result.get('output_path')}")
```

### Using Individual Tools

```python
"""
Use individual tools for specific tasks.
"""
import asyncio
from src.tools.search import SearchTool
from src.tools.browser import BrowserTool
from src.tools.financial_data import FinancialDataTool


async def demo_tools():
    # Search tool
    search = SearchTool()
    results = await search.search("OpenAI company news 2024")
    print(f"Found {len(results)} search results")

    # Browser tool
    browser = BrowserTool()
    content = await browser.get_page_content("https://openai.com/about")
    print(f"Page content length: {len(content)}")

    # Financial data tool
    finance = FinancialDataTool()
    data = await finance.get_company_info("MSFT")
    print(f"Microsoft market cap: {data['market_data']['market_cap']}")


if __name__ == "__main__":
    asyncio.run(demo_tools())
```

### Using the AI Client

```python
"""
Direct AI client usage for custom prompts.
"""
import asyncio
from src.core.ai_client import get_ai_manager


async def demo_ai_client():
    client = get_ai_manager()

    # Simple generation
    response = await client.generate(
        "Summarize the key business model of Netflix in 3 bullet points."
    )
    print(response)

    # With JSON response
    response = await client.generate(
        """Extract company info as JSON:
        Company: Spotify
        Return: {"name": "...", "industry": "...", "founded": "..."}
        """,
        response_format="json"
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(demo_ai_client())
```

---

## Custom Agents

### Creating a New Specialist Agent

```python
"""
Example: Create a custom Patent Research Agent.
Save as: src/agents/patent_agent.py
"""
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.graph.state import ResearchState


class PatentAgent(BaseAgent):
    """Agent specialized in patent and IP research."""

    def __init__(self, client=None):
        super().__init__(
            client=client,
            name="PatentAgent",
            prompt_template="patent_research.md"  # Create this template
        )

    async def research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Research patents and intellectual property.

        Args:
            state: Current research state

        Returns:
            Patent research findings
        """
        company_name = state.company_name

        # Define search queries
        queries = [
            f"{company_name} patents filed",
            f"{company_name} intellectual property portfolio",
            f"{company_name} patent litigation",
            f"{company_name} R&D innovations"
        ]

        # Gather data using inherited method
        sources = await self._gather_data(queries)

        # Analyze with LLM
        analysis_prompt = f"""
        Analyze patent and IP information for {company_name}.

        Sources:
        {self._format_sources(sources)}

        Provide:
        1. Number of patents (estimated)
        2. Key patent areas/technologies
        3. Recent patent filings
        4. Notable IP litigation
        5. R&D focus areas

        Return as structured JSON.
        """

        analysis = await self.ai.generate(
            analysis_prompt,
            response_format="json"
        )

        # Return structured result
        return {
            "patent_data": analysis,
            "sources": sources,
            "agent": self.agent_name
        }

    def _format_sources(self, sources) -> str:
        """Format sources for prompt."""
        return "\n".join([
            f"- {s.title}: {s.content[:500]}..."
            for s in sources[:10]
        ])


# Integration: Add to orchestrator
# In src/agents/orchestrator.py, add:
# from src.agents.patent_agent import PatentAgent
# self.patent_agent = PatentAgent(client)
```

### Extending BaseAgent

```python
"""
Example: Agent with custom tool integration.
"""
from src.agents.base_agent import BaseAgent


class EnhancedAgent(BaseAgent):
    """Agent with additional capabilities."""

    def __init__(self, client=None):
        super().__init__(client=client, name="EnhancedAgent")

        # Add custom tools
        self.custom_api = CustomAPITool()

    async def research(self, state):
        # Use inherited tools
        search_results = await self.search_tool.search(f"{state.company_name}")

        # Use custom tool
        api_data = await self.custom_api.fetch(state.company_name)

        # Combine and analyze
        combined = self._merge_data(search_results, api_data)

        return await self._analyze(combined, state)
```

---

## Custom Tools

### Creating a New Data Tool

```python
"""
Example: Custom tool for Crunchbase-like data.
Save as: src/tools/startup_data.py
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel
from src.core.logger import setup_logger

logger = setup_logger("startup_tool")


class StartupInfo(BaseModel):
    """Structured startup information."""
    name: str
    founded: Optional[str] = None
    funding_total: Optional[str] = None
    funding_rounds: int = 0
    employees: Optional[str] = None
    investors: list[str] = []
    categories: list[str] = []


class StartupDataTool:
    """
    Tool for fetching startup/company data.

    In production, this would integrate with APIs like:
    - Crunchbase
    - PitchBook
    - CB Insights
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # Initialize API client here

    async def get_startup_info(self, company_name: str) -> StartupInfo:
        """
        Fetch startup information.

        Args:
            company_name: Name of the startup

        Returns:
            StartupInfo with available data
        """
        logger.info(f"Fetching startup data for: {company_name}")

        try:
            # In production: API call
            # data = await self._call_api(company_name)

            # Demo: Return placeholder
            return StartupInfo(
                name=company_name,
                founded="2020",
                funding_total="$50M",
                funding_rounds=3,
                employees="50-100",
                investors=["Sequoia", "a16z"],
                categories=["SaaS", "AI"]
            )

        except Exception as e:
            logger.error(f"Failed to fetch startup data: {e}")
            return StartupInfo(name=company_name)

    async def get_funding_history(self, company_name: str) -> list[Dict[str, Any]]:
        """Get detailed funding round history."""
        # Implementation here
        return []

    async def get_competitors(self, company_name: str) -> list[str]:
        """Get list of competitors."""
        # Implementation here
        return []


# Usage in agent:
# tool = StartupDataTool(api_key="...")
# info = await tool.get_startup_info("Notion")
```

### Integrating Tools with Agents

```python
"""
Add custom tool to BaseAgent.
"""
# In src/agents/base_agent.py, add:

from src.tools.startup_data import StartupDataTool

class BaseAgent(ABC):
    def __init__(self, ...):
        # Existing tools
        self.search_tool = SearchTool()
        self.browser_tool = BrowserTool()

        # Add new tool
        self.startup_tool = StartupDataTool()
```

---

## Testing Examples

### Unit Test Example

```python
"""
Test custom agent.
Save as: tests/test_patent_agent.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agents.patent_agent import PatentAgent
from src.graph.state import ResearchState


@pytest.fixture
def mock_ai_client():
    client = MagicMock()
    client.generate = AsyncMock(return_value='{"patents": 100}')
    return client


@pytest.fixture
def agent(mock_ai_client):
    return PatentAgent(client=mock_ai_client)


@pytest.fixture
def sample_state():
    return ResearchState(
        company_name="TestCorp",
        website="https://testcorp.com"
    )


@pytest.mark.asyncio
async def test_patent_research(agent, sample_state):
    result = await agent.research(sample_state)

    assert "patent_data" in result
    assert result["agent"] == "PatentAgent"
```

### Integration Test Example

```python
"""
Integration test with real API.
Save as: tests/integration/test_api.py
"""
import pytest
import requests

BASE_URL = "http://localhost:8000"


@pytest.mark.integration
def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.integration
def test_research_workflow():
    # Start research
    response = requests.post(
        f"{BASE_URL}/api/v1/research",
        json={"company_name": "TestCo"}
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    # Check status
    response = requests.get(f"{BASE_URL}/api/v1/research/{task_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "in_progress", "completed"]
```

---

## Related Documentation

- [API Reference](../api/API_REFERENCE.md)
- [Quick Start Tools](../guides/QUICK_START_TOOLS.md)
- [Module Documentation](../development/modules/)
