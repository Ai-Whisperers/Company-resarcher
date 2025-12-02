# Troubleshooting Guide

Common issues and their solutions for Company Researcher.

## Quick Diagnostics

```bash
# Check API health
curl http://localhost:8000/health/detailed

# View detailed component status
curl http://localhost:8000/health/detailed | python -m json.tool

# Check logs
tail -f company_researcher.log
```

## Common Errors

### API Authentication

#### Error: 401 Unauthorized
```json
{"detail": "Invalid or missing API key"}
```

**Cause:** Missing or invalid `API_KEY` header.

**Solution:**
1. Set `API_KEY` in your `.env` file
2. Include header in requests: `Authorization: Bearer your-api-key`
3. Or use query parameter: `?api_key=your-api-key`

### AI Provider Errors

#### Error: AIRateLimitError
```
Rate limit exceeded for provider 'openai'. Retry after 60s
```

**Cause:** AI provider rate limit hit.

**Solutions:**
1. Wait for retry period (automatic with circuit breaker)
2. Add fallback providers in `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   GEMINI_API_KEY=...
   ```
3. Reduce concurrent queries:
   ```bash
   AGENT_MAX_CONCURRENT_QUERIES=3
   ```

#### Error: CircuitOpenError
```
Circuit 'ai_openai' is open. Retry after 45.0s
```

**Cause:** Provider failed repeatedly, circuit breaker tripped.

**Solutions:**
1. Wait for recovery timeout (default 60s)
2. Check provider status at their dashboard
3. Fallback providers will be used automatically
4. To reset manually, restart the application

#### Error: All AI providers failed
```
All AI providers failed. Using mock client.
```

**Cause:** No AI providers available.

**Solutions:**
1. Verify at least one API key is set and valid
2. Check circuit breaker status: `GET /health/detailed`
3. Test provider directly:
   ```python
   from src.core.ai_client import get_ai_manager
   ai = get_ai_manager()
   print(ai.all_clients)  # Should show available clients
   ```

### Search Errors

#### Error: SearchTimeoutError
```
Search timed out after 30s
```

**Cause:** Search provider slow or unreachable.

**Solutions:**
1. Increase timeout:
   ```bash
   SEARCH_TIMEOUT_SECONDS=60
   ```
2. Check network connectivity
3. DuckDuckGo may be rate-limited - wait and retry

#### Error: No search results
```
Gathered 0 sources from 5/5 successful queries
```

**Cause:** Search queries returned empty results.

**Solutions:**
1. Check company name spelling
2. Try broader search terms
3. Verify internet connectivity
4. DuckDuckGo may block VPN/datacenter IPs

### Browser/Scraping Errors

#### Error: Playwright not installed
```
Playwright browsers not installed
```

**Solution:**
```bash
playwright install chromium
```

#### Error: Page timeout
```
Navigation timeout of 30000ms exceeded
```

**Cause:** Website slow or blocking scrapers.

**Solutions:**
1. Increase browser timeout
2. Site may be blocking - content still gathered from search snippets
3. Check if site requires JavaScript (Playwright handles this)

### Database Errors

#### Error: Database locked
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes accessing SQLite.

**Solutions:**
1. Only run one API instance with SQLite
2. For multi-instance, migrate to PostgreSQL
3. Check for zombie processes: `ps aux | grep python`

#### Error: Task not found
```json
{"detail": "Task not found"}
```

**Cause:** Invalid task ID or task was deleted.

**Solutions:**
1. Verify task ID format (UUID)
2. Check task exists: `GET /api/v1/research`
3. Task may have expired or been cleaned up

### Memory Issues

#### Error: Out of memory
```
MemoryError: Unable to allocate array
```

**Cause:** Processing large documents or too many concurrent requests.

**Solutions:**
1. Increase container memory limit
2. Reduce concurrent queries:
   ```bash
   AGENT_MAX_CONCURRENT_QUERIES=3
   ```
