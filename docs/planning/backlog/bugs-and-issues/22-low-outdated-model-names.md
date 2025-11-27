# LOW: Outdated Model Names

## Severity: Low
## File: `src/core/config.py` (lines 20-26)

## Problem

Default model configurations use outdated or deprecated model names:

```python
openai: Optional[AIProviderConfig] = AIProviderConfig(model="gpt-4-turbo-preview")
anthropic: Optional[AIProviderConfig] = AIProviderConfig(model="claude-3-opus-20240229")
gemini: Optional[AIProviderConfig] = AIProviderConfig(model="gemini-1.5-pro-latest")
```

## Impact

- `gpt-4-turbo-preview` is deprecated
- Model names may become invalid
- Not using latest/best models

## Solution

Update to current model names:

```python
class AIConfig(BaseModel):
    primary: Literal["openai", "anthropic", "gemini", "groq", "ollama"] = "openai"
    fallback: Optional[Literal["openai", "anthropic", "gemini", "groq", "ollama"]] = None

    openai: Optional[AIProviderConfig] = AIProviderConfig(model="gpt-4o")
    anthropic: Optional[AIProviderConfig] = AIProviderConfig(model="claude-sonnet-4-20250514")
    gemini: Optional[AIProviderConfig] = AIProviderConfig(model="gemini-2.0-flash")
    groq: Optional[AIProviderConfig] = AIProviderConfig(model="llama-3.3-70b-versatile")
    ollama: Optional[AIProviderConfig] = AIProviderConfig(model="llama3.2")
```

Note: Model names change frequently. Consider:
1. Making this easily configurable
2. Adding model validation
3. Documenting which models are tested

## Testing

After fix:
1. Run with default configuration
2. Verify no model deprecation warnings
3. Verify API calls succeed
