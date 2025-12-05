# DO-005: No Setup/Installation Guide

**Priority**: High
**Category**: Documentation
**Status**: Open
**Effort**: Medium (2-4 hours)

## Problem

The README provides minimal installation instructions. A comprehensive setup guide is needed for:

- Development environment setup
- Production deployment
- Docker deployment
- Environment variable configuration
- Dependency management

## Current State

README only covers:
```bash
git clone ...
pip install -r requirements.txt
# Create .env with 2 keys
```

## Missing Information

1. **Prerequisites**
   - Python version requirements
   - System dependencies (Playwright browsers)
   - Optional dependencies (Redis, PostgreSQL)

2. **Development Setup**
   - Virtual environment creation
   - IDE configuration (VSCode settings)
   - Pre-commit hooks
   - Running tests

3. **Environment Variables**
   - Full list of all environment variables
   - Which are required vs optional
   - Default values
   - Security considerations

4. **Database Setup**
   - SQLite (default) configuration
   - PostgreSQL setup for production
   - Running migrations

5. **LLM Provider Setup**
   - OpenAI configuration
   - Anthropic configuration
   - Gemini configuration
   - Groq configuration
   - Ollama (local) setup

6. **Tool Dependencies**
   - Playwright browser installation
   - Tavily API key
   - NewsAPI key
   - Other tool-specific setup

## Solution

Create `docs/guides/SETUP.md` with comprehensive setup instructions.

## Acceptance Criteria

- [ ] Setup guide created
- [ ] All environment variables documented
- [ ] Development workflow documented
- [ ] Production deployment guide included
- [ ] Troubleshooting section added

## Related Issues

- DO-011 - Configuration not documented
- DO-012 - Deployment not documented
