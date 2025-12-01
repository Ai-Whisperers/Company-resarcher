# Technology Stack

This document outlines the core technologies used in the **Company Researcher System**, what we use them for, and why they were chosen.

## Core Framework

### **Python 3.10+**

- **Use**: Primary programming language.
- **Why**: Extensive ecosystem for AI/ML, excellent async support, and strong typing capabilities.

### **FastAPI**

- **Use**: REST API framework for the backend.
- **Why**:
  - **Performance**: Built on Starlette and Pydantic, making it one of the fastest Python frameworks.
  - **Async Support**: Native support for asynchronous programming, essential for our I/O-bound research tasks.
  - **Auto-Documentation**: Automatically generates OpenAPI (Swagger) documentation.

### **Pydantic**

- **Use**: Data validation, settings management, and serialization.
- **Why**: Ensures type safety and data integrity across the application. Its integration with FastAPI and AI libraries is seamless.

## AI & Agents

### **LangChain & LangGraph**

- **Use**: Building blocks for agents and stateful multi-agent workflows.
- **Why**:
  - **LangChain**: Provides standard interfaces for LLMs, prompts, and tools.
  - **LangGraph**: Enables the creation of cyclic, stateful graphs for complex agent interactions (though we are moving towards a custom Pipeline architecture for the core orchestrator to improve testability).

### **OpenAI / Anthropic / Gemini APIs**

- **Use**: Large Language Models (LLMs) for reasoning, analysis, and content generation.
- **Why**: State-of-the-art performance in reasoning and context handling. We support multiple providers for redundancy and specific strengths (e.g., Claude for large context, GPT-4 for reasoning).

## Web Scraping & Research

### **Playwright**

- **Use**: Headless browser automation for fetching web pages.
- **Why**:
  - **Reliability**: Handles modern, dynamic JavaScript-heavy websites better than Requests or Selenium.
  - **Anti-Bot**: easier to configure to mimic real user behavior.
  - **Async**: Native async API fits perfectly with our architecture.

### **BeautifulSoup4**

- **Use**: Parsing HTML content.
- **Why**: Robust and forgiving parser for extracting data from messy HTML.

### **Tavily API**

- **Use**: AI-optimized search engine.
- **Why**: Returns clean, parsed content specifically designed for LLM consumption, reducing the need for raw scraping in initial discovery phases.

## Data & Storage

### **PostgreSQL (via AsyncPG & SQLAlchemy)**

- **Use**: Persistent storage for research tasks, results, and logs.
- **Why**:
  - **Reliability**: ACID compliance and robust data integrity.
  - **AsyncPG**: High-performance async driver.
  - **SQLAlchemy**: Powerful ORM for managing database interactions.

### **Redis**

- **Use**: Caching AI responses and search results.
- **Why**: In-memory speed reduces costs and latency by caching expensive API calls.

## Utilities

### **Jinja2**

- **Use**: Templating engine for generating Markdown reports.
- **Why**: Allows for strict separation of logic and presentation, ensuring consistent report formatting.

### **Tenacity**

- **Use**: Retrying failing operations (API calls, network requests).
- **Why**: Essential for building resilient systems that interact with unreliable external services.

### **Pytest**

- **Use**: Testing framework.
- **Why**: Powerful fixture system and ease of use for writing unit, integration, and async tests.
