# Configuration Reference

Complete reference for all configuration options in Company Researcher.

## Configuration Sources

Configuration is loaded in the following order (later sources override earlier):

1. **Default values** (in `src/core/config.py`)
2. **Environment variables**
3. **`.env` file** (in project root)

## Environment Variables

### AI Providers

At least one AI provider must be configured.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | One required | None | OpenAI API key (`sk-...`) |
| `ANTHROPIC_API_KEY` | One required | None | Anthropic API key (`sk-ant-...`) |
| `GEMINI_API_KEY` | One required | None | Google Gemini API key |
| `GROQ_API_KEY` | One required | None | Groq API key (`gsk_...`) |

**Note**: Ollama works without an API key if the server is running locally.

### AI Configuration

Advanced AI settings using nested configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `AI__PRIMARY` | `openai` | Primary AI provider: `openai`, `anthropic`, `gemini`, `groq`, `ollama` |
| `AI__FALLBACK` | None | Fallback provider if primary fails |
| `AI__OPENAI__MODEL` | `gpt-4o` | OpenAI model to use |
| `AI__OPENAI__TEMPERATURE` | `0.7` | Sampling temperature |
| `AI__OPENAI__MAX_TOKENS` | `4096` | Maximum response tokens |
| `AI__ANTHROPIC__MODEL` | `claude-sonnet-4-20250514` | Anthropic model |
| `AI__GEMINI__MODEL` | `gemini-2.0-flash` | Gemini model |
| `AI__GROQ__MODEL` | `llama-3.1-8b-instant` | Groq model |
| `AI__OLLAMA__MODEL` | `llama3.1:8b` | Ollama model |

### Search & Data APIs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TAVILY_API_KEY` | Recommended | None | Tavily search API key |
| `NEWSAPI_KEY` | No | None | NewsAPI key for news aggregation |
| `SERPAPI_API_KEY` | No | None | SerpAPI key (alternative search) |

### Observability

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LANGFUSE_PUBLIC_KEY` | No | None | Langfuse public key for tracing |
| `LANGFUSE_SECRET_KEY` | No | None | Langfuse secret key |
| `LANGFUSE_HOST` | No | `https://cloud.langfuse.com` | Langfuse server URL |

### API Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins (comma-separated) |
| `MAX_REQUEST_SIZE_BYTES` | No | `1000000` | Maximum request body size (1MB) |
| `RESEARCH_TIMEOUT_SECONDS` | No | `1800` | Research task timeout (30 min) |

### Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./tasks.db` | Database connection string |

Supported databases:
- SQLite: `sqlite:///./tasks.db`
- PostgreSQL: `postgresql://user:pass@host:5432/dbname`

### Research Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAX_SEARCH_RESULTS` | No | `5` | Max results per search query |
| `CONCURRENT_SEARCHES` | No | `3` | Number of concurrent searches |
| `OUTPUT_DIR` | No | `./output` | Directory for research output |

---

## Example Configurations

### Minimal (OpenAI only)

```env
OPENAI_API_KEY=sk-your-key
TAVILY_API_KEY=tvly-your-key
```

### Local Development (Ollama)

```env
# No API keys needed for AI
AI__PRIMARY=ollama
AI__OLLAMA__MODEL=llama3.1:8b

# Use free search
# DuckDuckGo is used automatically when TAVILY_API_KEY is not set
```

### Production

```env
# Primary and fallback AI
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
AI__PRIMARY=openai
AI__FALLBACK=anthropic

# Search
TAVILY_API_KEY=tvly-your-key
NEWSAPI_KEY=your-newsapi-key

# Database
DATABASE_URL=postgresql://user:pass@db.example.com:5432/company_researcher

# API configuration
CORS_ORIGINS=https://app.example.com
MAX_REQUEST_SIZE_BYTES=2000000
RESEARCH_TIMEOUT_SECONDS=3600

# Observability
LANGFUSE_PUBLIC_KEY=pk-your-key
LANGFUSE_SECRET_KEY=sk-your-key
```

### Cost-Optimized

```env
# Use cheaper models
AI__PRIMARY=groq
AI__GROQ__MODEL=llama-3.1-8b-instant
AI__FALLBACK=ollama

# Limit searches
MAX_SEARCH_RESULTS=3
CONCURRENT_SEARCHES=2
```

### High-Quality Research

```env
# Use best models
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
AI__PRIMARY=anthropic
AI__ANTHROPIC__MODEL=claude-sonnet-4-20250514
AI__FALLBACK=openai
AI__OPENAI__MODEL=gpt-4o

# More thorough search
MAX_SEARCH_RESULTS=10
CONCURRENT_SEARCHES=5
```

---

## AI Provider Models

### OpenAI Models

| Model | Best For | Cost |
|-------|----------|------|
| `gpt-4o` | General research (default) | $$$ |
| `gpt-4o-mini` | Cost-effective tasks | $$ |
| `gpt-4-turbo` | Complex analysis | $$$$ |

### Anthropic Models

| Model | Best For | Cost |
|-------|----------|------|
| `claude-sonnet-4-20250514` | Balanced quality/cost (default) | $$$ |
| `claude-3-5-haiku-20241022` | Fast, cost-effective | $$ |
| `claude-3-opus-20240229` | Highest quality | $$$$ |

### Gemini Models

| Model | Best For | Cost |
|-------|----------|------|
| `gemini-2.0-flash` | Fast responses (default) | $$ |
| `gemini-1.5-pro` | Complex tasks | $$$ |

### Groq Models

| Model | Best For | Cost |
|-------|----------|------|
| `llama-3.1-8b-instant` | Fast, free tier (default) | $ |
| `llama-3.1-70b-versatile` | Better quality | $$ |
| `mixtral-8x7b-32768` | Long context | $$ |

### Ollama Models

| Model | Best For | Cost |
|-------|----------|------|
| `llama3.1:8b` | Local, fast (default) | Free |
| `llama3.1:70b` | Local, quality | Free |
| `mistral:7b` | Local, balanced | Free |

---

## Validation

The configuration is validated at startup. Check warnings:

```python
from src.core.config import get_settings

settings = get_settings()
warnings = settings.validate_config()

if warnings:
    for w in warnings:
        print(f"Warning: {w}")
```

Common warnings:
- "Primary AI provider has no API key configured"
- "TAVILY_API_KEY not set - search functionality will be limited"

---

## Security Recommendations

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use environment variables in production** - Don't use `.env` files in production
3. **Rotate API keys regularly**
4. **Use secrets management** - AWS Secrets Manager, HashiCorp Vault, etc.
5. **Limit CORS origins** - Don't use `*` in production
6. **Set appropriate timeouts** - Prevent runaway tasks

---

## Troubleshooting

### Configuration Not Loading

1. Ensure `.env` file is in project root
2. Check file encoding (UTF-8)
3. No spaces around `=` in `.env`
4. Restart application after changes

### Nested Configuration Not Working

Use double underscore for nested config:
```env
# Correct
AI__PRIMARY=anthropic
AI__ANTHROPIC__MODEL=claude-3-opus-20240229

# Wrong
AI.PRIMARY=anthropic
```

### Environment Variables vs .env

Environment variables take precedence over `.env` file:
```bash
# This overrides .env
export OPENAI_API_KEY=sk-override
python main.py
```
