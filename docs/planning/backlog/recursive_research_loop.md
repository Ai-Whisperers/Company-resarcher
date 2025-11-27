# Feature: Recursive Research Loop

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/skills/deep_research.py`

## Status

**Implemented** in `src/agents/deep_research.py`.

## Description

Implement a recursive "Breadth vs. Depth" research loop. The agent should start with a broad query, generate sub-queries (Breadth), process them, and then recursively dive deeper into interesting findings (Depth) by generating new queries based on previous learnings.

## Implementation Details

1.  **Parameters:**
    - `breadth` (int): Number of parallel queries to generate at each level.
    - `depth` (int): How many levels deep to go.
2.  **Logic:**
    - Start with `current_depth = 1`.
    - Generate `breadth` search queries using an LLM.
    - For each query:
      - Search & Scrape.
      - Extract "Learnings" and "Follow-up Questions".
    - If `current_depth < depth`:
      - Use "Follow-up Questions" to generate the next set of queries.
      - Recurse with `depth - 1`.
3.  **Accumulation:**
    - Maintain a global list of `learnings` and `visited_urls` to avoid duplication.

## Code Reference (Python)

```python
async def deep_research(query, breadth, depth, learnings=[]):
    if depth <= 0: return learnings

    queries = generate_serp_queries(query, breadth)
    results = await process_concurrently(queries)

    new_learnings = extract_learnings(results)
    learnings.extend(new_learnings)

    next_query = generate_next_query(results)
    return await deep_research(next_query, breadth, depth-1, learnings)
```
