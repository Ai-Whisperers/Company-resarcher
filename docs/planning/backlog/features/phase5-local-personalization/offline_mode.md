# Feature: Offline Mode

## Source

- **Repository:** `khoj-ai/khoj`
- **File:** `src/llm/ollama_client.py`

## Description

Support running entirely offline using local LLMs (like Llama 3 via Ollama) and local embeddings.

## Implementation Details

1.  **LLM Provider:** Add `Ollama` and `LlamaCpp` as providers in `AIClient`.
2.  **Embeddings:** Use `sentence-transformers` locally instead of OpenAI Embeddings.
3.  **Config:** Toggle `--offline` to force local providers.

## Code Reference

```python
if config.offline:
    client = OllamaClient(model="llama3")
else:
    client = OpenAIClient()
```
