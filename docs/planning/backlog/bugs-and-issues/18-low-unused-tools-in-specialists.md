# LOW: Unused Tools in Specialists

## Severity: Low
## File: `src/agents/specialists.py` (lines 74-75, 141-142)

## Problem

MarketAnalyst and BrandAuditor accept tools but never use them:

```python
class MarketAnalyst(BaseAgent):
    def __init__(self, ..., youtube_tool=None, app_store_tool=None, **kwargs):
        self.youtube_tool = youtube_tool
        self.app_store_tool = app_store_tool

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        # youtube_tool and app_store_tool are NEVER used here!
        queries = [...]
        return await self.execute_research_cycle(...)


class BrandAuditor(BaseAgent):
    def __init__(self, ..., youtube_tool=None, app_store_tool=None, **kwargs):
        self.youtube_tool = youtube_tool
        self.app_store_tool = app_store_tool

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        # Also never used!
```

## Impact

- Dead code / unused objects
- Misleading API - suggests tools are used
- Wastes memory initializing unused tools
- Confusing for developers

## Solution

Option 1: Remove unused tools if not planned:

```python
class MarketAnalyst(BaseAgent):
    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(...)
        # No youtube_tool, no app_store_tool
```

Option 2: Actually use the tools:

```python
class MarketAnalyst(BaseAgent):
    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [...]

        # Use YouTube tool for market insights
        youtube_data = {}
        if self.youtube_tool:
            youtube_data = await self.youtube_tool.search_videos(
                f"{company.name} market analysis"
            )

        # Use App Store tool for mobile presence
        app_data = {}
        if self.app_store_tool and company.name:
            app_data = await self.app_store_tool.search_apps(company.name)

        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            extra_context={
                "youtube_insights": youtube_data,
                "app_store_data": app_data,
            },
            ...
        )
```

## Testing

After fix (if implementing):
1. Research a company with YouTube presence
2. Verify YouTube data appears in market analysis
3. Research a company with mobile apps
4. Verify app data appears in analysis
