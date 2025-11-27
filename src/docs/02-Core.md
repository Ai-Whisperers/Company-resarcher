# Core Module Documentation

This module contains the foundational utilities, types, and configurations used throughout the system.

## 1. AI Client (`src/core/ai_client.py`)

Handles interactions with various LLM providers (OpenAI, Anthropic, Gemini, Groq).

### Class: `BaseAIClient` (Abstract)

- **`generate(self, prompt: str, ...) -> str`**: Abstract method for text generation.

### Class: `OpenAIClient` / `AnthropicClient` / `GeminiClient`

- Implementations of `BaseAIClient` for specific providers.
- **`__init__(self, api_key: str, model: str)`**: Initializes the provider SDK.
- **`generate(...)`**: Sends the prompt to the API and returns the response string.

---

## 2. Research Phases (`src/core/research_phases.py`)

Defines the structure of the research process.

### Constant: `RESEARCH_PHASES`

A list of dictionaries defining each phase, its sub-phases, and the specific queries to run.

Example Structure:

```python
{
    "name": "Market Intelligence",
    "sub_phases": [
        {
            "name": "Market Size & Growth",
            "queries": ["{industry} market size {country}", ...]
        }
    ]
}
```

---

## 3. Configuration (`src/core/config.py`)

Manages environment variables and application settings.

- **`load_config()`**: Loads `.env` file.
- **`Config` Class**: Pydantic model or class holding keys like `OPENAI_API_KEY`, `TAVILY_API_KEY`.

---

## 4. Logger (`src/core/logger.py`)

Centralized logging configuration.

- **`setup_logger(name: str) -> logging.Logger`**: Returns a configured logger with colored console output and file logging (`research.log`).

---

## 5. Types (`src/core/types.py`)

Pydantic models for type safety.

- **`CompanyProfile`**: `name`, `industry`, `country`, `url`.
- **`ResearchSource`**: `url`, `title`, `content`, `source_type`.
- **`ResearchPhaseResult`**: `phase_name`, `markdown_content`, `sources`.

---

## 6. Template Renderer (`src/core/template_renderer.py`)

Helper for Jinja2 template rendering.

- **`render_template(template_name: str, context: Dict) -> str`**: Renders a markdown template with the provided data.
