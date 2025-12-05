# LangFuse Setup Guide - Self-Hosted Tracing

## 🎯 What is LangFuse?

LangFuse is a self-hosted alternative to LangSmith that gives you:
- **100% local control** - All data stays on your machine
- **Beautiful UI** - Similar to LangSmith
- **Full features** - Tracing, evaluation, datasets
- **No limits** - Unlimited traces, no rate limits
- **Open source** - Free forever

---

## 📋 Current Status

✓ Docker is installed and running
⏳ Docker is downloading LangFuse images (~200MB)
⏳ Waiting for containers to start...

---

## ⏱️ While You Wait (2-3 minutes)

The first download takes a few minutes. You can:
1. **Read this guide** (you are here!)
2. **Prepare your .env file** (instructions below)
3. **Understand the workflow** (see below)

---

## 🚀 Steps After Download Completes

### Step 1: Verify Containers are Running

```bash
docker ps --filter name=langfuse
```

You should see TWO containers:
- **langfuse-db** (PostgreSQL database)
- **langfuse-app** (LangFuse web application)

### Step 2: Access the Web UI

Open your browser and go to:
```
http://localhost:3000
```

### Step 3: Create Your Account

**Important:** This account is stored LOCALLY, not in the cloud!

1. Click "Sign Up"
2. Enter:
   - **Email:** your@email.com (any email, doesn't need to be real)
   - **Password:** (your choice)
   - **Name:** (your name)
3. Click "Create Account"

### Step 4: Create a Project

1. After logging in, click "Create Project"
2. **Project Name:** `company-researcher`
3. Click "Create"

### Step 5: Get Your API Keys

1. Go to **Settings** (gear icon)
2. Click **API Keys**
3. Click **"Create new secret key"**
4. Give it a name: "Local Development"
5. **IMPORTANT:** Copy both keys NOW (you can't see the secret key again):
   - **Public Key:** `pk-lf-...`
   - **Secret Key:** `sk-lf-...`

### Step 6: Update Your .env File

Add these lines to your `.env` file:

```env
# ===================================
# LANGFUSE (Self-Hosted Tracing)
# ===================================
LANGFUSE_PUBLIC_KEY=pk-lf-your-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-key-here
LANGFUSE_HOST=http://localhost:3000

# Optional: Disable LangSmith if using LangFuse
# LANGCHAIN_TRACING_V2=false
```

### Step 7: Install LangFuse Python SDK

```bash
pip install langfuse
```

### Step 8: Test the Integration

```bash
python test_langfuse_integration.py
```

You should see:
- ✓ Configuration loaded
- ✓ Test message sent
- ✓ Trace created

### Step 9: View Your First Trace

1. Go back to http://localhost:3000
2. Click on your project: **company-researcher**
3. You should see your test trace!
4. Click on it to see:
   - Complete execution tree
   - LLM prompts & responses
   - Token usage & costs
   - Execution time

---

## 🎮 Using LangFuse with Your Research

Once configured, all your LangChain calls will be automatically traced!

### Option A: Automatic Tracing (Recommended)

Add LangFuse callback to your code:

```python
from langfuse.callback import CallbackHandler

# Create handler
langfuse_handler = CallbackHandler()

# Use with any LangChain call
llm.invoke("Hello", config={"callbacks": [langfuse_handler]})
```

### Option B: Use with Your Main Research Script

```bash
# Run research - traces will appear in LangFuse
python main.py --name "Tesla" --industry "Automotive"
```

Make sure your code includes the LangFuse callback handler.

---

## 📊 What You'll See in LangFuse

### Dashboard View
```
Recent Traces:
├─ Tesla Research (5 min ago) - Success - $0.15
├─ Test Run (10 min ago) - Success - $0.02
└─ Apple Analysis (1 hour ago) - Success - $0.28
```

### Trace Detail View
```
Tesla Research (45s, $0.15)
│
├─ 🔍 Search Phase (15s)
│  ├─ Tavily Search: "Tesla financial data"
│  │  ├─ Input: {"query": "Tesla financial..."}
│  │  ├─ Output: 15 results found
│  │  └─ Cost: $0
│  │
│  ├─ LLM: Extract Information (8s, $0.04)
│  │  ├─ Model: gpt-3.5-turbo
│  │  ├─ Prompt: [View full prompt]
│  │  ├─ Response: [View full response]
│  │  ├─ Tokens: 1,234
│  │  └─ Cost: $0.04
│  │
│  └─ Result: Market data extracted
│
├─ 🌐 Browser Phase (20s)
│  ├─ Visit tesla.com
│  ├─ Extract content
│  └─ LLM: Summarize (5s, $0.06)
│
└─ ✅ Complete
   ├─ Total Duration: 45s
   ├─ Total Cost: $0.15
   └─ Status: Success
```

---

## 🛠️ Useful Commands

### Check Container Status
```bash
docker ps --filter name=langfuse
```

### View Logs
```bash
# View app logs
docker logs langfuse-app

# View database logs
docker logs langfuse-db

# Follow logs in real-time
docker logs -f langfuse-app
```

### Stop LangFuse
```bash
docker-compose -f docker-compose-langfuse.yml stop
```

### Start LangFuse (after stopping)
```bash
docker-compose -f docker-compose-langfuse.yml start
```

### Restart LangFuse
```bash
docker-compose -f docker-compose-langfuse.yml restart
```

### Remove LangFuse (including data)
```bash
docker-compose -f docker-compose-langfuse.yml down -v
```

---

## 🔧 Troubleshooting

### Issue: Containers won't start

**Check port conflicts:**
```bash
# Check if ports 3000 or 5432 are in use
netstat -ano | findstr :3000
netstat -ano | findstr :5432
```

**Solution:** Stop other services using these ports

### Issue: Can't access http://localhost:3000

**Check container status:**
```bash
docker ps --filter name=langfuse-app
```

**View logs:**
```bash
docker logs langfuse-app
```

**Wait longer:** First startup can take 30-60 seconds

### Issue: Traces not appearing

**Check API keys:**
- Public key starts with `pk-lf-`
- Secret key starts with `sk-lf-`
- Both are in `.env` file

**Flush traces manually:**
```python
langfuse_handler.langfuse.flush()
```

**Check network:**
```bash
# Test if LangFuse is accessible
curl http://localhost:3000
```

### Issue: "Database connection failed"

**Wait for database:**
- PostgreSQL takes 10-20 seconds to start
- Check with: `docker logs langfuse-db`

**Restart containers:**
```bash
docker-compose -f docker-compose-langfuse.yml restart
```

---

## 💡 Tips & Best Practices

1. **Keep Docker Desktop running**
   - LangFuse needs Docker to run
   - Start Docker Desktop automatically on system startup

2. **Backup your data**
   - Data is in Docker volume: `langfuse_db`
   - Export traces regularly from LangFuse UI

3. **Monitor disk space**
   - Traces accumulate over time
   - Delete old traces from UI Settings

4. **Use tags**
   - Tag traces with environment (dev/test/prod)
   - Tag with company name for filtering

5. **Create datasets**
   - Save good examples as test cases
   - Use for regression testing

---

## 📈 Next Steps

### After Setup Works:

1. **Integrate with your code**
   - Add LangFuse callback to main research functions
   - Configure automatic tracing

2. **Create dashboards**
   - Use LangFuse UI to create custom views
   - Track cost trends over time

3. **Set up evaluation**
   - Create golden test datasets
   - Run evaluations before releases

4. **Share with team** (optional)
   - Create accounts for team members
   - Share project access

---

## 🔐 Security Notes

- All data stays local (no cloud)
- Database accessible only on localhost
- API keys stored in PostgreSQL
- Use strong password for LangFuse account
- Don't expose port 3000 to internet

---

## 📚 Resources

- **LangFuse Docs:** https://langfuse.com/docs
- **Docker Docs:** https://docs.docker.com
- **Test Script:** `test_langfuse_integration.py`
- **Setup Helper:** `langfuse_setup_guide.py`

---

## ✅ Checklist

- [ ] Docker Desktop installed and running
- [ ] Containers downloaded and started
- [ ] Web UI accessible at http://localhost:3000
- [ ] Account created in LangFuse
- [ ] Project created: "company-researcher"
- [ ] API keys generated
- [ ] Keys added to `.env` file
- [ ] LangFuse Python SDK installed
- [ ] Test script runs successfully
- [ ] First trace visible in UI

---

**Once all checkboxes are complete, you're ready to go!** 🎉

Your LangChain flows will now be traced and visualized in your local LangFuse instance!
