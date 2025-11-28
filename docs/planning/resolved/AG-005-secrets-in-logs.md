# AG-005: Secrets Potentially Exposed in Logs

**Priority**: Critical
**Effort**: Medium (1-3 days)
**Type**: Security

## Problem

Agent code may log sensitive information including API keys, user data, or internal prompts:

```python
# Various locations log full prompts which may contain sensitive data
logger.info(f"Generating response for prompt: {prompt}")
logger.error(f"Failed with data: {company_data}")
```

## Locations

- `src/agents/base_agent.py` - prompt logging
- `src/agents/deep_research.py` - query logging
- `src/core/ai_client.py` - response logging
- Various exception handlers that log full context

## Impact

1. **API key exposure**: Keys could end up in log files
2. **PII leakage**: User/company data in logs
3. **Compliance violations**: GDPR, SOC2 requirements
4. **Attack surface**: Logs accessible to attackers

## Recommended Fix

1. Create a log sanitization utility:

```python
def sanitize_for_logging(data: str, max_length: int = 100) -> str:
    """Truncate and redact sensitive patterns."""
    # Redact API keys
    sanitized = re.sub(r'(sk-|api_key["\s:=]+)[a-zA-Z0-9-]+', r'\1[REDACTED]', data)
    # Truncate
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    return sanitized
```

2. Use structured logging with explicit field selection
3. Never log full prompts or responses in production

## Acceptance Criteria

- [ ] Log sanitization utility created
- [ ] All sensitive logging calls updated
- [ ] Log levels appropriate (DEBUG for verbose, INFO for production)
- [ ] Security audit of log statements
- [ ] Documentation on logging best practices
