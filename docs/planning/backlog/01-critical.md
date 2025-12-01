# Critical Backlog Items

## High Priority / Critical

### [CRITICAL] Fix Windows Unicode Encoding Issues

**Priority:** Critical
**Description:** The system forces UTF-8 encoding for stdout/stderr in `main.py` to handle non-ASCII characters on Windows. This is a patch. We need a more robust cross-platform solution that doesn't rely on modifying `sys.stdout`.
**Acceptance Criteria:**

- [ ] Remove `sys.stdout` modification in `main.py`.
- [ ] Implement a custom logger handler that handles encoding gracefully.
- [ ] Verify output on Windows (PowerShell/CMD) and Linux.
      **Technical Notes:**
- File: `main.py`
- Issue: `UnicodeEncodeError` when printing emojis or non-ASCII text on Windows consoles.

### [CRITICAL] Implement Rate Limiting for Search APIs

**Priority:** Critical
**Description:** The `SearchTool` currently has a basic `try/except` block but no proper rate limiting. We need to use `aiolimiter` (already in requirements) to respect API limits for Tavily, Serper, etc.
**Acceptance Criteria:**

- [ ] Implement `AsyncLimiter` in `SearchManager`.
- [ ] Configure limits per provider (e.g., Tavily: 100 req/min).
- [ ] Handle `429 Too Many Requests` errors with exponential backoff.
      **Technical Notes:**
- File: `src/tools/search/manager.py`
- Library: `aiolimiter`

### [CRITICAL] Secure Path Traversal in OutputManager

**Priority:** High
**Description:** While `OutputManager` has some validation, we need to ensure it's robust against all forms of traversal attacks, especially when dealing with user-provided company names.
**Acceptance Criteria:**

- [ ] Add comprehensive unit tests for `_validate_path` with various attack vectors.
- [ ] Ensure `company_name` is strictly sanitized (alphanumeric only recommended).
      **Technical Notes:**
- File: `src/core/output_manager.py`
