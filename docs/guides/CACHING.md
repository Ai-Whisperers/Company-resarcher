# Caching Guide

This guide covers the caching infrastructure in Company Researcher, including configuration, usage patterns, and best practices.

## Overview

Company Researcher uses a multi-layer caching system to reduce API costs and improve response times:

1. **AI Response Cache** (`src/core/cache.py`) - Caches AI provider responses
2. **Cache Service** (`src/services/cache_service.py`) - General-purpose caching with namespaces
3. **CachedAIClient** (`src/core/cached_ai_client.py`) - Wrapper for AI clients with caching

## Configuration

### Environment Variables

```bash
# Cache Settings
CACHE_ENABLED=true              # Enable/disable caching globally
CACHE_DEFAULT_TTL=3600          # Default TTL in seconds (1 hour)
CACHE_DIR=/path/to/cache        # Custom cache directory

# Nested configuration (via pydantic)
CACHE__ENABLED=true
CACHE__DEFAULT_TTL=3600
CACHE__AI_CACHE_ENABLED=true
CACHE__MAX_SIZE_MB=500
```

### Configuration Classes

```python
from src.core.config import get_settings, CacheConfig

settings = get_settings()

# Access cache configuration
print(settings.cache.enabled)        # True
print(settings.cache.default_ttl)    # 3600
print(settings.cache.ai_cache_enabled)  # True
print(settings.get_cache_dir())      # Path to .cache directory
```

### Profile-Based Defaults

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| enabled | True | True | True |
| default_ttl | 3600 | 3600 | 7200 |
| ai_cache_enabled | True | True | True |

## Usage

### CacheService (General Purpose)

```python
from src.services.cache_service import get_cache_service

cache = get_cache_service()

# Store with default TTL
cache.set("my_key", {"data": "value"})

# Store with custom TTL (5 minutes)
cache.set("short_lived", data, ttl_seconds=300)

# Store with namespace
cache.set("user:123", user_data, namespace="users")

# Retrieve
data = cache.get("my_key")
if data is None:
    # Cache miss - fetch from source
    data = fetch_from_source()
    cache.set("my_key", data)

# Check existence
if cache.exists("my_key"):
    # Key exists and is not expired
    pass

# Delete
cache.delete("my_key")

# Clear namespace
cache.clear(namespace="users")

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate}%")
print(stats.to_dict())
```

### AI Response Cache

The AI cache is automatically used by `CachedAIClient`:

```python
from src.core.cached_ai_client import CachedAIClient
from src.core.ai_client import AIClientManager

# Wrap an AI client with caching
base_client = AIClientManager().get_client()
cached_client = CachedAIClient(base_client, enable_cache=True)

# Responses are automatically cached based on:
# - prompt
# - system message
# - temperature
# - max_tokens
response = await cached_client.generate(prompt, system=system)

# Get cache statistics
stats = cached_client.get_cache_stats()
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate_percent']}%")

# Disable caching for testing
test_client = CachedAIClient(base_client, enable_cache=False)
```

### Cache Integration in AgentFactory

The `AgentFactory` automatically applies caching as the outermost optimization layer:

```python
from src.agents.factory import AgentFactory

# Cache is enabled by default
factory = AgentFactory(enable_cache=True)

# Disable for testing
factory = AgentFactory(enable_cache=False)
```

## Cache Locations

| Cache Type | Directory | File Format |
|------------|-----------|-------------|
| AI Responses | `.cache/ai_responses/` | `{sha256_hash}.json` |
| Service Cache | `.cache/service/` | `{sha256_hash}.json` |

## Cache Key Generation

Cache keys are generated using SHA256 hashing to ensure:
- Unique keys for different inputs
- Safe filenames
- Collision resistance

```python
# AI Cache key includes:
key_data = {
    "prompt": prompt,
    "system": system,
    "temperature": temperature,
    "max_tokens": max_tokens,
}
key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
```

## Cache Statistics

### CacheService Stats

```python
cache = get_cache_service()
stats = cache.get_stats()

# Available metrics
stats.hits          # Number of cache hits
stats.misses        # Number of cache misses
stats.sets          # Number of cache sets
stats.deletes       # Number of cache deletes
stats.expirations   # Number of expired entries found
stats.errors        # Number of errors encountered
stats.total_requests  # Total get requests
stats.hit_rate      # Hit rate percentage
```

### CachedAIClient Stats

```python
client = CachedAIClient(base_client)
stats = client.get_cache_stats()

# Available metrics
stats["hits"]
stats["misses"]
stats["total_requests"]
stats["hit_rate_percent"]
stats["estimated_savings_percent"]
```

## Performance Characteristics

From benchmarking:

| Scenario | Expected Hit Rate |
|----------|-------------------|
| Repeated company research | 60-80% |
| Similar companies in same industry | 20-40% |
| Completely new research | 0% |

## Best Practices

### 1. Use Namespaces for Organization

```python
# Good: Organized by feature
cache.set("company:apple", data, namespace="companies")
cache.set("search:query123", results, namespace="search")
cache.set("user:123:prefs", prefs, namespace="users")

# Clear specific namespace without affecting others
cache.clear(namespace="search")
```

### 2. Choose Appropriate TTLs

```python
# Frequently changing data - short TTL
cache.set("stock_price", price, ttl_seconds=60)

# Slowly changing data - longer TTL
cache.set("company_info", info, ttl_seconds=86400)  # 24 hours

# Static data - very long TTL
cache.set("industry_codes", codes, ttl_seconds=604800)  # 1 week
```

### 3. Handle Cache Misses Gracefully

```python
def get_company_data(company_id: str) -> dict:
    cache = get_cache_service()

    # Try cache first
    data = cache.get(f"company:{company_id}", namespace="companies")

    if data is not None:
        return data

    # Cache miss - fetch from source
    data = fetch_company_from_api(company_id)

    # Store for next time
    cache.set(f"company:{company_id}", data, namespace="companies", ttl_seconds=3600)

    return data
```

### 4. Invalidate Stale Data

```python
# Delete specific key
cache.delete(f"company:{company_id}", namespace="companies")

# Clear entire namespace after bulk update
cache.clear(namespace="companies")
```

## Security Considerations

1. **No Sensitive Data in Cache Keys** - Don't include API keys or secrets in cache keys
2. **JSON Serialization** - Uses JSON instead of pickle to prevent deserialization attacks
3. **File Permissions** - Cache directory should have appropriate permissions
4. **Cache Location** - `.cache/` is gitignored by default

## Troubleshooting

### Cache Not Working

1. Check if caching is enabled:
   ```python
   settings = get_settings()
   print(settings.cache.enabled)
   ```

2. Check cache directory exists and is writable:
   ```python
   print(settings.get_cache_dir())
   ```

3. Check for errors in logs:
   ```bash
   grep -i "cache" research.log
   ```

### High Cache Miss Rate

1. Verify cache key consistency (same inputs produce same keys)
2. Check TTL settings (may be too short)
3. Review cache statistics for patterns

### Cache Growing Too Large

1. Set `CACHE__MAX_SIZE_MB` to limit size
2. Clear old entries: `cache.clear()`
3. Manually delete cache directory contents

## Future Improvements (Planned)

- **Redis Backend** - For distributed caching in production
- **Cache Warming** - Pre-populate cache with common queries
- **Automatic Cleanup** - Background process to remove expired entries
- **Size-Based Eviction** - LRU eviction when max size reached
