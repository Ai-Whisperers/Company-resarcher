# Feature: Smart Context Trimming

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/skills/deep_research.py`

## Description

As research accumulates, the context size grows rapidly. We need an algorithm to trim the context to fit within the LLM's token limit (e.g., 128k tokens) while preserving the most relevant and recent information.

## Implementation Details

1.  **Token/Word Counting:** Use a fast tokenizer or simple word count approximation (1 token ≈ 0.75 words).
2.  **Trimming Strategy:**
    - Keep the **System Prompt** and **Current Query** (High priority).
    - Keep the **most recent** learnings/results.
    - Trim older results if limit is exceeded.
    - Optionally, summarize older results instead of dropping them.
3.  **Safety Margin:** Always leave a buffer (e.g., 4k tokens) for the LLM's response.

## Code Reference

```python
MAX_WORDS = 25000
def trim_context(context_list):
    total_words = 0
    trimmed = []
    for item in reversed(context_list): # Keep most recent
        words = len(item.split())
        if total_words + words < MAX_WORDS:
            trimmed.insert(0, item)
            total_words += words
    return trimmed
```
