# Critical Backlog Items

## High Priority / Critical

### ~~[CRITICAL] Fix Windows Unicode Encoding Issues~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/critical/CRIT-001-windows-unicode.md`
> **Implementation:** `src/core/logger.py` (SafeStreamHandler, _configure_windows_encoding)

### ~~[CRITICAL] Implement Rate Limiting for Search APIs~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/critical/CRIT-002-rate-limiting.md`
> **Implementation:** `src/core/rate_limited_client.py` (AsyncLimiter with minute/hour limits)

### ~~[CRITICAL] Secure Path Traversal in OutputManager~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/critical/CRIT-003-path-traversal.md`
> **Implementation:** `src/core/output_manager.py` (comprehensive security with pattern detection)
