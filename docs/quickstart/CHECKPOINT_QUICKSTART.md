# Checkpoint Quick Start

## 🚀 5-Minute Checkpoint Guide

### 1. Start Research (with automatic checkpointing)

```bash
# Checkpointing is enabled by default
python main.py --name "Tesla" --industry "Automotive"
```

### 2. Interrupt Research (Ctrl+C)

Press `Ctrl+C` to stop the research at any time. The current state is automatically saved.

### 3. List Checkpoints

```bash
python main.py --list-checkpoints
```

**Output:**
```
Thread: research-tesla-2024-01-15-123456
  Checkpoints: 3
  Latest: 2024-01-15T14:23:45
```

### 4. Resume Research

```bash
python main.py --resume-checkpoint research-tesla-2024-01-15-123456
```

That's it! Your research continues from where it left off.

---

## 📋 Common Commands

### Checkpoint Management

```bash
# List all checkpoints
python main.py --list-checkpoints

# View statistics
python main.py --checkpoint-stats

# Clean up old checkpoints (7 days)
python main.py --cleanup-checkpoints 7

# Delete specific checkpoint
python main.py --delete-checkpoint <thread_id>
```

### Resume with Feedback

```bash
# Resume with human feedback for quality improvement
python main.py --resume-checkpoint <thread_id> \
  --human-feedback "Add more competitive analysis"
```

---

## ⚙️ Configuration

### Enable/Disable Checkpointing

```bash
# In .env file
GRAPH__ENABLE_CHECKPOINTING=true  # Default: enabled
```

### Custom Database Path

```bash
# In .env file
GRAPH__CHECKPOINT_DB_PATH=data/checkpoints/research.db
```

### Automatic Cleanup

```bash
# In .env file
GRAPH__CHECKPOINT_CLEANUP_DAYS=30  # Keep for 30 days
```

---

## 🎯 Use Cases

### Long-Running Research

Research takes hours? No problem:

```bash
# Start research
python main.py --full --batch companies.json

# (Later) Resume if interrupted
python main.py --list-checkpoints
python main.py --resume-checkpoint <thread_id>
```

### Human-in-the-Loop

Review and improve research quality:

```bash
# Research completes, quality check triggers review
# Add your feedback and resume
python main.py --resume-checkpoint <thread_id> \
  --human-feedback "Include more market size data"
```

### Batch Processing with Recovery

Process multiple companies with automatic recovery:

```bash
# Start batch
python main.py --batch companies/

# If crash, resume from checkpoint
python main.py --resume-checkpoint <thread_id>
```

---

## 🔍 Troubleshooting

### "No checkpoints found"

- Research needs to run for at least one node to create a checkpoint
- Check: `python main.py --checkpoint-stats`

### "Checkpointing is disabled"

- Set in .env: `GRAPH__ENABLE_CHECKPOINTING=true`
- Verify: `python tests/test_checkpointing.py`

### Database errors

- Check permissions: `ls -lh data/checkpoints/`
- Clean up: `python main.py --cleanup-checkpoints 7`

---

## 📚 Learn More

- [Full Checkpointing Guide](../guides/CHECKPOINTING.md)
- [Configuration Reference](../configuration/CHECKPOINT_CONFIG.md)
- [Test Suite](../../tests/test_checkpointing.py)

---

## 💡 Tips

1. **Use descriptive thread IDs** when running programmatically
2. **Clean up regularly** with `--cleanup-checkpoints`
3. **Monitor database size** with `--checkpoint-stats`
4. **Backup important checkpoints** before major changes
5. **Test resumption** in dev before relying on it in production
