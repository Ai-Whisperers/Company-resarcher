# LangGraph Checkpointing Guide

## Overview

The Company Researcher system uses **LangGraph checkpointing** to enable **resumable research workflows**. This means you can:

- ✅ **Resume interrupted research** after crashes or manual stops
- ✅ **Implement human-in-the-loop** workflows with state persistence
- ✅ **Audit research execution** with complete state history
- ✅ **Recover from failures** without losing progress

## How It Works

LangGraph checkpointing automatically saves the research state at each node execution. The checkpoint includes:

- **Research state**: Company data, sources, insights, reports
- **Execution phase**: Which research nodes have completed
- **Quality metrics**: Scores and feedback from quality checks
- **Error tracking**: Any errors encountered during execution

All checkpoints are stored in a **SQLite database** for fast, reliable persistence.

---

## Configuration

### Enable/Disable Checkpointing

Checkpointing is **enabled by default**. You can control it via environment variables:

```bash
# In .env file
GRAPH__ENABLE_CHECKPOINTING=true  # Enable (default)
GRAPH__CHECKPOINT_DB_PATH=data/checkpoints/research.db  # Database path
GRAPH__CHECKPOINT_CLEANUP_DAYS=30  # Keep checkpoints for 30 days
```

### Database Location

By default, checkpoints are stored in: `data/checkpoints/research.db`

You can customize this path:

```bash
# Use custom path
GRAPH__CHECKPOINT_DB_PATH=/path/to/custom/checkpoints.db

# Use in-memory database (NOT recommended for production)
GRAPH__CHECKPOINT_DB_PATH=:memory:
```

---

## CLI Usage

### 1. List Available Checkpoints

See all research tasks that can be resumed:

```bash
python main.py --list-checkpoints
```

**Output:**
```
Found 3 checkpoints:

Thread: research-tesla-2024-01-15
  Checkpoints: 5
  Latest: 2024-01-15T14:23:45
  Checkpoint ID: abc123...

Thread: research-apple-2024-01-14
  Checkpoints: 3
  Latest: 2024-01-14T10:15:30
  Checkpoint ID: def456...
```

### 2. Resume Research from Checkpoint

Continue an interrupted research task:

```bash
# Basic resume
python main.py --resume-checkpoint research-tesla-2024-01-15

# Resume with human feedback (for quality review)
python main.py --resume-checkpoint research-tesla-2024-01-15 \
  --human-feedback "Please add more detail on competitive positioning"
```

### 3. View Checkpoint Statistics

See database statistics:

```bash
python main.py --checkpoint-stats
```

**Output:**
```
Checkpoint Database Statistics:
  Total Checkpoints: 47
  Unique Threads: 12
  Database Size: 15.42 MB
  Oldest Checkpoint: 2024-01-01T08:00:00
  Newest Checkpoint: 2024-01-15T14:23:45
```

### 4. Clean Up Old Checkpoints

Remove checkpoints older than N days:

```bash
# Clean up checkpoints older than 7 days
python main.py --cleanup-checkpoints 7

# Clean up checkpoints older than 30 days (default)
python main.py --cleanup-checkpoints 30
```

### 5. Delete Specific Thread

Remove all checkpoints for a specific research task:

```bash
python main.py --delete-checkpoint research-failed-task-123
```

---

## Python API Usage

### Basic Usage

```python
from src.graph.research_graph import run_research, resume_research
from src.graph.checkpointer import get_checkpointer

# Run research with checkpointing
result = await run_research(
    company_name="Tesla",
    research_types=["market", "financial"],
    thread_id="research-tesla-2024",  # Custom thread ID
)

# Resume from checkpoint
result = await resume_research(
    thread_id="research-tesla-2024",
    human_feedback="Add more competitive analysis",  # Optional
)
```

### Advanced Usage

```python
from src.graph.checkpointer import (
    get_checkpointer,
    list_checkpoints,
    cleanup_old_checkpoints,
    get_checkpoint_stats,
)

# Get checkpointer instance
checkpointer = get_checkpointer()

# List recent checkpoints
checkpoints = list_checkpoints(limit=10)
for cp in checkpoints:
    print(f"Thread: {cp['thread_id']}, Created: {cp['created_at']}")

# Clean up old checkpoints
deleted = cleanup_old_checkpoints(max_age_days=7)
print(f"Deleted {deleted} old checkpoints")

# Get statistics
stats = get_checkpoint_stats()
print(f"Total checkpoints: {stats['total_checkpoints']}")
print(f"Database size: {stats['db_size_mb']} MB")
```

### Creating Custom Graphs with Checkpointing

```python
from src.graph.research_graph import create_research_graph
from src.graph.checkpointer import get_checkpointer

# Create graph with checkpointing
graph = create_research_graph(
    research_types=["market", "financial"],
    with_checkpointer=True,  # Enable checkpointing
    with_human_review=True,  # Enable human-in-the-loop
)

# Run with custom thread ID
config = {
    "configurable": {
        "thread_id": "custom-research-123"
    }
}

result = await graph.ainvoke(initial_state, config)
```

---

## Common Scenarios

### Scenario 1: Long-Running Research Crashes

**Problem:** Research takes 2 hours, crashes after 90 minutes.

**Solution:**
1. Research automatically checkpoints every node execution
2. After crash, list checkpoints: `python main.py --list-checkpoints`
3. Resume: `python main.py --resume-checkpoint <thread_id>`
4. Research continues from last successful checkpoint

