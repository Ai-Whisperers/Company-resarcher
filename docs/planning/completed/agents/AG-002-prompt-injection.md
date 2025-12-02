# AG-002: Prompt Injection Vulnerabilities

**Priority**: Critical
**Effort**: Medium (1-3 days)
**Type**: Security

## Problem

Multiple agents use f-string formatting with unsanitized user input in prompts, creating potential for prompt injection attacks:

```python
# critic.py:36
prompt = f"Review the following insights for {company.name}..."

# generic_agent.py:69
prompt = f"Research {company.name} for {phase_config['name']}..."
```

## Locations

- `src/agents/critic.py:36`
- `src/agents/generic_agent.py:69`
- `src/agents/insight_generator.py` - multiple locations
- `src/agents/deep_research.py` - query generation

## Impact

1. **Prompt injection**: Malicious company names could manipulate AI behavior
2. **Data exfiltration**: Crafted inputs could extract system prompts
3. **Bypass controls**: Could circumvent content filtering

## Recommended Fix

1. Sanitize all user inputs before including in prompts:

```python
def sanitize_prompt_input(text: str) -> str:
    """Remove potentially dangerous characters from prompt inputs."""
    # Remove control characters and limit length
    sanitized = ''.join(c for c in text if c.isprintable())
    return sanitized[:500]  # Limit length
```

2. Use parameterized templates instead of f-strings
3. Validate inputs against expected patterns

## Acceptance Criteria

- [ ] Input sanitization function created
- [ ] All prompt inputs sanitized before use
- [ ] Input length limits enforced
- [ ] Unit tests for sanitization
- [ ] Security review completed
