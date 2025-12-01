# Agent 4: Features & Documentation

## Focus Area
New features, API improvements, UI enhancements, and documentation.

## Priority: MEDIUM

---

## Task 1: Documentation Gaps
**Files:** `docs/planning/backlog/documentation/DOC-001-*.md` through `DOC-013-*.md`

### High Priority Docs
- [ ] DOC-001: Generate API documentation (OpenAPI/Swagger)
- [ ] DOC-002: Create architecture documentation with diagrams
- [ ] DOC-007: Write troubleshooting guide
- [ ] DOC-008: Write deployment guide

### Subtasks
- [ ] Generate OpenAPI spec from FastAPI endpoints
- [ ] Create architecture diagrams (Mermaid or draw.io)
- [ ] Document all environment variables
- [ ] Write common troubleshooting scenarios

### Files to Create
- `docs/api/openapi.yaml` (or auto-generate)
- `docs/architecture/overview.md`
- `docs/guides/TROUBLESHOOTING.md`
- `docs/guides/DEPLOYMENT.md`

---

## Task 2: Interactive Research Mode (FEAT-001)
**File:** `docs/planning/backlog/features/FEAT-001-interactive-research-mode.md`

### Subtasks
- [ ] Implement user prompting during research
- [ ] Add confirmation points for expensive operations
- [ ] Support research direction adjustments mid-flow
- [ ] Add progress callbacks for UI integration

### Files to Create
- `src/core/interactive.py`

### Files to Modify
- `src/pipeline/orchestrator.py`
- `main.py`

---

## Task 3: Progress Reporting (FEAT-010-progress)
**File:** `docs/planning/backlog/features/FEAT-010-progress-reporting.md`

### Subtasks
- [ ] Implement progress callbacks
- [ ] Add stage completion notifications
- [ ] Create progress percentage calculation
- [ ] Support WebSocket progress updates

### Files to Modify
- `src/pipeline/orchestrator.py`
- `src/api/app.py`

### Progress Events
```python
events = [
    {"stage": "search", "progress": 25, "message": "Searching sources..."},
    {"stage": "extract", "progress": 50, "message": "Extracting content..."},
    {"stage": "analyze", "progress": 75, "message": "Analyzing data..."},
    {"stage": "generate", "progress": 100, "message": "Generating report..."},
]
```

---

## Task 4: Task Management APIs
**Files:** `docs/planning/backlog/features/FEAT-011-*.md`, `FEAT-012-*.md`

### Subtasks
- [ ] Implement task cancellation support (FEAT-011)
- [ ] Add task result pagination (FEAT-012)
- [ ] Create task status polling endpoint
- [ ] Support batch task submission

### Files to Modify
- `src/api/app.py`
- `src/api/models.py`

### New Endpoints
```
POST   /api/v1/tasks              # Submit task
GET    /api/v1/tasks/{id}         # Get task status
DELETE /api/v1/tasks/{id}         # Cancel task
GET    /api/v1/tasks/{id}/result  # Get paginated result
```

---

## Task 5: UI Improvements
**Files:** `docs/planning/backlog/ui/UI-001-*.md`, `UI-002-*.md`

### Subtasks
- [ ] Improve Streamlit error handling (UI-001)
- [ ] Fix session state management (UI-002)
- [ ] Add progress bars (from 11-ux.md)
- [ ] Improve loading states

### Files to Modify
- Streamlit app files (if exists)
- `src/api/app.py` (for API-based UI)

---

## Task 6: Tech Debt - Hardcoded Values
**Files:** `docs/planning/backlog/tech-debt/TECH-001-*.md` through `TECH-016-*.md`

### Priority Items
- [ ] TECH-001: Move hardcoded AI model names to config
- [ ] TECH-005: Move browser timeout to config
- [ ] TECH-006: Move search timeout to config
- [ ] TECH-011: Move CORS methods to config

### Files to Modify
- `src/core/config.py` (add new settings)
- `src/core/ai_client.py`
- `src/tools/browser.py`
- `src/tools/search_tool.py`
- `src/api/app.py`

---

## Task 7: Follow-up Generation (FEAT-009)
**File:** `docs/planning/backlog/features/FEAT-009-follow-up-generation.md`

### Subtasks
- [ ] Generate follow-up questions based on research
- [ ] Identify knowledge gaps in reports
- [ ] Suggest deeper research areas
- [ ] Integrate with interactive mode

### Files to Create
- `src/services/followup_generator.py`

---

## Acceptance Criteria
- [ ] API documentation auto-generated and accessible
- [ ] Architecture diagrams created for key flows
- [ ] Interactive mode functional for CLI usage
- [ ] Progress reporting working via API
- [ ] Task cancellation working
- [ ] All hardcoded values moved to configuration

## Estimated Scope
- **Documentation files:** 4-6
- **Source files to create:** 3-4
- **Source files to modify:** 8-10

---

## Getting Started

```bash
# Generate OpenAPI docs
python -c "from src.api.app import app; import json; print(json.dumps(app.openapi()))"

# Run Streamlit UI (if exists)
streamlit run ui/app.py

# Test API endpoints
pytest tests/api/ -v
```

## Documentation Standards
- Use Mermaid for diagrams (renders in GitHub)
- Follow Google docstring style
- Include code examples in guides
- Keep troubleshooting actionable

## Related Documentation
- [06-documentation.md](../backlog/06-documentation.md)
- [03-features.md](../backlog/03-features.md)
- [11-ux.md](../backlog/11-ux.md)
