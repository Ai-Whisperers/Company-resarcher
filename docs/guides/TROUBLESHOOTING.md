# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Company Researcher.

## Quick Diagnostics

### Check System Health

```bash
# If running the API
curl http://localhost:8000/health/detailed
```

### Validate Configuration

```python
from src.core.config import get_settings

settings = get_settings()
warnings = settings.validate_config()
for w in warnings:
    print(f"Warning: {w}")
```

### Check Logs

Logs are written to both console and `research.log` file:

```bash
# View recent logs
tail -f research.log

# Search for errors
grep -i error research.log
```

---

## Common Issues

### API Key Errors

#### Error: "No AI provider configured"

**Symptom**: Application fails to start or returns error about missing AI provider.

**Cause**: No valid AI provider API key found.

**Solution**:
1. Check your `.env` file exists in project root
2. Ensure at least one API key is set:
   ```env
   OPENAI_API_KEY=sk-your-key
   # OR
   ANTHROPIC_API_KEY=sk-ant-your-key
   # OR use Ollama (no key needed)
   ```
3. Restart the application

#### Error: "Invalid API key"

**Symptom**: 401 Unauthorized errors from AI provider.

**Cause**: API key is invalid, expired, or has incorrect format.

**Solution**:
1. Verify the key is correct (no extra spaces)
2. Check the key hasn't expired
3. Ensure you're using the right key type (not a project key for OpenAI)
4. Regenerate the key if needed

---

### Rate Limiting Errors

#### Error: "Rate limit exceeded" (429)

**Symptom**: API returns 429 status code.

**Cause**: Too many requests to LLM provider or local API.

**Solution**:
1. Wait 60 seconds before retrying
2. Reduce concurrent requests
3. Configure fallback providers:
   ```env
   # In .env - system will fallback when primary is rate limited
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

#### Error: "OpenAI rate limit" or "Anthropic rate limit"

**Symptom**: Research hangs or fails during execution.

**Cause**: Exceeded LLM provider rate limits.

**Solution**:
1. Use the built-in rate limiter (enabled by default)
2. Add delays between requests
3. Use Groq or Ollama for high-volume tasks (higher limits)
4. Upgrade your API plan

---

### Browser/Scraping Issues

#### Error: "Browser not found" or "Playwright error"

**Symptom**: Web scraping fails immediately.

**Cause**: Playwright browsers not installed.

**Solution**:
```bash
# Install browsers
playwright install chromium

# Install system dependencies (Linux)
playwright install-deps

# If still failing, try force reinstall
playwright install --force
```

#### Error: "Page timeout" or "Navigation timeout"

**Symptom**: Web scraping times out on certain pages.

**Cause**: Slow website, anti-bot protection, or network issues.

**Solution**:
1. The system will retry automatically
2. For persistent issues, the page will be skipped
3. Check your internet connection
4. Some sites block automated access - this is expected

#### Error: "Access denied" or "403 Forbidden"

**Symptom**: Certain websites refuse connection.

**Cause**: Anti-bot detection or IP blocking.

**Solution**:
1. This is expected for some sites
2. The system will use search results as fallback
3. Consider using a VPN for research

---

### Database Issues

#### Error: "Database is locked" (SQLite)

**Symptom**: Concurrent requests fail with locking errors.

**Cause**: SQLite doesn't handle concurrent writes well.

**Solution**:
1. For production, switch to PostgreSQL:
   ```env
   DATABASE_URL=postgresql://user:pass@localhost:5432/db
   ```
2. Reduce concurrent API requests
3. Restart the application to clear locks

#### Error: "Connection pool exhausted"

**Symptom**: Database operations timeout or fail.

**Cause**: Too many concurrent database connections.

**Solution**:
1. Reduce concurrent requests
2. Increase pool size (requires code changes)
3. Use connection pooling (PgBouncer for PostgreSQL)

---

### Research Issues

#### Empty or Incomplete Results

**Symptom**: Research completes but reports are empty or missing sections.

**Possible Causes**:
1. Company not found online
2. API rate limits hit during research
3. Search API issues

**Solution**:
1. Verify company name spelling
2. Provide website URL for better results:
   ```bash
   python main.py --name "Company" --url "https://company.com"
   ```
3. Check logs for errors during specific phases
4. Try running with `--local` flag for different search

#### Error: "JSON parsing failed"

**Symptom**: Agent fails to parse LLM response.

**Cause**: LLM returned malformed JSON.

**Solution**:
1. This is usually transient - retry the research
2. The system has robust JSON parsing that handles most cases
3. Check logs for the raw response if it persists

#### Research Takes Too Long

**Symptom**: Research doesn't complete within expected time.

**Cause**: Many factors - network, API limits, complex company.

**Solution**:
1. Default timeout is 30 minutes
2. Check progress in logs
3. Use faster models (Groq) for initial testing
4. Reduce scope by specifying industry

---

### Environment Issues

#### Error: "Module not found"

**Symptom**: Import errors when running.

**Cause**: Dependencies not installed or wrong Python environment.

**Solution**:
```bash
# Ensure virtual environment is active
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Error: ".env file not found"

**Symptom**: Configuration defaults used, API keys missing.

**Cause**: No `.env` file in project root.

**Solution**:
```bash
# Create from example
cp .env.example .env

# Or create manually
touch .env
# Add your API keys
```

#### Python Version Issues

**Symptom**: Syntax errors or incompatible packages.

**Cause**: Python version too old.

**Solution**:
```bash
# Check version (need 3.10+)
python --version

# Use pyenv to manage versions
pyenv install 3.10.12
pyenv local 3.10.12
```

---

## Diagnostic Commands

### Test AI Provider

```python
import asyncio
from src.core.ai_client import get_ai_manager

async def test():
    client = get_ai_manager()
    response = await client.generate("Hello, respond with 'OK'")
    print(f"Response: {response}")

asyncio.run(test())
```

### Test Search

```python
import asyncio
from src.tools.search import SearchTool

async def test():
    tool = SearchTool()
    results = await tool.search("OpenAI company")
    print(f"Found {len(results)} results")

asyncio.run(test())
```

### Test Browser

```python
import asyncio
from src.tools.browser import BrowserTool

async def test():
    tool = BrowserTool()
    content = await tool.get_page_content("https://example.com")
    print(f"Content length: {len(content)}")

asyncio.run(test())
```

---

## Getting Help

If you can't resolve an issue:

1. **Check existing issues**: [GitHub Issues](https://github.com/Ai-Whisperers/Company-resarcher/issues)

2. **Report a bug** with:
   - Error message and stack trace
   - Steps to reproduce
   - Environment details (OS, Python version)
   - Relevant log entries (sanitize API keys!)

3. **Include diagnostic info**:
   ```bash
   python --version
   pip list | grep -E "langchain|openai|anthropic|playwright"
   ```

---

## FAQ

**Q: Can I run without internet?**
A: Limited - you need Ollama for AI, but web research requires internet.

**Q: How do I reduce API costs?**
A: Use Groq or Ollama for testing, cache responses, reduce concurrent searches.

**Q: Why is research slow?**
A: Multiple factors - AI provider latency, web scraping, and analysis. Use faster models or increase concurrency for speed.

**Q: Can I research private companies?**
A: Yes, but results depend on available public information. Provide website URL for best results.
