# LOW: No Graceful Degradation for Missing Tools

## Severity: Low
## File: `src/agents/factory.py`

## Problem

Factory creates tools without checking if dependencies exist:

```python
def create_specialists(self) -> Dict[str, BaseAgent]:
    from src.tools.youtube_tool import YouTubeTool
    from src.tools.sec_tool import SECTool
    from src.tools.app_store_tool import AppStoreTool
    from src.tools.tech_stack_tool import TechStackTool

    youtube_tool = YouTubeTool()      # Crashes if youtube-dl not installed
    sec_tool = SECTool()              # Crashes if edgartools not installed
    app_store_tool = AppStoreTool()   # Crashes if dependency missing
    tech_stack_tool = TechStackTool() # Crashes if webtech not installed
```

## Impact

- Missing optional dependency crashes entire factory
- Cannot run system with subset of tools
- All-or-nothing approach
- Poor user experience for quick setups

## Solution

Use try/except with graceful fallback:

```python
def create_specialists(self) -> Dict[str, BaseAgent]:
    # Try to load optional tools
    youtube_tool = None
    sec_tool = None
    app_store_tool = None
    tech_stack_tool = None

    try:
        from src.tools.youtube_tool import YouTubeTool
        youtube_tool = YouTubeTool()
    except ImportError as e:
        logger.warning(f"YouTubeTool unavailable: {e}")

    try:
        from src.tools.sec_tool import SECTool
        sec_tool = SECTool()
    except ImportError as e:
        logger.warning(f"SECTool unavailable: {e}")

    try:
        from src.tools.app_store_tool import AppStoreTool
        app_store_tool = AppStoreTool()
    except ImportError as e:
        logger.warning(f"AppStoreTool unavailable: {e}")

    try:
        from src.tools.tech_stack_tool import TechStackTool
        tech_stack_tool = TechStackTool()
    except ImportError as e:
        logger.warning(f"TechStackTool unavailable: {e}")

    return {
        "financial": FinancialAgent(
            self.ai_client, search_tool=search_tool, sec_tool=sec_tool
        ),
        # ... etc
    }
```

## Testing

After fix:
1. Uninstall optional dependency (e.g., edgartools)
2. Run research
3. Verify system works with warning, not crash
