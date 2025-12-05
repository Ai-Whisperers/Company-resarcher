# Quick Start: Tracing Your LangChain Flows

## TL;DR

**Question:** Are workspaces paid features? Can we do this locally?

**Answer:**
- ✅ LangSmith Free Tier works (just need to use correct API key)
- ✅ Yes! Multiple 100% free local alternatives available
- ⭐ **Recommended:** Phoenix (easiest local setup)

---

## 🆓 Option 1: Fix LangSmith Free Tier (5 min)

Your issue: Using wrong API key type.

**Fix:**
```env
# In .env - Change from service key to project key
LANGCHAIN_API_KEY=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
```

**Then test:**
```bash
python test_langsmith_clean.py
```

**Dashboard:** https://smith.langchain.com

**Free tier limits:**
- 5,000 traces/month
- 14-day retention
- ✓ Full features (no workspace needed)

---

## 🏠 Option 2: Phoenix Local (10 min) ⭐ RECOMMENDED

**Why Phoenix:**
- 100% free & open source
- No cloud, no accounts, no limits
- Beautiful UI
- Automatic instrumentation
- Real-time streaming

**Setup:**
```bash
# 1. Install
pip install arize-phoenix openinference-instrumentation-langchain

# 2. Start Phoenix
python start_phoenix.py
# Opens: http://localhost:6006

# 3. In NEW terminal, run research
python main.py --name "Tesla" --industry "Automotive"

# 4. View traces in browser
```

**That's it!** All LangChain calls are now traced automatically.

---

## 🐳 Option 3: LangFuse Self-Hosted (15 min)

**Why LangFuse:**
- Most similar to LangSmith
- Full evaluation features
- Persistent storage
- Multi-user support

**Setup:**
```bash
# 1. Start with Docker
docker-compose -f docker-compose-langfuse.yml up -d

# 2. Open browser
open http://localhost:3000

# 3. Create account (local only)

# 4. Get API keys from Settings

# 5. Add to .env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

---

## 🎨 Option 4: Built-in Visual Workflow (Already Installed!)

**Why Visual Workflow:**
- Already in your code
- Exports to JSON/YAML/Mermaid
- No installation needed
- Great for planning

**Setup:**
```bash
# Run demo
python demo_visual_workflow.py

# View outputs in workflow_exports/
# - research_workflow.mmd -> Copy to mermaid.live
# - research_workflow.json -> Import to draw.io
```

---

## 🎯 What Should You Choose?

### For Quick Testing → Phoenix
```bash
pip install arize-phoenix openinference-instrumentation-langchain
python start_phoenix.py
```

### For Production Setup → LangFuse
```bash
docker-compose -f docker-compose-langfuse.yml up -d
```

### For Planning Workflows → Visual Workflow
```bash
python demo_visual_workflow.py
```

### For Limited Cloud Use → LangSmith Free
```env
LANGCHAIN_API_KEY=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
```

---

## 📊 Feature Comparison

| Feature | Phoenix | LangFuse | Visual Workflow | LangSmith Free |
|---------|---------|----------|-----------------|----------------|
| **Cost** | Free | Free | Free | Free (5K/mo) |
| **Setup Time** | 5 min | 15 min | 0 min | 5 min |
| **Requires Cloud** | No | No | No | Yes |
| **Real-time** | Yes | Yes | No | Yes |
| **Storage** | Memory | PostgreSQL | Files | Cloud (14d) |
| **Team Sharing** | No | Yes | Files only | Yes |
| **Evaluation** | Basic | Full | No | Full |
| **Best For** | Solo dev | Team/Prod | Design | Light use |

---

## 🚀 Recommended Path

**For You (Solo Developer):**

1. **Start with Phoenix** (today):
   ```bash
   pip install arize-phoenix openinference-instrumentation-langchain
   python start_phoenix.py
   ```

2. **Try LangSmith Free** (if you like cloud):
   - Fix API key in `.env`
   - Get 5,000 traces/month free

3. **Use Visual Workflow** (for planning):
   - Already installed
   - Great for complex flows

4. **Upgrade to LangFuse** (if you need persistence):
   - When Phoenix memory isn't enough
   - When working with a team

---

## 💡 My Recommendation

**Use Phoenix!** Here's why:

✅ **Zero Configuration**
- No accounts, no API keys
- Just `pip install` and run

✅ **100% Local**
- No data sent to cloud
- Unlimited traces
- No rate limits

✅ **Beautiful UI**
- Real-time streaming
- Interactive exploration
- Professional visualizations

✅ **Automatic**
- Auto-instruments LangChain
- No code changes needed

---

## 🎬 Try Phoenix Now (2 minutes)

```bash
# Terminal 1: Install and start Phoenix
pip install arize-phoenix openinference-instrumentation-langchain
python start_phoenix.py

# Terminal 2: Run research
python main.py --name "Apple" --industry "Technology"

# Browser: Open http://localhost:6006
# Watch your traces appear in real-time!
```

---

## 📚 Full Guides

- **Phoenix Details:** See `start_phoenix.py`
- **All Local Options:** See `LOCAL_TRACING_GUIDE.md`
- **LangSmith Cloud:** See `LANGSMITH_GUIDE.md`
- **Visual Workflow:** See `demo_visual_workflow.py`

---

## 🤔 Still Have Questions?

**Q: Is Phoenix production-ready?**
A: Yes! Used by companies like Uber, Adobe. But for production, consider LangFuse for persistence.

**Q: Can I export Phoenix traces?**
A: Yes! Phoenix can export to JSON/Parquet for archival.

**Q: Does Phoenix work with other LLM providers?**
A: Yes! Works with OpenAI, Anthropic, Google, Groq, local models, etc.

**Q: Can I use multiple tools together?**
A: Yes! Use Phoenix for dev, LangSmith for prod, Visual Workflow for planning.

---

**Bottom Line:** You have excellent free, local options. Phoenix is the easiest to start with! 🎉
