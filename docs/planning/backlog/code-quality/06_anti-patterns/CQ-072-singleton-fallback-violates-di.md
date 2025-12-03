# CQ-072: Singleton Fallback Violates Dependency Injection

## Metadata
- **Severity**: HIGH
- **Category**: Anti-patterns
- **File**: [src/agents/base_agent.py](src/agents/base_agent.py#L74)
- **Lines**: 71-74
- **Effort**: L
- **Status**: Open

## Problem

The `BaseAgent` class falls back to global singletons when dependencies aren't provided:

```python
class BaseAgent:
    def __init__(self, client=None, ...):
        self.ai = client or get_ai_manager()  # Global fallback!
        self.search = get_shared_search_tool()  # Always uses global!
```

This violates Dependency Injection principles:
1. Hidden dependencies make testing difficult
2. Can't easily substitute implementations
3. Global state creates coupling
4. Initialization order becomes critical

## Why This Is a Problem

### Testing Difficulties
```python
# Can't easily test with mock AI client
def test_agent():
    agent = BaseAgent()  # Uses real AI client!
    # How to inject mock?
```

### Hidden Dependencies
```python
# Caller doesn't know agent needs search tool
agent = BaseAgent(client=mock_client)
# Surprise! It's using global search tool
```

### Initialization Order
```python
# If get_ai_manager() called before config loaded...
import agents  # Triggers singleton creation
load_config()  # Too late! Manager already created
```

## Solution

### Step 1: Require Explicit Dependencies

```python
from typing import Optional, Protocol

class AIClient(Protocol):
    """Protocol for AI client implementations."""
    async def generate(self, prompt: str) -> str: ...

class SearchTool(Protocol):
    """Protocol for search tool implementations."""
    async def search(self, query: str) -> List[Result]: ...


class BaseAgent:
    """Base class for all research agents."""

    def __init__(
        self,
        ai_client: AIClient,
        search_tool: Optional[SearchTool] = None,
        browser_tool: Optional[BrowserTool] = None,
        name: Optional[str] = None
    ):
        """
        Initialize agent with required dependencies.

        Args:
            ai_client: AI client for LLM operations (REQUIRED)
            search_tool: Optional search tool for web searches
            browser_tool: Optional browser tool for page fetching
            name: Agent name for logging (defaults to class name)

        Raises:
            ValueError: If ai_client is None
        """
        if ai_client is None:
            raise ValueError(
                "ai_client is required. Use AgentFactory to create agents "
                "with proper dependency injection."
            )

        self.ai = ai_client
        self.search = search_tool
        self.browser = browser_tool
        self.name = name or self.__class__.__name__
```

### Step 2: Create Factory for Convenience

```python
# src/agents/factory.py

from src.core.di import Container

class AgentFactory:
    """Factory for creating agents with proper dependencies."""

    def __init__(self, container: Optional[Container] = None):
        """
        Initialize factory with DI container.

        Args:
            container: DI container. If None, creates default container.
        """
        self.container = container or self._create_default_container()

    def _create_default_container(self) -> Container:
        """Create container with default implementations."""
        container = Container()
        container.register(AIClient, AIClientImpl)
        container.register(SearchTool, SearchToolImpl)
        return container

    def create_research_agent(self, **kwargs) -> ResearchAgent:
        """Create a research agent with injected dependencies."""
        return ResearchAgent(
            ai_client=self.container.resolve(AIClient),
            search_tool=self.container.resolve(SearchTool),
            **kwargs
        )

    def create_financial_agent(self, **kwargs) -> FinancialAgent:
        """Create a financial agent with injected dependencies."""
        return FinancialAgent(
            ai_client=self.container.resolve(AIClient),
            financial_tool=self.container.resolve(FinancialTool),
            **kwargs
        )
```

### Step 3: Update All Agent Subclasses

```python
class DeepResearchAgent(BaseAgent):
    """Agent for deep iterative research."""

    def __init__(
        self,
        ai_client: AIClient,
        search_tool: SearchTool,  # Required for this agent
        browser_tool: Optional[BrowserTool] = None,
        breadth: int = 4,
        depth: int = 2
    ):
        super().__init__(
            ai_client=ai_client,
            search_tool=search_tool,
            browser_tool=browser_tool
        )
        self.breadth = breadth
        self.depth = depth
```

### Step 4: Easy Testing

```python
# Tests are now straightforward
def test_agent_with_mock():
    mock_ai = MockAIClient()
    mock_search = MockSearchTool()

    agent = DeepResearchAgent(
        ai_client=mock_ai,
        search_tool=mock_search
    )

    # Full control over dependencies
    mock_search.search.return_value = [Result(...)]
    result = await agent.research("query")

    mock_search.search.assert_called_once()
```

## Migration Steps

1. **Add required parameter validation** to BaseAgent.__init__
2. **Update AgentFactory** to always provide dependencies
3. **Update all subclasses** to pass dependencies to super()
4. **Update all call sites** to use factory or provide deps
5. **Remove global singleton getters** after migration
6. **Add deprecation warnings** during transition

### Transition Pattern

```python
class BaseAgent:
    def __init__(self, ai_client=None, ...):
        if ai_client is None:
            warnings.warn(
                "Creating agent without ai_client is deprecated. "
                "Use AgentFactory or provide dependencies explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            ai_client = get_ai_manager()  # Temporary fallback

        self.ai = ai_client
```

## Files to Update

1. `src/agents/base_agent.py` - Core fix
2. `src/agents/deep_research.py` - Update constructor
3. `src/agents/specialists.py` - Update all specialist agents
4. `src/agents/factory.py` - Ensure DI usage
5. `src/agents/reasoning_agent.py` - Update constructor
6. All files that create agents directly

## Verification Checklist

- [ ] BaseAgent requires ai_client parameter
- [ ] No global singleton fallbacks in constructors
- [ ] AgentFactory provides all dependencies
- [ ] All tests use explicit dependency injection
- [ ] Deprecation warnings for transitional period
- [ ] No direct calls to get_ai_manager() in agents
