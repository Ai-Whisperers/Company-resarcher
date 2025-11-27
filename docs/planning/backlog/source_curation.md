# Feature: Source Curation

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/prompts.py` (`curate_sources`)

## Status

**Implemented** in `src/agents/deep_research.py` (Relevance Scoring).

## Description

Not all search results are equal. The agent should evaluate scraped URLs and filter them based on credibility, relevance, and content quality before adding them to the context.

## Implementation Details

1.  **LLM Evaluation:** Use a specific prompt to ask the LLM to rate/filter sources.
2.  **Criteria:**
    - **Relevance:** Does it answer the query?
    - **Credibility:** Is it a known domain (e.g., `.gov`, `.edu`, major news)?
    - **Data Richness:** Does it contain stats/numbers?
3.  **Blacklist:** Maintain a `blacklist.txt` of low-quality domains (SEO spam, content farms).

## Prompt Example

```text
Evaluate the following sources for the query "{query}".
Return only sources that are highly relevant and credible.
Prioritize sources with statistical data.
```
