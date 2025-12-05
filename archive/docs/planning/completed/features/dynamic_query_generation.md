# Feature: Dynamic Query Generation

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/skills/deep_research.py` (`generate_search_queries`)

## Description

Instead of just using the user's prompt as the search query, the agent should generate multiple, specific SERP queries to cover different angles.

## Implementation Details

1.  **Prompt:** "Given the topic '{topic}', generate {n} search queries to research it thoroughly."
2.  **Diversity:** Instruct the LLM to cover different aspects (e.g., "History", "Current State", "Future Outlook").
3.  **Format:** Parse the LLM output (e.g., JSON list or line-separated) to get clean query strings.

## Code Reference

```python
async def generate_search_queries(query, n=3):
    prompt = f"Generate {n} google search queries for: {query}"
    response = await llm.generate(prompt)
    return parse_list(response)
```
