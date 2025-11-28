# DO-011: Configuration Not Documented

**Priority**: Medium
**Category**: Documentation
**Status**: Open
**Effort**: Medium (2-4 hours)

## Problem

Environment variables and configuration options are not comprehensively documented.

## Impact

- Users don't know what can be configured
- Default values unclear
- Security-sensitive settings may be misconfigured
- Production tuning is guesswork

## Configuration Sources

Configuration is loaded from:
1. Environment variables
2. `.env` file (via python-dotenv)
3. `src/core/config.py` (defaults)

## Known Environment Variables

### Required
| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `TAVILY_API_KEY` | Tavily search API key | `tvly-...` |

### Optional - LLM Providers
| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `GEMINI_API_KEY` | Google Gemini API key | None |
| `GROQ_API_KEY` | Groq API key | None |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |

### Optional - API Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `localhost:3000,localhost:8000` |
| `MAX_REQUEST_SIZE_BYTES` | Max request body size | `1000000` (1MB) |
| `RESEARCH_TIMEOUT_SECONDS` | Research task timeout | `1800` (30 min) |

### Optional - Integrations
| Variable | Description | Default |
|----------|-------------|---------|
| `NEWSAPI_KEY` | NewsAPI key | None |
| `DATABASE_URL` | Database connection string | `sqlite:///./tasks.db` |

## Solution

Create `docs/guides/CONFIGURATION.md` with:
1. Complete variable reference
2. Required vs optional distinction
3. Default values
4. Security recommendations
5. Example `.env` files for different scenarios

## Acceptance Criteria

- [ ] All environment variables documented
- [ ] Default values listed
- [ ] Security guidance included
- [ ] Example configurations provided

## Related Issues

- DO-005 - Setup guide
