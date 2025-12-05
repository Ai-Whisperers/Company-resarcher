# INT-004: LiteLLM Multi-Provider Support

## Problem Statement

We are currently locked into specific LLM providers (e.g., OpenAI or Gemini) in different parts of the code. We need a unified interface to switch between providers easily.

## Proposed Solution

Integrate `LiteLLM` as the standard interface for all LLM calls. This allows us to use OpenAI, Anthropic, Gemini, Groq, or Ollama by simply changing a configuration string.

## Implementation Steps

1.  Install `litellm`.
2.  Create a `LLMService` wrapper around `litellm.completion`.
3.  Update all agents and extractors to use this service.
4.  Configure models via environment variables.

## Code Example

```python
from litellm import completion

response = completion(
    model="gemini/gemini-pro",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Acceptance Criteria

- [ ] Can switch models (e.g., GPT-4 to Claude 3) via config.
- [ ] Streaming works across providers.
- [ ] Error handling is standardized.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/extraction_strategy.py` (uses LiteLLM concepts)
