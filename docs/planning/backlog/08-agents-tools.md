# Agents & Tools Backlog Items

### [AGENT] Implement SalesAgent (Phase 3)

**Priority:** Medium
**Description:** Create a specialist agent that analyzes research data to generate sales pitches.
**Acceptance Criteria:**

- [ ] Create `src/agents/specialists/sales.py`.
- [ ] Input: `CompanyProfile`, `ResearchContext`.
- [ ] Output: `SalesStrategy` (Pain points, Value prop, Pitch deck outline).
- [ ] Use `RAG` to find relevant case studies from internal docs.

### [AGENT] Implement InvestmentAgent (Phase 3)

**Priority:** Medium
**Description:** Create a specialist agent for investment thesis generation.
**Acceptance Criteria:**

- [ ] Create `src/agents/specialists/investment.py`.
- [ ] Input: Financial data, Market trends.
- [ ] Output: `InvestmentMemo` (Risks, Upside, SWOT, Recommendation).

### [AGENT] Social Media Agent

**Priority:** Low
**Description:** Analyze public social media footprint.
**Acceptance Criteria:**

- [ ] Integrate with Twitter/LinkedIn APIs (or scrapers).
- [ ] Analyze sentiment and engagement.
- [ ] Identify key decision makers.

### [TOOL] Chart Generator Tool

**Priority:** Low
**Description:** Generate visualization for financial data.
**Acceptance Criteria:**

- [ ] Use `matplotlib` or `plotly`.
- [ ] Input: JSON data series.
- [ ] Output: Image file path (PNG/SVG).

### [TOOL] YouTube Transcript Tool

**Priority:** Low
**Description:** Extract transcripts from relevant YouTube videos (interviews, product launches).
**Acceptance Criteria:**

- [ ] Use `youtube-transcript-api`.
- [ ] Input: Video URL.
- [ ] Output: Text transcript with timestamps.

### [CODE] Remove Hardcoded "Objective" Tone

**Priority:** Low
**Description:** `DeepResearchAgent` defaults to "Objective" tone. This should be configurable.
**Acceptance Criteria:**

- [ ] Pass `tone` from `main.py` arguments.
- [ ] Update prompts to reflect the requested tone.

### [CODE] Fix "Unknown" Title in ResearchSource

**Priority:** Low
**Description:** `ResearchSource` defaults title to "Unknown". We should try to extract it from HTML `<title>` tag if missing.
**Acceptance Criteria:**

- [ ] In `BrowserTool`, ensure title is always extracted.
- [ ] Fallback to domain name if no title found.

### [CODE] Standardize Error Classes

**Priority:** Medium
**Description:** We have `ResultSearchError`, `ProviderSearchError`, etc.
**Acceptance Criteria:**

- [ ] Create a unified `ResearchError` hierarchy in `src/core/exceptions.py`.
- [ ] Ensure all tools raise/return these standard errors.