3. Reduce document processing batch size

### Network Errors

#### Error: Connection refused
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Cause:** Service not running or wrong port.

**Solutions:**
1. Check if API is running: `docker ps` or `ps aux | grep uvicorn`
2. Verify port: default is 8000
3. Check firewall rules

#### Error: SSL Certificate errors
```
ssl.SSLCertVerificationError: certificate verify failed
```

**Cause:** Invalid or self-signed certificates.

**Solutions:**
1. For development, some tools accept `verify=False` (not recommended for production)
2. Update CA certificates: `pip install certifi --upgrade`
3. Check system time is correct

## Diagnostic Commands

### Check System Status

```bash
# Health check
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed

# Check readiness
curl http://localhost:8000/health/ready

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Check Configuration

```python
# In Python REPL
from src.core.config import get_config
config = get_config()
print(f"AI Primary: {config.ai_primary}")
print(f"Output Dir: {config.output_dir}")
```

### Check AI Providers

```python
from src.core.ai_client import get_ai_manager

ai = get_ai_manager()
print(f"Primary: {ai.primary_client.get_provider_name()}")
print(f"All clients: {[c.get_provider_name() for c in ai.all_clients]}")

# Check circuit breakers
from src.core.circuit_breaker import get_circuit_registry
registry = get_circuit_registry()
print(registry.get_all_stats())
```

### Test Search

```python
import asyncio
from src.tools import get_shared_search_tool

async def test():
    search = get_shared_search_tool()
    results = await search.search("test company", max_results=3)
    print(results)

asyncio.run(test())
```

## Log Analysis

### Enable Debug Logging

```bash
# Via environment
export LOG_LEVEL=DEBUG

# Via CLI flag
python main.py --name "Company" -vv
```

### Key Log Patterns

```bash
# Find errors
grep -i "error\|exception\|failed" company_researcher.log

# Find rate limits
grep -i "rate.limit\|429\|too many" company_researcher.log

# Find timeouts
grep -i "timeout\|timed out" company_researcher.log

# Circuit breaker events
grep -i "circuit" company_researcher.log
```

### Log Format

```
2025-12-01 10:30:45 [INFO] [ai_client] Using primary provider: openai
2025-12-01 10:30:46 [WARNING] [circuit_breaker] Circuit 'ai_openai' opened after 5 failures
2025-12-01 10:31:46 [INFO] [circuit_breaker] Circuit 'ai_openai' transitioned: open -> half_open
```

## Performance Issues

### Slow Research

**Symptoms:** Research takes >30 minutes

**Solutions:**
1. Enable parallel mode (default):
   ```bash
   python main.py --parallel --name "Company"
   ```
2. Increase concurrent queries:
   ```bash
   AGENT_MAX_CONCURRENT_QUERIES=10
   ```
3. Use faster AI provider (Groq for speed)
4. Reduce search depth

### High Memory Usage

**Solutions:**
1. Monitor with: `docker stats`
2. Reduce batch sizes
3. Clear vault cache periodically
4. Increase swap space

### High CPU Usage

**Solutions:**
1. Reduce concurrent requests
2. Check for infinite loops in logs
3. Rate limit incoming requests

## Recovery Procedures

### Reset Circuit Breakers

```python
from src.core.circuit_breaker import get_circuit_registry

registry = get_circuit_registry()
registry.reset_all()
print("All circuit breakers reset")
```

### Clear Cache

```bash
# Clear vault cache
rm -rf data/vault/*

# Clear task database (WARNING: deletes history)
rm data/tasks.db
```

### Restart Services

```bash
# Docker
docker-compose restart api

# Kubernetes
kubectl rollout restart deployment/company-researcher
```

## Getting Help

1. Check the [GitHub Issues](https://github.com/ai-whisperers/Company-researcher/issues)
2. Review logs with debug enabled
3. Test individual components
4. Create a minimal reproduction case
