# Setup Guide

This guide covers everything you need to get Company Researcher running on your machine.

## Prerequisites

### Required

- **Python 3.10+** - Check with `python --version`
- **pip** - Python package manager
- **Git** - For cloning the repository

### Optional (for full functionality)

- **Redis** - For response caching (improves performance)
- **PostgreSQL** - For production database (SQLite used by default)
- **Docker** - For containerized deployment

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Ai-Whisperers/Company-resarcher.git
cd Company-resarcher

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web scraping)
playwright install chromium

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Run a test research
python main.py --name "Apple" --industry "Technology"
```

## Environment Configuration

Create a `.env` file in the project root with your configuration.

### Minimal Configuration

```env
# At least one AI provider is required
OPENAI_API_KEY=sk-your-openai-key

# Search API (required for web search)
TAVILY_API_KEY=tvly-your-tavily-key
```

### Full Configuration

```env
# ===========================================
# AI PROVIDERS (at least one required)
# ===========================================

# OpenAI (recommended for best results)
OPENAI_API_KEY=sk-your-openai-key

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Google Gemini
GEMINI_API_KEY=your-gemini-key

# Groq (fast, free tier available)
GROQ_API_KEY=gsk_your-groq-key

# Ollama (local, free - no key needed)
# Just ensure Ollama server is running at http://localhost:11434

# ===========================================
# SEARCH & DATA APIS
# ===========================================

# Tavily (primary search - required)
TAVILY_API_KEY=tvly-your-tavily-key

# NewsAPI (for news aggregation - optional)
NEWSAPI_KEY=your-newsapi-key

# SerpAPI (alternative search - optional)
SERPAPI_API_KEY=your-serpapi-key

# ===========================================
# OBSERVABILITY (optional)
# ===========================================

# Langfuse (for monitoring/tracing)
LANGFUSE_PUBLIC_KEY=pk-your-key
LANGFUSE_SECRET_KEY=sk-your-key
LANGFUSE_HOST=https://cloud.langfuse.com

# ===========================================
# API CONFIGURATION
# ===========================================

# CORS allowed origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Maximum request body size in bytes
MAX_REQUEST_SIZE_BYTES=1000000

# Research task timeout in seconds (default: 30 minutes)
RESEARCH_TIMEOUT_SECONDS=1800

# ===========================================
# DATABASE
# ===========================================

# Database URL (SQLite is default)
# DATABASE_URL=sqlite:///./tasks.db

# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/company_researcher

# ===========================================
# OUTPUT
# ===========================================

# Custom output directory (default: ./output)
# OUTPUT_DIR=/path/to/custom/output
```

## LLM Provider Setup

### OpenAI

1. Create an account at [platform.openai.com](https://platform.openai.com)
2. Generate an API key in Settings > API Keys
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

**Models used**: `gpt-4o` (default)

### Anthropic

1. Create an account at [console.anthropic.com](https://console.anthropic.com)
2. Generate an API key
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

**Models used**: `claude-sonnet-4-20250514`

### Google Gemini

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env`: `GEMINI_API_KEY=...`

**Models used**: `gemini-2.0-flash`

### Groq

1. Create an account at [console.groq.com](https://console.groq.com)
2. Generate an API key
3. Add to `.env`: `GROQ_API_KEY=gsk_...`

**Models used**: `llama-3.1-8b-instant`

### Ollama (Local, Free)

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama server: `ollama serve`
3. Pull a model: `ollama pull llama3.1:8b`
4. No API key needed - just ensure server is running

**Models used**: `llama3.1:8b`

## Search API Setup

### Tavily (Recommended)

1. Sign up at [tavily.com](https://tavily.com)
2. Get your API key from the dashboard
3. Add to `.env`: `TAVILY_API_KEY=tvly-...`

**Free tier**: 1,000 searches/month

### DuckDuckGo (Fallback)

No API key required. Used automatically when Tavily is unavailable.

## Playwright Browser Setup

Playwright is used for web scraping. Install browsers after installing dependencies:

```bash
# Install Chromium (recommended)
playwright install chromium

# Or install all browsers
playwright install

# Install system dependencies (Linux)
playwright install-deps
```

## Running the System

### Command Line

```bash
# Basic research
python main.py --name "Company Name" --industry "Industry"

# With website URL
python main.py --name "Tesla" --url "https://tesla.com"

# Local mode (free tools only, uses DuckDuckGo + Ollama)
python main.py --name "Apple" --local
```

### REST API

```bash
# Start the API server
uvicorn src.api.app:app --reload

# Or with custom host/port
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

API will be available at:
- Endpoints: `http://localhost:8000/api/v1/`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Streamlit UI

```bash
streamlit run src/ui/app.py
```

UI will be available at `http://localhost:8501`

## Verification

### Check Configuration

```python
from src.core.config import get_settings

settings = get_settings()
warnings = settings.validate_config()

if warnings:
    print("Configuration warnings:")
    for w in warnings:
        print(f"  - {w}")
else:
    print("Configuration OK!")
```

### Test AI Provider

```python
from src.core.ai_client import get_ai_manager

client = get_ai_manager()
response = await client.generate("Say hello!")
print(response)
```

### Test Health Endpoint

```bash
curl http://localhost:8000/health/detailed
```

## Troubleshooting

### "No AI provider configured"

Ensure at least one AI provider API key is set in `.env`:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- Or use Ollama (no key needed)

### "TAVILY_API_KEY not set"

Search functionality requires Tavily. Get a free API key at [tavily.com](https://tavily.com).

### Playwright Browser Issues

```bash
# Reinstall browsers
playwright install --force chromium

# Install system dependencies (Linux)
sudo playwright install-deps
```

### Rate Limiting Errors

The system has built-in rate limiting. If you see 429 errors:
- Wait a few seconds between requests
- Reduce `CONCURRENT_SEARCHES` in settings
- Use multiple AI providers as fallbacks

## Next Steps

- [API Reference](../api/API_REFERENCE.md) - REST API documentation
- [Configuration](./CONFIGURATION.md) - Full configuration reference
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions
