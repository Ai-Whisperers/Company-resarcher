# New Features Backlog Items

### [FEAT] Interactive Research Mode

**Priority:** High
**Description:** Implement the "Ask User" functionality in `DeepResearchAgent`.
**Acceptance Criteria:**

- [ ] When `generate_research_plan` produces questions, pause execution.
- [ ] Prompt user via CLI (or API callback) for answers.
- [ ] Resume research with user answers.
      **Technical Notes:**
- File: `src/agents/deep_research.py` (Line 416 TODO)

### [FEAT] Resume Interrupted Research

**Priority:** High
**Description:** Research can take a long time. If it crashes, we should be able to resume from the last checkpoint.
**Acceptance Criteria:**

- [ ] Serialize `ResearchState` to disk/DB after each phase/step.
- [ ] Add `--resume <run_id>` flag to `main.py`.
- [ ] Load state and continue execution.
      **Technical Notes:**
- Use `pickle` or JSON for state serialization.

### [FEAT] Advanced Search Operators

**Priority:** Medium
**Description:** Allow trusted agents to use `site:`, `filetype:pdf`, etc., in search queries.
**Acceptance Criteria:**

- [ ] Add `safe_mode=True` default to `SearchTool`.
- [ ] Allow `safe_mode=False` for `DeepResearchAgent`.
- [ ] Update `sanitize_search_query` to respect the flag.
      **Technical Notes:**
- File: `src/tools/search_tool.py`

### [FEAT] Graph Persistence with Redis

**Priority:** Medium
**Description:** Move "Dead Letter Queue" and "Circuit Breaker" state from memory to Redis.
**Acceptance Criteria:**

- [ ] Implement `RedisDeadLetterQueue`.
- [ ] Implement `RedisCircuitBreaker`.
- [ ] Update `GraphBuilder` to use these implementations if Redis is available.
      **Technical Notes:**
- File: `src/graph/graph_builder.py`

### [FEAT] PDF Report Generation

**Priority:** Medium
**Description:** Generate a professional PDF report alongside Markdown.
**Acceptance Criteria:**

- [ ] Add `weasyprint` or `reportlab` dependency.
- [ ] Convert Markdown/HTML output to PDF.
- [ ] Apply styling (CSS) for a professional look.
      **Technical Notes:**
- File: `src/core/report_generator.py`

### [FEAT] Web UI with Streamlit

**Priority:** Medium
**Description:** Create a simple Web UI to trigger research and view results.
**Acceptance Criteria:**

- [ ] Create `src/ui/app.py`.
- [ ] Input: Company Name, URL, Industry.
- [ ] Output: Real-time logs, Final Report viewer.
      **Technical Notes:**
- Use `streamlit` (already in requirements).
