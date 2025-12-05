# CQ-040: Missing Type Hints in Agent Classes

## Metadata
- **Severity**: HIGH
- **Category**: Type Hints
- **Files**: Multiple agent files
- **Effort**: M
- **Status**: Open

## Problem

Several agent classes have missing or incorrect type hints, making the code harder to understand and preventing static analysis tools from catching bugs.

## Affected Files

| File | Issue |
|------|-------|
| reasoning_agent.py:17-18 | `tools` parameter no type, defaults to None |
| sector_analyst.py:9+ | Entire class missing annotations |
| deep_research.py:64-75 | Constructor param name mismatch |
| generic_agent.py:20-35 | Phase config validation incomplete |
| specialists.py:19-38 | DataSourceResult needs documentation |

## Detailed Issues

### 1. reasoning_agent.py - Missing Parameter Types

```python
# CURRENT (line 17-18)
def __init__(self, name=None, tools=None, client=None):
    self.tools = tools or []
    self.client = client  # Never used!

# FIXED
from typing import List, Optional
from src.tools.base import BaseTool
from src.core.ai import AIClient

def __init__(
    self,
    name: Optional[str] = None,
    tools: Optional[List[BaseTool]] = None,
    client: Optional[AIClient] = None
) -> None:
    super().__init__(client=client, name=name)
    self.tools = tools or []
    # Removed unused self.client - parent handles it
```

### 2. sector_analyst.py - Entire Class Missing Types

```python
# CURRENT
class SectorAnalyst:
    def __init__(self):
        self.vault = VaultManager()
        self.ai = get_ai_manager()

    def analyze_sector(self, sector, companies):
        # No types!
        pass

    def compare_companies(self, companies):
        # No types!
        pass

# FIXED
from typing import List, Dict, Any, Optional
from src.core.vault import VaultManager
from src.core.ai import AIClientManager

class SectorAnalyst:
    """Analyzes sectors and compares companies within them."""

    def __init__(
        self,
        vault: Optional[VaultManager] = None,
        ai_manager: Optional[AIClientManager] = None
    ) -> None:
        self.vault = vault or VaultManager()
        self.ai = ai_manager or get_ai_manager()

    async def analyze_sector(
        self,
        sector: str,
        companies: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a sector based on company data.

        Args:
            sector: Sector name (e.g., "Technology", "Healthcare")
            companies: List of company names to analyze

        Returns:
            Dict containing sector analysis with keys:
                - overview: Sector overview text
                - trends: List of identified trends
                - leaders: Top companies in sector
        """
        pass

    async def compare_companies(
        self,
        companies: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple companies.

        Args:
            companies: List of company names to compare

        Returns:
            Comparison matrix and rankings
        """
        pass
```

### 3. deep_research.py - Parameter Name Mismatch

```python
# CURRENT (line 64-75)
class DeepResearchAgent(BaseAgent):
    def __init__(self, ai_client, ...):  # Uses 'ai_client'
        super().__init__(client=ai_client)  # Parent expects 'client'

# FIXED - Consistent naming
class DeepResearchAgent(BaseAgent):
    def __init__(
        self,
        client: AIClient,  # Match parent parameter name
        search_tool: Optional[SearchTool] = None,
        breadth: int = DEFAULT_BREADTH,
        depth: int = DEFAULT_DEPTH
    ) -> None:
        super().__init__(client=client, search_tool=search_tool)
        self.breadth = breadth
        self.depth = depth
```

### 4. generic_agent.py - Incomplete Validation

```python
# CURRENT (line 20-35)
def validate_phase_config(config):
    if "name" not in config:
        raise ValueError("Missing name")
    # Doesn't check for empty strings or None values

# FIXED
from typing import Dict, Any, List

def validate_phase_config(config: Dict[str, Any]) -> None:
    """
    Validate phase configuration.

    Args:
        config: Phase configuration dictionary

    Raises:
        ValueError: If required fields missing or invalid
    """
    required_fields: List[str] = ["name", "queries", "template"]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
        if config[field] is None:
            raise ValueError(f"Field cannot be None: {field}")
        if isinstance(config[field], str) and not config[field].strip():
            raise ValueError(f"Field cannot be empty string: {field}")
```

### 5. specialists.py - DataSourceResult Documentation

```python
# CURRENT (line 19-38)
@dataclass
class DataSourceResult:
    source: str
    data: Any
    error: Optional[str] = None

# FIXED
from dataclasses import dataclass, field
from typing import Any, Optional, List
from datetime import datetime

@dataclass
class DataSourceResult:
    """
    Container for data fetched from a specific source.

    This dataclass encapsulates results from various data tools
    (financial, news, social, etc.) with consistent error handling.

    Attributes:
        source: Name of the data source (e.g., "financial", "news")
        data: The fetched data, or None if fetch failed
        error: Error message if fetch failed, None otherwise
        timestamp: When the data was fetched
        metadata: Additional metadata about the fetch

    Example:
        >>> result = DataSourceResult(source="financial", data={"revenue": 1M})
        >>> if result.has_error:
        ...     logger.warning(f"Failed: {result.error}")
    """
    source: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_error(self) -> bool:
        """Check if this result represents an error."""
        return self.error is not None

    @property
    def has_data(self) -> bool:
        """Check if this result contains data."""
        return self.data is not None
```

## Verification

Run mypy to verify type hints:

```bash
# Install mypy
pip install mypy

# Check specific files
mypy src/agents/reasoning_agent.py
mypy src/agents/sector_analyst.py
mypy src/agents/deep_research.py
mypy src/agents/generic_agent.py
mypy src/agents/specialists.py

# Check all agents
mypy src/agents/
```

## Checklist

- [ ] reasoning_agent.py has complete type hints
- [ ] sector_analyst.py has complete type hints
- [ ] deep_research.py uses consistent param names
- [ ] generic_agent.py validates all config fields
- [ ] specialists.py DataSourceResult documented
- [ ] mypy passes with no errors
- [ ] All public methods have return types
