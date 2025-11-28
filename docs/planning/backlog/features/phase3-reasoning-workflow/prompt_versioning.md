# Feature: Prompt Versioning

## Source

- **Repository:** `langgenius/dify`
- **File:** `api/core/prompt`

## Description

Prompts are code. They should be versioned, tracked, and easily rolled back.

## Implementation Details

1.  **Storage:** Store prompts in a database or Git-backed folder structure (e.g., `prompts/v1/researcher.txt`).
2.  **Metadata:** Track `author`, `created_at`, `model_config` (temp, top_p).
3.  **Comparison:** UI to diff two versions of a prompt.

## Code Reference

```python
def get_prompt(name, version="latest"):
    return db.query("SELECT content FROM prompts WHERE name=? AND version=?", name, version)
```
