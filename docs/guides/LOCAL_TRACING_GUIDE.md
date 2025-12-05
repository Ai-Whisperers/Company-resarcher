# Local Tracing & Visualization Guide

**100% Free, Open Source, No Cloud Required**

This guide shows you how to trace and visualize your LangChain flows completely locally, without any paid services.

---

## 🆓 Quick Fix: LangSmith Free Tier (Still Cloud)

If you want to use LangSmith's free tier, just fix your API key:

**Current issue:** You're using the service key (`lsv2_sk_...`) which requires paid workspaces.

**Solution:** Use the project key instead:

```env
# In .env - Replace the service key with project key
LANGCHAIN_API_KEY=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
```

**Free tier includes:**
- 5,000 traces/month
- 14-day retention
- Full UI & debugging features
- No credit card required

---

## 🏠 Local Alternatives (No Cloud, 100% Free)

### **Option 1: LangFuse (Self-Hosted) ⭐ RECOMMENDED**

**Pros:**
- Beautiful UI (similar to LangSmith)
- Full LangChain integration
- Runs in Docker
- Evaluation & datasets support
- Open source

**Setup:**

```bash
# 1. Start LangFuse with Docker
docker-compose -f docker-compose-langfuse.yml up -d

# 2. Open browser
open http://localhost:3000

# 3. Create account (stored locally, no cloud)

# 4. Get API keys from Settings

# 5. Add to .env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

**Install Python SDK:**
```bash
pip install langfuse
```

**Use in code:**
```python
from langfuse.callback import CallbackHandler

# Add to your LangChain calls
handler = CallbackHandler()
llm.invoke("Hello", config={"callbacks": [handler]})
```

**Dashboard:** http://localhost:3000

---

### **Option 2: Phoenix by Arize 🔥 EASIEST**

**Pros:**
- Zero configuration
- Automatic instrumentation
- Real-time streaming
- Beautiful visualizations
- Runs as single Python process

**Setup:**

```bash
# 1. Install
pip install arize-phoenix openinference-instrumentation-langchain

# 2. Start Phoenix and run your code
python setup_phoenix_local.py

# 3. In another terminal, run research
python main.py --name "Tesla" --industry "Automotive"
```

**Dashboard:** http://localhost:6006

**Code Integration:**
```python
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

# Launch Phoenix
session = px.launch_app()
tracer_provider = register(endpoint=f"{session.url}/v1/traces")

# Instrument LangChain (automatic tracing)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# Now all LangChain calls are automatically traced!
```

---

### **Option 3: Built-in Visual Workflow 🎨 NO INSTALL**

**Pros:**
- Already in your codebase!
- Export to JSON/YAML/Mermaid
- Visualize with free tools
- Full workflow control

**Setup:**

```bash
# Run the demo
python demo_visual_workflow.py
```

**Outputs:**
- `workflow_exports/research_workflow.json` - Import to Draw.io
- `workflow_exports/research_workflow.mmd` - View at mermaid.live
- `workflow_exports/workflow_nodes.md` - Documentation
- `workflow_exports/execution_trace.json` - Execution details

**Visualize:**
1. **Mermaid Live**: Copy `.mmd` file to https://mermaid.live
2. **Draw.io**: Import `.json` file at https://app.diagrams.net
3. **VS Code**: Install Mermaid Preview extension

---

### **Option 4: LangServe (API + Playground)**

**Pros:**
- Built by LangChain team
- Interactive playground UI
- REST API automatically generated
- Good for testing prompts

**Setup:**

```bash
pip install "langserve[all]"
```

Create `serve_research.py`:
```python
from fastapi import FastAPI
from langserve import add_routes
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

app = FastAPI(
    title="Company Research API",
    description="Local LangChain Playground"
)

# Your research chain
prompt = ChatPromptTemplate.from_template("Research {company_name}")
model = ChatOpenAI()
chain = prompt | model

# Add to playground
add_routes(app, chain, path="/research")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Start:**
```bash
python serve_research.py
```

**Playground:** http://localhost:8000/research/playground

---

### **Option 5: OpenLLMetry (OpenTelemetry)**

**Pros:**
- Industry standard (OpenTelemetry)
- Works with Jaeger, Zipkin, Grafana
- Production-ready
- Vendor-neutral

**Setup with Jaeger:**

```bash
# 1. Start Jaeger (all-in-one Docker)
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# 2. Install OpenLLMetry
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
pip install traceloop-sdk

# 3. Instrument LangChain
from traceloop.sdk import Traceloop
Traceloop.init(app_name="company-researcher")

# All LangChain calls now traced!
```

