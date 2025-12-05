# CQ-058: Factory Tool Initialization Duplication

## Metadata
- **Severity**: HIGH
- **Category**: Code Duplication
- **File**: [src/agents/factory.py](src/agents/factory.py#L154-L240)
- **Lines**: 154-240
- **Effort**: M
- **Status**: Open

## Problem

The factory.py file contains 12 nearly identical try/except blocks for initializing different tools. Each block follows the exact same pattern:

```python
try:
    self.tool_name = ToolClass(config)
except Exception as e:
    logger.warning(f"Failed to initialize tool_name: {e}")
    self.tool_name = None
```

This violates DRY (Don't Repeat Yourself) and makes maintenance difficult.

## Current Code

```python
# Repeated 12 times with minor variations
try:
    self.search_tool = SearchTool(
        providers=providers,
        rate_limiter=rate_limiter
    )
except Exception as e:
    logger.warning(f"Failed to initialize search tool: {e}")
    self.search_tool = None

try:
    self.browser_tool = BrowserTool(
        config=browser_config
    )
except Exception as e:
    logger.warning(f"Failed to initialize browser tool: {e}")
    self.browser_tool = None

try:
    self.financial_tool = FinancialTool(
        api_key=financial_api_key
    )
except Exception as e:
    logger.warning(f"Failed to initialize financial tool: {e}")
    self.financial_tool = None

# ... 9 more identical blocks ...
```

## Solution

Create a generic tool initialization method:

```python
from typing import TypeVar, Callable, Optional
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class ToolConfig:
    """Configuration for tool initialization."""
    name: str
    factory: Callable[[], T]
    required: bool = False
    fallback: Optional[T] = None


class AgentFactory:
    def __init__(self, ...):
        # Define tool configurations
        tool_configs = [
            ToolConfig(
                name="search",
                factory=lambda: SearchTool(providers=providers, rate_limiter=rate_limiter),
                required=True  # Search is required
            ),
            ToolConfig(
                name="browser",
                factory=lambda: BrowserTool(config=browser_config),
            ),
            ToolConfig(
                name="financial",
                factory=lambda: FinancialTool(api_key=financial_api_key),
            ),
            ToolConfig(
                name="news",
                factory=lambda: NewsTool(api_key=news_api_key),
            ),
            # ... other tools ...
        ]

        # Initialize all tools using the generic method
        for config in tool_configs:
            tool = self._init_tool(config)
            setattr(self, f"{config.name}_tool", tool)

    def _init_tool(self, config: ToolConfig) -> Optional[T]:
        """
        Initialize a tool with standard error handling.

        Args:
            config: Tool configuration including factory and options

        Returns:
            Initialized tool instance, or None/fallback on failure

        Raises:
            ToolInitializationError: If required tool fails to initialize
        """
        try:
            tool = config.factory()
            logger.debug(f"Initialized {config.name} tool")
            return tool
        except Exception as e:
            if config.required:
                logger.error(f"Required tool {config.name} failed: {e}")
                raise ToolInitializationError(
                    f"Failed to initialize required tool: {config.name}"
                ) from e
            else:
                logger.warning(
                    f"Optional tool {config.name} unavailable: {e}",
                    extra={"tool": config.name, "error": str(e)}
                )
                return config.fallback
```

### Alternative: Decorator Approach

```python
def tool_initializer(name: str, required: bool = False):
    """Decorator for tool initialization methods."""
    def decorator(init_func: Callable[[], T]) -> Callable[[], Optional[T]]:
        @functools.wraps(init_func)
        def wrapper(self) -> Optional[T]:
            try:
                tool = init_func(self)
                logger.debug(f"Initialized {name}")
                return tool
            except Exception as e:
                if required:
                    raise ToolInitializationError(f"{name} required") from e
                logger.warning(f"{name} unavailable: {e}")
                return None
        return wrapper
    return decorator


class AgentFactory:
    @tool_initializer("search", required=True)
    def _init_search(self) -> SearchTool:
        return SearchTool(providers=self.providers)

    @tool_initializer("browser")
    def _init_browser(self) -> BrowserTool:
        return BrowserTool(config=self.browser_config)

    def __init__(self, ...):
        self.search_tool = self._init_search()
        self.browser_tool = self._init_browser()
        # ...
```

## Benefits

1. **Single point of change**: Error handling logic in one place
2. **Consistent logging**: All tools log the same way
3. **Required vs optional**: Clear distinction
4. **Testability**: Can mock `_init_tool` for testing
5. **Extensibility**: Easy to add new tools
6. **Reduced lines**: ~90 lines reduced to ~30

## Testing

```python
def test_tool_initialization_success():
    """Test successful tool initialization."""
    factory = AgentFactory(...)
    assert factory.search_tool is not None
    assert factory.browser_tool is not None

def test_optional_tool_failure():
    """Test optional tool gracefully handles failure."""
    with patch('src.tools.browser.BrowserTool', side_effect=Exception("No browser")):
        factory = AgentFactory(...)
        assert factory.browser_tool is None
        assert factory.search_tool is not None  # Others still work

def test_required_tool_failure():
    """Test required tool failure raises exception."""
    with patch('src.tools.search.SearchTool', side_effect=Exception("No search")):
        with pytest.raises(ToolInitializationError):
            AgentFactory(...)
```

## Related Issues

- CQ-059: Similar pattern in specialists.py _fetch_* methods
