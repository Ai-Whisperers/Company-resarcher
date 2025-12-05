# [RESOLVED] AGENT: Investment Agent

**Status**: RESOLVED
**Original File**: backlog/08-agents-tools.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Create a specialist agent for investment thesis generation.

**Acceptance Criteria:**
- [x] Create investment agent class
- [x] Input: Financial data, Market trends
- [x] Output: `InvestmentMemo` (Risks, Upside, SWOT, Recommendation)

## Resolution

### Implementation

**File:** `src/agents/specialists.py`

```python
class InvestmentAgent(BaseAgent):
    """
    Specialist agent for investment thesis generation.

    Analyzes financial data and market trends to generate investment memos
    including risk assessment, growth potential, SWOT analysis, and recommendations.
    """

    def __init__(
        self,
        client: BaseAIClient = None,
        financial_tool=None,
        sec_tool=None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            name="investment_analyst",
            prompt_template="investment_analysis.txt",
            **kwargs,
        )
        self.financial_tool = financial_tool
        self.sec_tool = sec_tool
```

### Files

- **Agent:** `src/agents/specialists.py` - `InvestmentAgent` class
- **Prompt:** `src/prompts/investment_analysis.txt`
- **Template:** `src/templates/06-Investment-Memo.md`

### Output Structure

The agent generates investment memos containing:
- Executive Summary (Recommendation, Conviction Level, Price Target)
- Valuation Analysis (P/E, EV/EBITDA, Fair Value)
- Growth Catalysts with timeline and impact assessment
- Risk Factors with severity and mitigation strategies
- Competitive Moat analysis
- SWOT Analysis
- Management Assessment
- Financial Health metrics
- Institutional Ownership data
- Scenario Analysis (Bull/Base/Bear cases)
- Key Metrics to Watch
- Investment Horizon and Position Sizing recommendations

### Data Sources

- SEC filings (10-K) via `sec_tool`
- Financial metrics via `financial_tool`
- Web search for market intelligence
