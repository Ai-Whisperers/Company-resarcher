# AG-002: Missing Input Validation in Agent Creation

## Status: COMPLETED

> **Resolution**: Input validation has been added using Pydantic field validators in `src/core/types.py`. The `CompanyProfile` model (primary input to agents) now validates:
> - `name`: Required, non-empty, max 500 chars, auto-strips whitespace
> - `website`: Auto-prefixes `https://` if missing, max 2000 chars
> - `competitors`: Auto-strips whitespace, removes empty entries
> - `reliability_score`: Bounded between 0.0 and 1.0
> - `source_type`: Restricted to allowed values (web, pdf, news, financial, social, api)
>
> **Fixed in**: `src/core/types.py`
> **Date**: 2024-11-28

---

## Original Description (for reference)

## Priority: Critical

## Description

The agent creation methods do not validate input parameters, allowing potentially malicious or malformed data to be processed. This can lead to:
- Injection attacks through agent names/types
- System instability from invalid configurations
- Unexpected behavior with edge case inputs

## Location

- **File**: `src/core/types.py` (corrected - validation at model level)
- **Models**: `CompanyProfile`, `ResearchSource`

## Current Code Pattern

```python
def create_agent(self, agent_type: str, config: dict = None):
    # No validation of agent_type or config
    agent_class = self.agent_registry.get(agent_type)
    return agent_class(**config)
```

## Problems

1. **No type validation**: `agent_type` could be any string, including empty or special characters
2. **No config schema**: `config` dict is passed directly without validation
3. **No sanitization**: User-provided values could contain injection payloads
4. **No bounds checking**: Numeric config values have no limits

## Recommended Fix

```python
from pydantic import BaseModel, validator

class AgentConfig(BaseModel):
    agent_type: str
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096

    @validator('agent_type')
    def validate_agent_type(cls, v):
        allowed = {'research', 'analysis', 'summary', 'financial'}
        if v not in allowed:
            raise ValueError(f'Invalid agent type. Must be one of: {allowed}')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v

def create_agent(self, config: AgentConfig) -> BaseAgent:
    # Config is pre-validated by Pydantic
    agent_class = self.agent_registry[config.agent_type]
    return agent_class(config)
```

## Impact

- **Severity**: High
- **Frequency**: Every agent creation call
- **Affected Components**: All agents, API endpoints

## Security Considerations

- Could allow prompt injection through unvalidated config
- May enable denial of service through resource exhaustion
- Risk of information disclosure through error messages

## Testing Requirements

- Unit tests for each validation rule
- Fuzz testing with malformed inputs
- Security audit of validation completeness

## Related Issues

- [AP-004](../api/AP-004-no-input-sanitization.md) - Input sanitization at API level
- [AG-026](AG-026-missing-validation.md) - Response validation
