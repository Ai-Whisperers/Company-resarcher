# 🔒 Security Improvements

This document outlines security enhancements to protect the application, its data, and its users. These improvements focus on credential management, input validation, abuse prevention, and auditing.

## SEC-1: API Key Rotation (3h)

### Concept & Rationale

Static API keys are a security risk. If a key is compromised, it can be used indefinitely until manually revoked.

**The Improvement:**
Implement an automated **API Key Rotation** system (`APIKeyManager`).

- **Vault Integration:** Store keys securely in a vault (e.g., HashiCorp Vault, AWS Secrets Manager) rather than environment variables or config files.
- **Automated Rotation:** A background task checks key expiration. When a key is near expiration, the system automatically requests a new key from the vault, updates the in-memory configuration, and notifies dependent services.
- **Zero Downtime:** Ensure the rotation process is atomic and does not interrupt active requests.

### Key Implementation Details

- Define a rotation policy (e.g., rotate every 30 days).
- Implement a background loop (`_rotation_loop`) to monitor key validity.
- Reference: `src/core/security/key_rotation.py` (Proposed)

## SEC-2: Input Sanitization (3h)

### Concept & Rationale

Accepting raw user input opens the door to injection attacks (XSS, SQLi, Command Injection) and data corruption.

**The Improvement:**
Implement a rigorous **Input Sanitization** layer (`InputSanitizer`).

- **Sanitization:** Use libraries like `bleach` to strip dangerous HTML tags and scripts from text inputs.
- **Validation:** Use `pydantic` validators to enforce strict rules on input format, length, and content.
- **Pattern Matching:** Explicitly block known dangerous patterns (e.g., `javascript:`, `{{...}}` for template injection).

### Key Implementation Details

- Create a centralized sanitization utility.
- Integrate sanitization directly into Pydantic models so that all API inputs are validated automatically.
- Reference: `src/core/security/sanitizer.py` (Proposed)

## SEC-3: Rate Limiting by User (3h)

### Concept & Rationale

Without per-user rate limiting, a single malicious or buggy user can exhaust the system's resources (API quotas, CPU, DB connections), causing a denial of service for everyone else.

**The Improvement:**
Implement a **Tiered Rate Limiting** system (`UserRateLimiter`) backed by Redis.

- **Granularity:** Limit requests per user, not just globally.
- **Tiers:** Support different limits based on user subscription (e.g., Free: 10 req/min, Pro: 300 req/min).
- **Headers:** Return standard rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`) to let clients know their status.

### Key Implementation Details

- Use Redis atomic increments and expiration for accurate counting.
- Implement as a FastAPI middleware to protect all endpoints.
- Reference: `src/middleware/rate_limit.py` (Proposed)

## SEC-4: Audit Logging (3h)

### Concept & Rationale

For compliance (SOC2, GDPR) and security investigations, you need an immutable record of "who did what and when."

**The Improvement:**
Create a comprehensive **Audit Logging** system (`AuditLogger`).

- **Events:** Log critical actions such as data access (viewing a company report), configuration changes, and API key usage.
- **Details:** Capture the User ID, Action, Resource Type, Resource ID, IP Address, User Agent, and Timestamp.
- **Storage:** Store audit logs in a secure, append-only storage mechanism separate from the main application logs.

### Key Implementation Details

- Create an `AuditEntry` model.
- Implement helper methods (`log_data_access`, `log_api_key_usage`) to make instrumentation easy.
- Reference: `src/core/audit/logger.py` (Proposed)
