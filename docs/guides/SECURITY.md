# Security Guide

Security best practices and recommendations for Company Researcher.

## Overview

Company Researcher handles sensitive data including:
- API keys for LLM providers
- Company research data
- User request information

This guide covers how to protect this data and secure your deployment.

---

## API Key Management

### Storage Recommendations

| Environment | Recommendation |
|-------------|----------------|
| Development | `.env` file (gitignored) |
| CI/CD | GitHub Secrets / GitLab Variables |
| Production | Secrets Manager (AWS, GCP, Azure, Vault) |

### Never Do This

```bash
# WRONG - Don't commit API keys
git add .env
git commit -m "Add config"  # API keys exposed!

# WRONG - Don't hardcode in code
OPENAI_API_KEY = "sk-abc123..."  # Exposed in repo!

# WRONG - Don't log API keys
logger.info(f"Using key: {api_key}")  # Exposed in logs!
```

### Best Practices

```python
# CORRECT - Load from environment
import os
api_key = os.getenv("OPENAI_API_KEY")

# CORRECT - Validate without exposing
if not api_key:
    raise ValueError("OPENAI_API_KEY not configured")

# CORRECT - Mask in logs
logger.info(f"API key configured: {api_key[:8]}...")
```

### Key Rotation

1. Generate new API key in provider dashboard
2. Update in secrets manager
3. Deploy new configuration
4. Verify functionality
5. Revoke old key

---

## API Security

### Current Security Features

| Feature | Status | Description |
|---------|--------|-------------|
| Rate Limiting | ✅ Enabled | 10 req/min per IP |
| Request Size Limit | ✅ Enabled | 1MB max body |
| CORS | ✅ Configurable | Restrict allowed origins |
| HTTPS | ⚠️ External | Configure at load balancer |
| Authentication | ❌ Not implemented | Add for production |

### Rate Limiting

Built-in rate limiting prevents abuse:

```python
# Current implementation: 10 requests per minute per IP
# Configurable via environment or code

# Returns 429 Too Many Requests when exceeded
{
    "detail": "Too many requests. Please try again later."
}
```

### CORS Configuration

```env
# Restrict to specific origins in production
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# NEVER use in production:
# CORS_ORIGINS=*
```

### Adding Authentication

For production, consider adding authentication:

```python
# Example: API Key authentication
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/api/v1/research")
async def start_research(
    request: ResearchRequest,
    api_key: str = Security(verify_api_key)
):
    # ... authenticated endpoint
```

---

## Data Security

### Sensitive Data Handling

| Data Type | Handling |
|-----------|----------|
| API Keys | Never log, mask in errors |
| Research Results | Store securely, consider encryption |
| User Input | Validate and sanitize |
| Source URLs | Log for audit, no credentials |

### Input Validation

All inputs are validated via Pydantic:

```python
class ResearchRequest(BaseModel):
    company_name: str = Field(
        min_length=1,
        max_length=200,
    )
    url: Optional[HttpUrl] = None  # Validates URL format
```

### Logging Security

```python
# GOOD - Sanitized logging
logger.info(f"Starting research for: {company_name}")

# BAD - Don't log sensitive data
logger.debug(f"Full request: {request}")  # May contain sensitive info

# GOOD - Structured logging without secrets
logger.info("API call", extra={
    "provider": "openai",
    "model": "gpt-4o",
    "tokens": 1500
})
```

### Database Security

```env
# Use strong passwords
DATABASE_URL=postgresql://user:STRONG_PASSWORD@host:5432/db

# Enable SSL for remote databases
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

---

## Browser/Scraping Security

### Playwright Security

The browser tool uses Playwright with security considerations:

```python
# Headless mode (no visible browser)
browser = await playwright.chromium.launch(headless=True)

# Isolated context per request
context = await browser.new_context()

# Close context after use
await context.close()
```

### User Agent

```python
# Configurable user agent
USER_AGENT = os.getenv(
    "BROWSER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)
```

### Cookie Handling

- Cookies are not persisted between requests
- Each research task gets fresh browser context
- No authentication cookies are stored

---

## Production Hardening

### Checklist

```markdown
## Pre-Deployment Security Checklist

### Secrets Management
- [ ] API keys in secrets manager (not .env)
- [ ] Database credentials rotated
- [ ] No secrets in code or logs

### Network Security
- [ ] HTTPS enforced (TLS 1.2+)
- [ ] CORS restricted to known origins
- [ ] Rate limiting enabled
- [ ] Firewall rules configured

### Application Security
- [ ] Debug mode disabled
- [ ] Error messages sanitized
- [ ] Input validation enabled
- [ ] Dependencies updated

### Infrastructure
- [ ] Non-root container user
- [ ] Read-only filesystem where possible
- [ ] Resource limits configured
- [ ] Network isolation (VPC)

### Monitoring
- [ ] Security logging enabled
- [ ] Alerting on suspicious activity
- [ ] Regular security scans
```

### Disable Debug Mode

```python
# Production settings
DEBUG = False
LOG_LEVEL = "INFO"  # Not DEBUG

# FastAPI production
app = FastAPI(
    debug=False,
    docs_url=None,  # Disable Swagger in production
    redoc_url=None,
)
```

### Error Message Sanitization

```python
# GOOD - Generic error for users
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Internal error: {exc}")  # Full error in logs
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"}  # Generic to user
    )

# BAD - Don't expose internal details
return JSONResponse(
    content={"detail": str(exc)}  # Exposes stack trace!
)
```

---

## Dependency Security

### Keeping Dependencies Updated

```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade -r requirements.txt

# Use pip-audit for security scanning
pip install pip-audit
pip-audit
```

### Dependency Pinning

```txt
# requirements.txt - Pin versions for reproducibility
fastapi==0.104.1
pydantic==2.5.2
langchain==0.1.0

# Or use ranges for security updates
fastapi>=0.104.1,<0.105.0
```

---

## Incident Response

### If API Keys Are Exposed

1. **Immediately** revoke the exposed key
2. Generate new key
3. Update all deployments
4. Audit logs for unauthorized usage
5. Check for unexpected charges

### If Data Is Breached

1. Identify scope of breach
2. Contain the incident
3. Notify affected parties
4. Document timeline
5. Implement preventive measures

### Security Contacts

For security issues:
- Report via GitHub Security Advisories
- Email: security@example.com (update with actual contact)

---

## Compliance Considerations

### Data Retention

- Research results stored until manually deleted
- Consider implementing automatic cleanup
- Document retention policies

### Privacy

- No PII collection by default
- Company research is publicly available data
- Consider GDPR compliance for EU users

### Audit Logging

```python
# Log security-relevant events
logger.info("Research started", extra={
    "task_id": task_id,
    "company": company_name,
    "user_ip": request.client.host,
    "timestamp": datetime.utcnow().isoformat()
})
```

---

## Security Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.org/dev/security/)
