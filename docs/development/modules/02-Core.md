# Core Module Documentation

This module contains the foundational utilities, types, and configurations used throughout the system.

## 1. AI Client (`src/core/ai_client.py`)

Handles interactions with various LLM providers (OpenAI, Anthropic, Gemini, Groq, Ollama) and manages fallbacks.

### Class: `AIClientManager`

- **`__init__(self)`**: Initializes clients based on configuration settings.
- **`get_client_for_task(self, task_type)`**: Returns the appropriate client (primary or fallback) for a specific task.
- **`generate(self, prompt, ...)`**: Delegates generation to the selected client.

### Class: `BaseAIClient` (Abstract)

- **`generate(self, prompt: str, ...) -> str`**: Abstract method for text generation.
- **Implementations**: `OpenAIClient`, `AnthropicClient`, `GeminiClient`, `GroqClient`, `OllamaClient`, `MockAIClient`.

---

## 2. Research Phases (`src/core/research_phases.py`)

Defines the structure of the research process using the V2 Research Schema.

### Constant: `RESEARCH_PHASES`

A dictionary defining each phase, its sub-phases, and the specific queries to run.

**Example Structure:**

```python
"01-Market-Intelligence/01-Market-Size-Growth": {
    "name": "Market Size & Growth",
    "description": "TAM/SAM/SOM, CAGR, financial projections",
    "query_templates": [
        "{industry} market size {country} 2024 2025",
        "{industry} industry growth rate {country} CAGR",
    ],
    "min_sources": 4,
    "priority": 3,
}
```

---

## 3. Configuration (`src/core/config.py`)

Manages environment variables and application settings using Pydantic.

### Class: `Settings`

- **`profile`**: Development, Staging, or Production.
- **API Keys**: `OPENAI_API_KEY`, `TAVILY_API_KEY`, etc.
- **AI Settings**: Model selection for each provider.

---

## 4. Logger (`src/core/logger.py`)

Centralized logging configuration.

- **`setup_logger(name: str) -> logging.Logger`**: Returns a configured logger with colored console output and file logging (`research.log`).

---

## 5. Types (`src/core/types.py`)

Pydantic models for type safety and validation.

- **`CompanyProfile`**: Stores company details (`name`, `website`, `industry`, `country`). Includes validation and enrichment methods.
- **`ResearchSource`**: Represents a data source (`url`, `title`, `content`). Includes methods to check if a source is usable or relevant.
- **`ResearchPhaseResult`**: The output of a research phase, containing markdown content and sources.
- **`FullCompanyResearch`**: The complete research dossier.

---

## 6. Template Renderer (`src/core/template_renderer.py`)

Helper for Jinja2 template rendering.

- **`render_template(template_name: str, context: Dict) -> str`**: Renders a markdown template with the provided data.
