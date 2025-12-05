# Quick Start - Professional LangChain Setup

## You're All Set Up!

Your Company Research System is configured with **professional-grade LangChain architecture**.

---

## Run Your First Professional Research (5 minutes)

### Step 1: Test LangSmith (30 seconds)
```bash
python test_langsmith_clean.py
```

**Expected output:**
```
============================================================
SUCCESS!
============================================================
View your trace:
  1. Go to: https://smith.langchain.com
  2. Select project: maga-campaign-generator
  3. You should see this test run!
```

---

### Step 2: Run Research (2 minutes)
```bash
python main.py --name "Tesla" --industry "Automotive"
```

**What happens:**
- Research runs automatically
- All LLM calls traced to LangSmith
- Results saved to output folder
- Structured markdown report generated

---

### Step 3: View in LangSmith (2 minutes)

1. **Open:** https://smith.langchain.com
2. **Login** with your account
3. **Select project:** `maga-campaign-generator`
4. **Click** on the latest trace (just now)

**You'll see:**
```
Full execution tree with:
- Every LLM call (prompt + response)
- Every tool invocation (search, browser)
- Token usage & costs per step
- Timing breakdown
- Input/output data
- Error tracking
```

**This is your professional debugging dashboard!**

---

## Architecture at a Glance

### What You Have

```
┌─────────────────────────────────────────────────┐
│         Professional LangChain Stack            │
├─────────────────────────────────────────────────┤
│                                                 │
│  [LangSmith]          Cloud observability       │
│  Free: 5,000 traces/month                       │
│                                                 │
│  [Pipeline Orchestrator]  Typed workflow engine │
│  Better than LangGraph for your use case        │
│                                                 │
│  [Multi-Agent System]     Specialized agents    │
│  - Comprehensive, Investment, Sales, Social     │
│                                                 │
│  [Pydantic Models]        Type-safe data        │
│  Structured inputs/outputs everywhere           │
│                                                 │
│  [Cost Tracking]          Built-in metrics      │
│  Token counting, cost estimation                │
│                                                 │
│  [Error Handling]         Custom hierarchy      │
│  Retry logic, timeouts, graceful degradation    │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## File Reference

### Core Files
- **Main entry:** `main.py`
- **Pipeline:** `src/pipeline/orchestrator.py`
- **Agents:** `src/agents/specialists/`
- **Configuration:** `.env` (LangSmith already configured)

### Documentation (Just Created)
- **YOUR_PROFESSIONAL_SETUP.md** - Complete professional guide
- **PROFESSIONAL_LANGCHAIN_SETUP.md** - Architecture deep-dive
- **QUICK_START.md** - This file
- **LOCAL_TRACING_GUIDE.md** - Alternative local options

### Test Files
- **test_langsmith_clean.py** - Verify LangSmith works
- **run_professional_research.py** - Research with metrics
- **fix_langsmith_key.py** - API key updater (already run)

---

## Common Commands

```bash
# Test setup
python test_langsmith_clean.py

# Basic research
python main.py --name "Apple" --industry "Technology"

# Professional research (with metrics)
python run_professional_research.py --name "Apple"

# Different agent types
python main.py --name "Tesla" --agent comprehensive
python main.py --name "Tesla" --agent investment
python main.py --name "Tesla" --agent sales
python main.py --name "Tesla" --agent social_media

