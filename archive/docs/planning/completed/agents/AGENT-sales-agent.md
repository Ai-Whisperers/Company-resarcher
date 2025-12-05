# [RESOLVED] AGENT: Sales Agent

**Status**: RESOLVED
**Original File**: backlog/08-agents-tools.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Create a specialist agent that analyzes research data to generate sales pitches.

**Acceptance Criteria:**
- [x] Create sales agent class
- [x] Input: `CompanyProfile`, `ResearchContext`
- [x] Output: `SalesStrategy` (Pain points, Value prop, Pitch deck outline)

## Resolution

### Implementation

**File:** `src/agents/specialists.py`

```python
class SalesAgent(BaseAgent):
    """Specialist for sales strategy."""

    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_SALES,
            prompt_template="sales_strategy.txt",
            **kwargs,
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        safe_name = sanitize_company_name(company.name)
        queries = [
            f"{safe_name} sales strategy",
            f"{safe_name} distribution channels",
            f"{safe_name} pricing strategy",
            f"{safe_name} B2B clients",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="05-Sales-Strategy.md",
        )
```

### Files

- **Agent:** `src/agents/specialists.py` - `SalesAgent` class
- **Prompt:** `src/prompts/sales_strategy.txt`
- **Template:** `src/templates/05-Sales-Strategy.md`

### Output Structure

The agent generates reports containing:
- Executive Summary
- Company Context (Business model, Tech stack, Organization)
- Strategic Priorities with timeline and investment level
- Identified Pain Points with business impact and urgency
- Decision Makers (Key titles, Buying process, Budget cycle)
- Recommended Solutions with rationale and pitch angles
- Competitive Positioning
- Engagement Strategy
- Next Steps
