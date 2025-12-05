# Scrapegraph-AI Integration Guide

## 1. Use Cases

Scrapegraph-AI uses LLMs to define scraping logic, replacing brittle CSS/XPath selectors.

- **Complex Extraction**: "Get the pricing table" works even if the table ID changes.
- **Unstructured Data**: Converting free-form text on a page into JSON.
- **Resilience**: The scraper adapts to UI changes automatically.

## 2. Implementation Strategy

We should add a `SmartScraperTool` to our toolkit.

### Setup

1.  Install: `pip install scrapegraphai`
2.  Configure with our existing LLM (OpenAI/Anthropic).

### Usage Pattern

Instead of writing custom parsing logic in `BeautifulSoup`:

```python
from scrapegraphai.graphs import SmartScraperGraph

def scrape_smart(url: str, prompt: str):
    graph = SmartScraperGraph(
        prompt=prompt,
        source=url,
        config={"llm": {"model": "openai/gpt-4o", "api_key": ...}}
    )
    return graph.run()
```

## 3. Integration with Stack

- **LangChain**: Can be wrapped as a custom Tool for our agents.
- **Cost Management**: Since it uses LLMs for scraping, it is more expensive than `BeautifulSoup`. Use it only when deterministic parsing fails (fallback mechanism).
