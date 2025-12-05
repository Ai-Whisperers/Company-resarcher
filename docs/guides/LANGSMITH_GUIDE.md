# LangSmith Integration Guide

## Overview

LangSmith is now configured for your **Company Researcher** project! This guide shows you how to view execution traces, debug issues, and monitor your AI agents.

---

## ✅ Current Configuration Status

Your `.env` file should have:

```env
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=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
LANGCHAIN_PROJECT=maga-campaign-generator
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Optional (if you get workspace warnings):
LANGSMITH_WORKSPACE_ID=your-workspace-id
```

**Status:** ✓ Basic tracing is working!

**Note:** You may need to add `LANGSMITH_WORKSPACE_ID` if you see warnings about "org-scoped API key".

---

## 🚀 Quick Start

### 1. Run a Test Research

```bash
# Simple test
python test_langsmith_clean.py

# Full research with tracing
python run_test_research.py

# Or use the main CLI
python main.py --name "Apple" --industry "Technology"
```

### 2. View Traces in LangSmith

1. **Open LangSmith Dashboard:**
   - Go to: [https://smith.langchain.com](https://smith.langchain.com)
   - Login with your account

2. **Select Your Project:**
   - Click on project: **maga-campaign-generator**
   - You'll see a list of all traces

3. **Explore a Trace:**
   - Click on any trace to see:
     - Complete execution tree
     - All LLM calls (prompts + responses)
     - Tool invocations (search, browser, API calls)
     - Timing breakdown
     - Token usage & costs
     - Error messages (if any)

---

## 📊 What You'll See in LangSmith

### Trace Components

```
Research Run: Tesla (Automotive)
│
├─ 🔍 Search Phase
│  ├─ Tavily Search: "Tesla financial reports"
│  │  ├─ Input: {"query": "Tesla financial reports"}
│  │  ├─ Output: 15 results
│  │  └─ Duration: 2.3s
│  │
│  ├─ LLM: Extract Key Information
│  │  ├─ Model: gpt-4o
│  │  ├─ Prompt: "Analyze these search results..."
│  │  ├─ Response: "Key findings: 1. Revenue..."
│  │  ├─ Tokens: 1,234 (input: 800, output: 434)
│  │  ├─ Cost: $0.024
│  │  └─ Duration: 3.2s
│  │
│  └─ Result: Market analysis complete
│
├─ 🌐 Browser Phase
│  ├─ Playwright: Visit tesla.com
│  ├─ Extract Content (4,500 chars)
│  └─ LLM: Summarize Company Info
│
├─ 🤖 Analysis Phase
│  ├─ LLM: Competitor Analysis
│  ├─ LLM: Market Positioning
│  └─ Result: Report generated
│
└─ ✅ Complete
   ├─ Total Duration: 45.8s
   ├─ Total Cost: $0.15
   └─ Status: Success
```

### Key Metrics Tracked

- **Latency**: Time for each step
- **Tokens**: Input/output token counts
- **Cost**: Estimated cost per call
- **Errors**: Any failures or exceptions
- **Feedback**: User ratings (thumbs up/down)

---

## 🎯 Common Use Cases

### 1. Debug Why a Research Failed

**Problem:** Research for "Company X" returned incomplete data

**Solution:**
1. Go to LangSmith
2. Find the failed trace
3. Expand the execution tree
4. Look for:
   - Red error nodes
   - Empty responses from tools
   - Timeout issues
   - Rate limit errors

### 2. Optimize LLM Costs

**Problem:** Research is too expensive

**Solution:**
1. Filter traces by cost
2. Find the most expensive calls
3. Check if:
   - Prompts are too long
   - You're using expensive models (GPT-4) when cheaper ones (GPT-3.5) would work
   - There are unnecessary repeated calls

### 3. Improve Prompt Quality

**Problem:** LLM responses are not good enough

**Solution:**
1. View the exact prompts sent
2. See the responses received
3. Iterate on prompt design
4. Compare before/after traces

### 4. Monitor Production

**Problem:** Need to track success rates in production

**Solution:**
1. Use LangSmith's dashboard filters
2. Track:
   - Success rate over time
   - Average latency
   - Error frequency
   - User feedback scores

---

## 🔍 Advanced Features

### Feedback Collection

Add user feedback to traces:

```python
from langsmith import Client

client = Client()
client.create_feedback(
    run_id="abc123",  # From trace
    key="user_rating",
    score=0.8,  # 0-1 scale
    comment="Good analysis, but missed competitors"
)
```

### Datasets & Evaluation

Create test datasets:

```python
from langsmith import Client

client = Client()

# Create dataset
dataset = client.create_dataset("company-research-golden-set")

# Add examples
client.create_example(
    dataset_id=dataset.id,
    inputs={"company_name": "Apple", "industry": "Technology"},
    outputs={"competitors": ["Microsoft", "Google", "Samsung"]}
)
```

### Custom Tags

Tag traces for better filtering:

```python
from langchain.callbacks import LangChainTracer

tracer = LangChainTracer(
    tags=["production", "high-priority"],
    metadata={
        "user_id": "user123",
        "version": "v2.0"
    }
)
```

---

## 🛠️ Troubleshooting

### Issue: "Workspace ID required"

**Solution:** Add to `.env`:
```env
LANGSMITH_WORKSPACE_ID=ws_xxxxx
```

Find your workspace ID:
1. Go to https://smith.langchain.com
2. Settings → Workspace
3. Copy the Workspace ID

### Issue: "Traces not appearing"

**Checklist:**
- [ ] `LANGCHAIN_TRACING_V2=true` in `.env`
- [ ] Valid `LANGCHAIN_API_KEY`
- [ ] Internet connection working
- [ ] Not using a firewall that blocks api.smith.langchain.com

**Debug:**
```python
import os
print(os.getenv("LANGCHAIN_TRACING_V2"))  # Should be "true"
print(os.getenv("LANGCHAIN_API_KEY")[:10])  # Should show "lsv2_pt_ca"
```

### Issue: "Rate limit exceeded"

**Solution:**
- Free tier: 5,000 traces/month
- Upgrade at: https://smith.langchain.com/settings/billing

### Issue: "Traces are slow to appear"

- Traces are sent asynchronously
- Can take 5-30 seconds to appear in dashboard
- Refresh the page if needed

---

## 📚 Documentation Links

- **LangSmith Docs:** https://docs.smith.langchain.com
- **LangChain Docs:** https://python.langchain.com/docs
- **API Reference:** https://api.python.langchain.com

---

## 🎓 Learning Resources

### Tutorials

1. **Getting Started with LangSmith**
   - https://docs.smith.langchain.com/tutorials

2. **Evaluating LLM Applications**
   - https://docs.smith.langchain.com/evaluation

3. **Production Monitoring**
   - https://docs.smith.langchain.com/monitoring

### Video Guides

1. **LangSmith Overview** (10 min)
   - https://www.youtube.com/watch?v=xxx

2. **Debugging with LangSmith** (15 min)
   - https://www.youtube.com/watch?v=xxx

---

## 💡 Tips & Best Practices

1. **Tag Everything**
   - Use tags for environment (dev/staging/prod)
   - Add metadata for user IDs, versions, etc.

2. **Create Golden Datasets**
   - Save good outputs as test cases
   - Run evaluations before deploying

3. **Monitor Costs**
   - Set up alerts for unusual spending
   - Track cost per research

4. **Use Feedback**
   - Add thumbs up/down in your UI
   - Send feedback to LangSmith
   - Use it to improve prompts

5. **Compare Runs**
   - Use "Compare" feature to A/B test prompts
   - Track improvements over time

---

## 🚀 Next Steps

1. ✅ **Test Basic Tracing** (You've done this!)
   ```bash
   python test_langsmith_clean.py
   ```

2. ✅ **Run Full Research**
   ```bash
   python run_test_research.py
   ```

3. **Explore LangSmith Dashboard**
   - View traces
   - Analyze costs
   - Identify bottlenecks

4. **Set Up Datasets**
   - Create golden test cases
   - Run evaluations

5. **Production Monitoring**
   - Track success rates
   - Monitor costs
   - Collect user feedback

---

## 📞 Support

- **LangSmith Issues:** support@langchain.dev
- **Project Issues:** Create a GitHub issue
- **Documentation:** docs.smith.langchain.com

---

**Happy Debugging! 🎉**

Your traces are now being captured. Go to [smith.langchain.com](https://smith.langchain.com) to see them in action!
