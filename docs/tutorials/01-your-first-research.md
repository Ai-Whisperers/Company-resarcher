# Tutorial: Your First Company Research

**Time:** 15-20 minutes
**Level:** Beginner
**Prerequisites:** Python 3.10+, API key (OpenAI or alternative)

## What You'll Learn

- How to set up Company Researcher
- How to run your first research task
- How to understand the output reports
- How to customize research parameters

---

## Before You Start

You'll need:
- Python 3.10 or higher installed
- At least one LLM API key (OpenAI, Anthropic, Groq, or Ollama)
- A terminal/command prompt
- 10-15 minutes of time

---

## Step 1: Clone and Install

Open your terminal and run:

```bash
# Clone the repository
git clone https://github.com/Ai-Whisperers/Company-resarcher.git
cd Company-resarcher

# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Expected Result:** All packages install without errors.

> **Troubleshooting:** If you see errors, ensure you have Python 3.10+ with `python --version`.

---

## Step 2: Install Browser (for Web Scraping)

The system uses Playwright for web scraping:

```bash
playwright install chromium
```

**Expected Result:** Chromium browser downloads (~150MB).

---

## Step 3: Configure API Keys

Create a `.env` file in the project root:

```bash
# On Windows:
copy NUL .env
# On macOS/Linux:
touch .env
```

Open `.env` in your text editor and add your API key:

```env
# Option 1: OpenAI (recommended for best results)
OPENAI_API_KEY=sk-your-key-here

# Option 2: Anthropic
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# Option 3: Groq (free tier available)
# GROQ_API_KEY=gsk_your-key-here

# Search API (recommended)
TAVILY_API_KEY=tvly-your-key-here
```

> **Tip:** Get a free Tavily key at [tavily.com](https://tavily.com) for better search results.

> **Free Option:** Skip API keys entirely and use `--local` flag (uses DuckDuckGo + Ollama).

---

## Step 4: Run Your First Research

Let's research a well-known company:

```bash
python main.py --name "Notion" --industry "Productivity Software"
```

**What happens:**
1. System initializes agents
2. Wave 1: Agents gather data (financial, market, competitors, brand, sales)
3. Wave 2: InsightGenerator analyzes findings
4. Wave 3: Reports are generated and reviewed

**Expected Output:**
```
🔍 Starting research for: Notion
📊 Industry: Productivity Software

[Wave 1: Gathering] ████████████████████ 100%
  ✓ FinancialAgent completed
  ✓ MarketAnalyst completed
  ✓ CompetitorScout completed
  ✓ BrandAuditor completed
  ✓ SalesAgent completed

[Wave 2: Analysis] ████████████████████ 100%
  ✓ InsightGenerator completed

[Wave 3: Writing] ████████████████████ 100%
  ✓ Reports generated
  ✓ LogicCritic review completed

✅ Research completed!
📁 Output saved to: output/Notion/
```

**Time:** This typically takes 5-15 minutes depending on your LLM provider.

---

## Step 5: Explore the Output

Navigate to the output folder:

```bash
# On Windows:
dir output\Notion

# On macOS/Linux:
ls output/Notion/
```

You'll see folders like:
```
output/Notion/
├── 00-Strategic-Context/
│   ├── Company-Overview.md
│   └── Key-People.md
├── 01-Market-Intelligence/
│   ├── Market-Size.md
│   └── Industry-Trends.md
├── 02-Target-Audience/
├── 03-Competitive-Landscape/
├── 04-Brand-Strategy/
├── 05-Marketing-Execution/
├── 06-Data-Room/
│   └── Financials.md
├── 07-Creative-Inspiration/
└── 99-Sources/
    ├── raw/
    └── Source-Log.md
```

---

## Step 6: Read Key Reports

Open the main overview:

```bash
# View company overview
cat output/Notion/00-Strategic-Context/Company-Overview.md
```

**Example content:**
```markdown
# Company Overview: Notion

## Summary
Notion is a productivity and note-taking application that combines
notes, databases, kanban boards, wikis, and calendars...

## Key Facts
- **Founded:** 2013
- **Headquarters:** San Francisco, CA
- **Employees:** 500+
- **Valuation:** $10B (as of last funding round)

## Business Model
Freemium SaaS with team/enterprise tiers...
```

---

## Step 7: Check Sources

All data is traceable. View the source log:

```bash
cat output/Notion/99-Sources/Source-Log.md
```

**Example:**
```markdown
# Source Log

## Sources Used

1. **Notion - About Page**
   - URL: https://notion.so/about
   - Type: web
   - Accessed: 2024-01-15 10:30:00

2. **TechCrunch: Notion Valuation**
   - URL: https://techcrunch.com/...
   - Type: news
   - Accessed: 2024-01-15 10:31:00
```

---

## Step 8: Try Advanced Options

### Research with Website URL

Providing the URL improves accuracy:

```bash
python main.py --name "Figma" --url "https://figma.com" --industry "Design Tools"
```

### Local Mode (Free, No API Keys)

Use Ollama + DuckDuckGo:

```bash
# First, ensure Ollama is running with a model
ollama pull llama3.1:8b
ollama serve

# Then run with --local flag
python main.py --name "Slack" --local
```

---

## Verification Checklist

After completing this tutorial, verify:

- [ ] Virtual environment created and activated
- [ ] Dependencies installed successfully
- [ ] At least one API key configured
- [ ] Research completed without errors
- [ ] Output folder contains reports
- [ ] You can read the generated markdown files

---

## Common Issues

### "No AI provider configured"

**Solution:** Ensure your `.env` file has at least one valid API key.

### Research takes too long

**Solutions:**
- Use Groq (fastest provider)
- Reduce scope with specific industry
- Check internet connection

### Empty or minimal results

**Solutions:**
- Provide website URL for better data
- Ensure company name is spelled correctly
- Try a more well-known company first

---

## Next Steps

Now that you've completed your first research:

1. **Try the REST API** - See [API Reference](../api/API_REFERENCE.md)
2. **Explore configuration** - See [Configuration Guide](../guides/CONFIGURATION.md)
3. **Optimize performance** - See [Performance Guide](../guides/PERFORMANCE.md)
4. **Build custom agents** - See [Examples](../examples/README.md)

---

## Summary

You've learned how to:
- ✅ Set up Company Researcher
- ✅ Configure API keys
- ✅ Run a research task
- ✅ Navigate the output structure
- ✅ Trace data back to sources

**Congratulations!** You're ready to research any company.
