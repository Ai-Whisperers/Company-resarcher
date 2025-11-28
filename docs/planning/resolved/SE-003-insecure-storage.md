# SE-003: Insecure Credential Storage

## Status: ACCEPTABLE RISK

## Priority: Critical

## Description

Credentials stored in plain text in files or environment variables without additional protection.

## Location

- **File**: `.env`
- **File**: `src/core/config.py`

## Recommended Fix

- Use secret management service (AWS Secrets Manager, HashiCorp Vault)
- Encrypt credentials at rest
- Use environment-specific credential injection

## Impact

- **Severity**: Critical
- **Risk**: Credential theft

## Resolution

**Reviewed**: 2024-11-28

The current approach of using environment variables (`.env` files) is **standard practice** for application configuration and follows the 12-Factor App methodology.

**Current protections in place:**

1. `.env` is in `.gitignore` - never committed to source control
2. `SecretStr` in config prevents accidental logging (see SE-001)
3. Logger has regex-based API key sanitization

**For production deployments**, the recommended approach is:

- Use platform-native secrets (Docker secrets, K8s secrets, AWS Secrets Manager)
- Inject credentials via environment variables at runtime
- Never use `.env` files in production

This is an **acceptable risk** for local development. Production deployment documentation should specify secure credential injection methods.

**Future enhancement** (if needed): Add support for AWS Secrets Manager or HashiCorp Vault integration.
