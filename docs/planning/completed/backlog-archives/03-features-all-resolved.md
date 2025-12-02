# New Features Backlog Items

## Already Implemented

### [FEAT] Interactive Research Mode ✅ RESOLVED

**Status:** RESOLVED - See `resolved/features/FEAT-03-04-features-enhancements.md`
**Implementation:** `src/core/interactive.py`

Features:
- [x] `InteractiveSession` class with `confirm()`, `choose()`, `get_input()`
- [x] Progress callbacks (Console, WebSocket, Multi)
- [x] `ProgressTracker` for phase-based progress
- [x] Cost/time confirmation for expensive operations

### [FEAT] Resume Interrupted Research ✅ RESOLVED

**Status:** RESOLVED - See `resolved/features/FEAT-03-04-features-enhancements.md`
**Implementation:** `src/core/session.py`

Features:
- [x] `SessionManager` with JSON persistence
- [x] `Session` and `SessionCheckpoint` dataclasses
- [x] Automatic checkpointing every N steps
- [x] `load_session()` / `save_session()` methods

---

## Remaining Features

### [FEAT] Advanced Search Operators ✅ RESOLVED

**Status:** RESOLVED - See `resolved/features/FEAT-advanced-search-operators.md`
**Implementation:** `src/tools/search_tool.py`

Features:
- [x] Add `safe_mode=True` default to `SearchTool`
- [x] Allow `safe_mode=False` for trusted agents
- [x] Update `sanitize_search_query` to respect the flag

### [FEAT] Graph Persistence with Redis ✅ RESOLVED

**Status:** RESOLVED
**Implementation:** `src/core/redis_cache.py`

Features:

- [x] Implement `RedisDeadLetterQueue` - persistent dead letter queue using Redis lists
- [x] Implement `RedisCircuitBreaker` - distributed circuit breaker with state management
- [x] `RedisCache` base class with connection pooling, TTL, key prefixing
- [x] Helper functions: `cache_research_result()`, `cache_search_results()`
- [ ] Optional: Update `GraphBuilder` to use Redis implementations (future enhancement)

### [FEAT] PDF Report Generation ✅ RESOLVED

**Status:** RESOLVED - See `resolved/features/FEAT-005-pdf-generation.md`
**Implementation:** `src/core/report_generator.py`

Features:

- [x] Add `weasyprint` dependency
- [x] Convert Markdown/HTML output to PDF
- [x] Professional CSS styling with A4 format
- [x] Page headers and footers
- [x] Table and code block styling

### [FEAT] Web UI with Streamlit ✅ RESOLVED

**Status:** RESOLVED - See `resolved/features/FEAT-03-04-features-enhancements.md`
**Implementation:** `src/ui/app.py`

Features:

- [x] Create `src/ui/app.py`
- [x] Input: Company Name, URL, Industry, Country
- [x] Output: Tabbed report viewer (Summary, Financials, Market, etc.)
- [x] Session state for research history
- [x] Export to Markdown/JSON
- [x] Error handling with retry button
