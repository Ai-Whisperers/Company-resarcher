# Checkpoint Configuration Reference

## Environment Variables for Checkpointing

Add these variables to your `.env` file to configure LangGraph checkpointing:

```bash
# =============================================================================
# LANGGRAPH CHECKPOINTING CONFIGURATION
# =============================================================================

# Enable/disable checkpointing (default: true)
# Set to false to disable checkpoint persistence
GRAPH__ENABLE_CHECKPOINTING=true

# Checkpoint database path (default: data/checkpoints/research.db)
# Can be absolute or relative path
GRAPH__CHECKPOINT_DB_PATH=data/checkpoints/research.db

# Automatic checkpoint cleanup (default: 30 days)
# Checkpoints older than this will be eligible for cleanup
GRAPH__CHECKPOINT_CLEANUP_DAYS=30

# =============================================================================
# EXAMPLE CONFIGURATIONS
# =============================================================================

# Development (keep short-term checkpoints)
# GRAPH__ENABLE_CHECKPOINTING=true
# GRAPH__CHECKPOINT_DB_PATH=data/checkpoints/dev.db
# GRAPH__CHECKPOINT_CLEANUP_DAYS=7

# Production (keep long-term checkpoints)
# GRAPH__ENABLE_CHECKPOINTING=true
# GRAPH__CHECKPOINT_DB_PATH=/var/lib/research/checkpoints/prod.db
# GRAPH__CHECKPOINT_CLEANUP_DAYS=90

# Testing (in-memory, no persistence)
# GRAPH__ENABLE_CHECKPOINTING=false
# GRAPH__CHECKPOINT_DB_PATH=:memory:

# Disable checkpointing (for fast, non-resumable research)
# GRAPH__ENABLE_CHECKPOINTING=false
```

## Default Values

If not specified in `.env`, these defaults are used:

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAPH__ENABLE_CHECKPOINTING` | `true` | Checkpointing enabled |
| `GRAPH__CHECKPOINT_DB_PATH` | `data/checkpoints/research.db` | SQLite database path |
| `GRAPH__CHECKPOINT_CLEANUP_DAYS` | `30` | Days to keep checkpoints |

## Configuration in Python

You can also configure checkpointing programmatically:

```python
from src.core.config import get_settings

settings = get_settings()

# Access checkpoint configuration
enabled = settings.graph.enable_checkpointing
db_path = settings.graph.checkpoint_db_path
cleanup_days = settings.graph.checkpoint_cleanup_days

print(f"Checkpointing: {'enabled' if enabled else 'disabled'}")
print(f"Database: {db_path}")
print(f"Cleanup after: {cleanup_days} days")
```

## Verifying Configuration

Test your checkpoint configuration:

```bash
# 1. Check if checkpointing is enabled
python -c "from src.core.config import get_settings; \
  print('Enabled:', get_settings().graph.enable_checkpointing)"

# 2. Check database path
python -c "from src.core.config import get_settings; \
  print('DB Path:', get_settings().graph.checkpoint_db_path)"

# 3. Run test suite
python tests/test_checkpointing.py
```

## See Also

- [Checkpointing Guide](../guides/CHECKPOINTING.md) - Complete usage guide
- [Configuration Guide](../guides/CONFIGURATION.md) - All configuration options
- [GraphConfig Reference](../../src/core/config/pipeline.py) - Source code