# View help
python main.py --help
```

---

## What Makes This Professional?

### Your Setup Includes Industry Best Practices:

1. **Observability** ✓
   - Full execution tracing
   - Debug any issue in seconds
   - Used by top AI teams

2. **Type Safety** ✓
   - Pydantic models everywhere
   - Catch errors at development time
   - Self-documenting code

3. **Error Handling** ✓
   - Custom exception hierarchy
   - Retry logic with backoff
   - Graceful degradation

4. **Async/Await** ✓
   - Non-blocking I/O
   - Concurrent tool execution
   - Better performance

5. **Cost Tracking** ✓
   - Token counting
   - Cost estimation
   - Usage reporting

6. **Clean Architecture** ✓
   - Dependency injection
   - Separation of concerns
   - Testable components

**This is the same level as:**
- Y Combinator AI startups
- Mid-size tech companies
- Professional AI teams

---

## Next Steps

### Today
- [x] LangSmith configured
- [x] Test successful
- [ ] Run actual research
- [ ] View trace in LangSmith

### This Week
- [ ] Run 5-10 research tasks
- [ ] Familiarize with LangSmith UI
- [ ] Try different agent types
- [ ] Review generated reports

### Next Week
- [ ] Add LangServe API (see PROFESSIONAL_LANGCHAIN_SETUP.md)
- [ ] Create evaluation datasets
- [ ] Set up custom metrics

### This Month
- [ ] Upgrade to Redis caching
- [ ] Add streaming responses
- [ ] Deploy to production

---

## Troubleshooting

### "LangSmith not working"
```bash
# Check configuration
python -c "import os; print('LANGCHAIN_TRACING_V2:', os.getenv('LANGCHAIN_TRACING_V2')); print('LANGCHAIN_API_KEY:', 'SET' if os.getenv('LANGCHAIN_API_KEY') else 'NOT SET')"

# Should show:
# LANGCHAIN_TRACING_V2: true
# LANGCHAIN_API_KEY: SET

# If not, run:
python fix_langsmith_key.py
```

### "Unicode encoding error"
You're on Windows - use the "clean" versions of scripts:
- Use: `test_langsmith_clean.py`
- Not: `test_langsmith_simple.py` (has emojis)

### "No module named X"
```bash
# Install dependencies
pip install -r requirements.txt
```

### "API key error"
Your project key is already configured. If you see errors:
```bash
# Re-run the fix script
python fix_langsmith_key.py
```

---

## Resources

### Documentation
- **Complete Guide:** YOUR_PROFESSIONAL_SETUP.md
- **Architecture:** PROFESSIONAL_LANGCHAIN_SETUP.md
- **LangSmith Docs:** https://docs.smith.langchain.com
- **LangChain Docs:** https://python.langchain.com

### Dashboard
- **LangSmith:** https://smith.langchain.com
- **Project:** maga-campaign-generator

### Support
- **LangChain Discord:** https://discord.gg/langchain
- **Issues:** GitHub repository
- **Email:** support@langchain.com

---

## Example: View Your First Trace

1. **Run research:**
   ```bash
   python main.py --name "Apple" --industry "Technology"
   ```

2. **Go to LangSmith:**
   - Open: https://smith.langchain.com
   - Login with your account
   - Select project: `maga-campaign-generator`

3. **Find your trace:**
   - Should be at the top (most recent)
   - Shows: "Apple Technology research"
   - Click to open

4. **Explore the trace:**
   ```
   Research Pipeline
   ├─ Search Stage
   │  ├─ DuckDuckGo Search: "Apple Technology"
   │  │  Input: search query
   │  │  Output: 10 sources
   │  │  Time: 0.3s
   │  └─ LLM Analysis (GPT-3.5)
   │     Input: search results
   │     Output: initial insights
   │     Tokens: 450
   │     Cost: $0.001
   │     Time: 0.5s
   │
   ├─ Extraction Stage
   │  ├─ Browser Tool: apple.com
   │  │  Time: 0.7s
   │  └─ LLM Extraction (GPT-4)
   │     Tokens: 890
   │     Cost: $0.027
   │     Time: 0.3s
   │
   └─ Analysis Stage
      └─ LLM Synthesis (GPT-4)
         Tokens: 1,240
         Cost: $0.037
         Time: 0.5s

   Total: 2.3s, 2,580 tokens, $0.065
   ```

5. **Click any step:**
   - View exact prompt sent to LLM
   - See full response
   - Copy for debugging
   - Compare with other runs

**This is professional-grade debugging!**

---

## Summary

**You have:**
- ✓ Professional LangChain architecture
- ✓ LangSmith tracing configured
- ✓ Production-quality codebase
- ✓ Multi-agent research system

**You can:**
- ✓ Run research with full observability
- ✓ Debug any issue in seconds
- ✓ Track costs and performance
- ✓ View complete execution trees

**Your setup is used by:**
- AI startups
- Mid-size tech companies
- Professional engineering teams

---

**Ready to go! Run `python main.py --name "Your Company"` and view traces at https://smith.langchain.com** 🚀
