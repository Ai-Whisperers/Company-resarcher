# Tool Use Pattern

## 📖 Overview

The Tool Use pattern extends LLM capabilities by enabling interaction with external tools, APIs, and resources to gather information or perform specific actions.

## 🎯 Core Concept

LLMs decide when and how to use external tools:

- Web search engines
- APIs (REST, GraphQL)
- Code execution environments
- Databases
- Specialized algorithms

## 💡 Key Benefits

- **Extended Capabilities**: Beyond text generation
- **Real-Time Data**: Access current information
- **Specialized Computation**: Use domain-specific tools
- **Action Execution**: Perform real-world tasks

## 🏗️ Implementation in Marketing Agent

### Locations

- `code/api/services/research_service.py` - Web research
- `code/api/services/web_fetcher.py` - Content fetching
- `code/api/services/web_search.py` - Tavily search

### Tools Used

| Tool               | Purpose            | Implementation           |
| ------------------ | ------------------ | ------------------------ |
| **Tavily API**     | Web search         | `web_search.py`          |
| **GPT Researcher** | Deep research      | `research_automation.py` |
| **Web Scraper**    | Content extraction | `web_fetcher.py`         |
| **Veo 3.1 API**    | Video generation   | `video_service.py`       |

### Example Implementation

```python
async def research_with_tools(query: str):
    # Decide which tool to use
    if needs_web_search(query):
        # Use Tavily for web search
        results = await tavily.search(query)

    if needs_deep_research(query):
        # Use GPT Researcher
        report = await gpt_researcher.research(query)

    if needs_content(url):
        # Use web fetcher
        content = await web_fetcher.fetch(url)

    return synthesize_results(results, report, content)
```

## 📊 Tool Selection Strategy

```python
def select_tool(task_type: str) -> Tool:
    tool_map = {
        "web_search": TavilySearch(),
        "deep_research": GPTResearcher(),
        "content_fetch": WebFetcher(),
        "video_gen": VeoAPI(),
        "code_exec": CodeInterpreter()
    }
    return tool_map.get(task_type)
```

## 🎓 Best Practices

### Do's ✅

- **Validate Tool Output**: Check for errors
- **Handle Failures**: Graceful degradation
- **Cache Results**: Avoid redundant calls
- **Rate Limiting**: Respect API limits
- **Cost Tracking**: Monitor API usage

### Don'ts ❌

- **Don't Trust Blindly**: Validate all tool outputs
- **Don't Ignore Errors**: Handle failures properly
- **Don't Over-Use**: Tools have costs
- **Don't Skip Auth**: Secure API keys

## 🔬 Research Foundations

**Key Papers**:

- Toolformer (Meta, 2023)
- ReAct (Yao et al., 2022)
- WebGPT (OpenAI, 2021)

## 🚀 Current Tools

### Research Tools

- ✅ Tavily Search API
- ✅ GPT Researcher
- ✅ Web Content Fetcher

### Generation Tools

- ✅ Veo 3.1 (Video)
- 🟡 Image Generation (Planned)

### Data Tools

- ✅ File Operations
- ✅ YAML/JSON Parsing
- ❌ Database (Removed)

---

**Pattern Type**: Core (Andrew Ng)  
**Difficulty**: Medium  
**Impact**: High  
**Status**: ✅ Fully Implemented