**Dashboard:** http://localhost:16686

---

## 📊 Comparison Table

| Tool | Setup | UI Quality | LangChain Support | Storage | Best For |
|------|-------|------------|-------------------|---------|----------|
| **LangFuse** | Docker | ⭐⭐⭐⭐⭐ | Native | PostgreSQL | Production-like setup |
| **Phoenix** | pip install | ⭐⭐⭐⭐ | Auto-instrument | In-memory | Quick debugging |
| **Visual Workflow** | Built-in | ⭐⭐⭐ | Manual | JSON files | Workflow design |
| **LangServe** | pip install | ⭐⭐⭐ | Native | None | Testing chains |
| **OpenLLMetry** | Docker + pip | ⭐⭐⭐⭐ | Auto-instrument | Jaeger DB | Enterprise/Production |
| **LangSmith Free** | Cloud setup | ⭐⭐⭐⭐⭐ | Native | Cloud | Limited use |

---

## 🚀 Quick Start Recommendations

### For Debugging (Start Here)
```bash
# Easiest: Phoenix
pip install arize-phoenix openinference-instrumentation-langchain
python setup_phoenix_local.py
```

### For Production-Like Setup
```bash
# Best: LangFuse
docker-compose -f docker-compose-langfuse.yml up -d
# Open: http://localhost:3000
```

### For Workflow Design
```bash
# Built-in: Visual Workflow
python demo_visual_workflow.py
# Then open: workflow_exports/research_workflow.mmd at mermaid.live
```

---

## 🎯 Step-by-Step: Phoenix (Recommended for You)

**1. Install:**
```bash
pip install arize-phoenix openinference-instrumentation-langchain
```

**2. Create startup script** (`start_phoenix.py`):
```python
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

# Launch Phoenix UI
session = px.launch_app()
print(f"Phoenix running at: {session.url}")

# Setup tracing
tracer = register(endpoint=f"{session.url}/v1/traces")
LangChainInstrumentor().instrument(tracer_provider=tracer)

print("\nNow run your research in another terminal!")
print("Example: python main.py --name 'Tesla' --industry 'Automotive'")

# Keep running
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping Phoenix...")
```

**3. Start Phoenix:**
```bash
python start_phoenix.py
```

**4. In another terminal, run research:**
```bash
python main.py --name "Apple" --industry "Technology"
```

**5. View traces:**
Open http://localhost:6006 - you'll see:
- Complete execution tree
- All LLM calls with prompts/responses
- Token usage & latency
- Error tracking
- Timeline visualization

---

## 🔧 Troubleshooting

### Phoenix not showing traces?

**Check Python SDK:**
```bash
pip list | grep phoenix
pip list | grep openinference
```

**Verify instrumentation:**
```python
from openinference.instrumentation.langchain import LangChainInstrumentor
print(LangChainInstrumentor().is_instrumented())  # Should be True
```

### LangFuse container won't start?

**Check Docker:**
```bash
docker ps
docker logs langfuse-app
```

**Reset database:**
```bash
docker-compose -f docker-compose-langfuse.yml down -v
docker-compose -f docker-compose-langfuse.yml up -d
```

---

## 💡 Pro Tips

1. **Use Phoenix for development**
   - Super fast to start
   - No configuration needed
   - Perfect for debugging

2. **Use LangFuse for team work**
   - Persistent storage
   - User accounts
   - Evaluation features

3. **Use Visual Workflow for design**
   - Plan before coding
   - Document complex flows
   - Share with non-technical stakeholders

4. **Export everything**
   - Phoenix can export to JSON
   - LangFuse has export API
   - Visual Workflow saves automatically

---

## 🎓 Next Steps

1. **Try Phoenix first** (easiest):
   ```bash
   pip install arize-phoenix openinference-instrumentation-langchain
   python setup_phoenix_local.py
   ```

2. **Run a test**:
   ```bash
   python main.py --name "Tesla"
   ```

3. **View dashboard**:
   Open http://localhost:6006

4. **If you like it**, keep using Phoenix

5. **If you need more features**, try LangFuse:
   ```bash
   docker-compose -f docker-compose-langfuse.yml up -d
   ```

---

## 📚 Resources

- **Phoenix Docs**: https://docs.arize.com/phoenix
- **LangFuse Docs**: https://langfuse.com/docs
- **Visual Workflow**: See `src/core/workflow/visual_workflow.py`
- **Mermaid Live**: https://mermaid.live
- **Draw.io**: https://app.diagrams.net

---

**You're all set for local tracing! No cloud, no costs, full control.** 🎉
