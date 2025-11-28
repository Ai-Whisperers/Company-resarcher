# Tutorials

Step-by-step guides for learning Company Researcher.

## Learning Path

### Beginner

| Tutorial | Time | Description |
|----------|------|-------------|
| [Your First Research](./01-your-first-research.md) | 15-20 min | Set up and run your first research task |
| [Using the API](./02-using-the-api.md) | 20-30 min | Start research via REST API |

### Coming Soon

- **Customizing Output** - Modify report templates
- **Building Custom Agents** - Create specialized research agents
- **Adding Data Sources** - Integrate new tools and APIs
- **Production Deployment** - Deploy with Docker and cloud services

---

## Quick Reference

### Command Line

```bash
# Basic research
python main.py --name "Company" --industry "Industry"

# With website
python main.py --name "Company" --url "https://company.com"

# Free/local mode
python main.py --name "Company" --local
```

### API

```bash
# Start research
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Company"}'

# Check status
curl http://localhost:8000/api/v1/research/{task_id}
```

---

## Prerequisites

All tutorials assume you have:
- Python 3.10+
- Git
- A terminal/command prompt
- Text editor

Some tutorials require:
- API keys (OpenAI, Anthropic, Groq, or Tavily)
- Basic Python knowledge
- Familiarity with REST APIs

---

## Getting Help

- [Troubleshooting Guide](../guides/TROUBLESHOOTING.md)
- [FAQ](../FAQ.md)
- [GitHub Issues](https://github.com/Ai-Whisperers/Company-resarcher/issues)