### Scenario 2: Manual Interruption (Ctrl+C)

**Problem:** You need to stop research to fix something.

**Solution:**
1. Press `Ctrl+C` to interrupt
2. LangGraph saves checkpoint at current node
3. Fix your issue
4. Resume: `python main.py --resume-checkpoint <thread_id>`

### Scenario 3: Human-in-the-Loop Quality Review

**Problem:** Research completes but quality score is low.

**Solution:**
1. Graph interrupts before `human_review` node
2. Review the report and insights
3. Resume with feedback:
   ```bash
   python main.py --resume-checkpoint <thread_id> \
     --human-feedback "Add more data on market trends"
   ```
4. Graph re-synthesizes with your feedback

### Scenario 4: Database Bloat

**Problem:** Checkpoint database grows too large.

**Solution:**
```bash
# Clean up checkpoints older than 7 days
python main.py --cleanup-checkpoints 7

# Or configure automatic cleanup
# In .env:
GRAPH__CHECKPOINT_CLEANUP_DAYS=7
```

---

## Best Practices

### 1. Use Descriptive Thread IDs

```python
# ✅ Good - descriptive
thread_id = f"research-{company_name}-{date}-{research_type}"

# ❌ Bad - generic
thread_id = str(uuid.uuid4())
```

### 2. Clean Up Regularly

Set up a cron job or scheduled task:

```bash
# Daily cleanup of checkpoints older than 7 days
0 2 * * * cd /path/to/project && python main.py --cleanup-checkpoints 7
```

### 3. Monitor Database Size

```python
from src.graph.checkpointer import get_checkpoint_stats

stats = get_checkpoint_stats()
if stats['db_size_mb'] > 100:
    print("Warning: Checkpoint database is large, consider cleanup")
```

### 4. Use Custom Paths for Different Environments

```bash
# Development
GRAPH__CHECKPOINT_DB_PATH=data/checkpoints/dev.db

# Production
GRAPH__CHECKPOINT_DB_PATH=/var/lib/research/checkpoints/prod.db
```

### 5. Backup Important Checkpoints

```bash
# Before major changes, backup the checkpoint database
cp data/checkpoints/research.db data/checkpoints/research.db.backup
```

---

## Troubleshooting

### Checkpoints Not Being Created

**Check 1:** Verify checkpointing is enabled
```bash
# In .env
GRAPH__ENABLE_CHECKPOINTING=true
```

**Check 2:** Verify database path is writable
```bash
# Test write permissions
touch data/checkpoints/test.db
rm data/checkpoints/test.db
```

**Check 3:** Check logs for errors
```bash
# Look for checkpointer errors
grep "checkpointer" research.log
```

### Cannot Resume from Checkpoint

**Check 1:** Verify thread ID exists
```bash
python main.py --list-checkpoints | grep <thread_id>
```

**Check 2:** Verify checkpoint database is accessible
```bash
ls -lh data/checkpoints/research.db
```

**Check 3:** Try listing checkpoint details
```python
from src.graph.checkpointer import list_checkpoints

checkpoints = list_checkpoints()
print(checkpoints)
```

### Database Locked Errors

**Cause:** Multiple processes accessing SQLite database

**Solution:**
- Use separate databases for concurrent research tasks
- Or use PostgreSQL for production (future enhancement)

### Performance Issues

**Symptom:** Research runs slowly with checkpointing enabled

**Check 1:** Database size
```bash
python main.py --checkpoint-stats
```

**Solution 1:** Clean up old checkpoints
```bash
python main.py --cleanup-checkpoints 7
```

**Solution 2:** Use custom database path on faster storage
```bash
# In .env
GRAPH__CHECKPOINT_DB_PATH=/fast/ssd/checkpoints.db
```

---

## Technical Details

### Checkpoint Schema

LangGraph creates the following SQLite tables:

```sql
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    checkpoint BLOB NOT NULL,
    metadata BLOB,
    created_at REAL NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

### State Serialization

Research state is serialized using LangGraph's built-in Pydantic serialization:

- **Efficient:** Only changed fields are stored
- **Type-safe:** Pydantic models ensure data integrity
- **Compressed:** Large data is compressed in SQLite BLOB

### Checkpoint Frequency

Checkpoints are created:
- **After each node execution** (market_research, financial_research, etc.)
- **Before human-in-the-loop interrupts**
- **On explicit state updates**

---

## Future Enhancements

Planned improvements to checkpointing:

1. **PostgreSQL Backend** - For production scalability
2. **Redis Backend** - For distributed systems
3. **Cloud Storage** - S3/GCS for cloud deployments
4. **Automatic Cleanup** - Background task for old checkpoints
5. **Checkpoint Compression** - Reduce database size
6. **Checkpoint Encryption** - Secure sensitive research data
7. **Partial Resume** - Resume from specific node
8. **Checkpoint Branching** - Try different paths from same checkpoint

---

## Related Documentation

- [LangGraph Official Docs](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Research Graph Architecture](../architecture/RESEARCH_GRAPH.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

## Support

If you encounter issues with checkpointing:

1. Check this guide's troubleshooting section
2. Review logs: `research.log`
3. Run test suite: `python tests/test_checkpointing.py`
4. File an issue: [GitHub Issues](https://github.com/ai-whisperers/Company-researcher/issues)
