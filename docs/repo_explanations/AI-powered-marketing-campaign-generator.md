# AI-powered-marketing-campaign-generator

**Description:** 
**URL:** https://github.com/Ai-Whisperers/AI-powered-marketing-campaign-generator
**Visibility:** PRIVATE

---

# Marketing Agent 🎯

> AI-powered marketing campaign generator with automated research, ideation, and video creation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Overview

Marketing Agent is an enterprise-grade AI system that automates the entire marketing campaign creation process, from research to video generation. Built for marketing agencies and brands, it combines multiple AI providers to deliver high-quality campaigns at a fraction of the traditional cost.

### Key Features

- 🔍 **Automated Research**: Multi-source market research with GPT Researcher
- 💡 **AI Ideation**: Two-phase generation producing 13 strategic fields per idea
- 🎬 **Video Generation**: Veo 3.1 integration with automated brand guidelines
- 💰 **Cost Optimized**: Hybrid Groq/OpenAI approach (~$0.01 per campaign)
- 🎨 **Brand Consistency**: Automated brand identity in all outputs
- ⚡ **Fast**: 80%+ time savings with intelligent caching
- 📊 **Scalable**: Batch processing with parallel execution

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- API Keys: Groq, OpenAI, Tavily, Google Cloud (for Veo 3.1)

### Installation

```bash
# Clone the repository
git clone https://github.com/Ai-Whisperers/Marketing-Agent.git
cd Marketing-Agent

# Install dependencies
pip install -r code/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```bash
# Generate campaign ideas
python code/cli.py generate \
  --project-id nestle-paraguay \
  --num-ideas 15

# Generate branded video prompts
python code/cli.py generate-branded-videos \
  --project-id nestle-paraguay \
  --prompts-only

# Generate actual videos (costs money)
python code/cli.py generate-branded-videos \
  --project-id nestle-paraguay
```

## 📖 Documentation

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Marketing Agent                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Research   │→ │   Ideation   │→ │    Critique  │      │
│  │   (Groq)     │  │ (2-Phase AI) │  │    (Groq)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                  ↓                  ↓              │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Brand Context Service                   │      │
│  │     (Nestlé colors, logo, visual identity)       │      │
│  └──────────────────────────────────────────────────┘      │
│         ↓                                                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Batch Video Agent (Veo 3.1)              │      │
│  │    Automated branded video generation             │      │
│  └──────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Two-Phase Ideation

**Phase 1**: Generate base concepts (6 fields)

- Title, Description, Rationale
- Target Audience, Channels, KPIs

**Phase 2**: Enrich with strategic fields (7 fields)

- Budget Tier, Timeline, Key Message
- Call to Action, Sustainability Component
- Risks, Success Factors

### AI Provider Strategy

| Task      | Primary | Fallback | Cost         |
| --------- | ------- | -------- | ------------ |
| Research  | Groq    | -        | $0.00        |
| Synthesis | Groq    | -        | $0.00        |
| Ideation  | Groq    | OpenAI   | ~$0.01       |
| Critique  | Groq    | -        | $0.00        |
| Videos    | Veo 3.1 | -        | ~$0.20/video |

## 🎨 Brand Context System

Automatically applies brand guidelines to all generated content:

```python
from api.services.brand_context import get_brand_context

brand = get_brand_context("paraguay")
print(brand.get_veo_brand_instructions())
# Outputs: Nestlé colors, logo placement, visual style
```

### Supported Brand Elements

- ✅ Color palette (primary, secondary, accents)
- ✅ Logo placement rules
- ✅ Visual style guidelines
- ✅ Typography specifications
- ✅ Market-specific cultural context

## 📊 Performance

### Speed

- **Research**: ~2-3 minutes (first run)
- **Research**: ~10 seconds (cached)
- **Ideation**: ~30 seconds for 15 ideas
- **Video Prompts**: ~5 minutes for 15 ideas
- **Videos**: ~30-60 minutes for 15 videos

### Cost Comparison

| Traditional      | Marketing Agent | Savings |
| ---------------- | --------------- | ------- |
| $50-100/campaign | ~$0.01/campaign | 99%+    |
| 2-4 hours        | 5-10 minutes    | 95%+    |

## 🛠️ Tech Stack

- **Agent Framework**: LangGraph
- **AI Providers**: Groq, OpenAI, Anthropic
- **Research**: GPT Researcher, Tavily
- **Video**: Google Veo 3.1 via Vertex AI
- **Caching**: Redis + File-based
- **Database**: PostgreSQL (optional)

## 📁 Project Structure

```
marketing-agent/
├── code/
│   ├── api/
│   │   ├── graphs/
│   │   │   └── campaign_graph.py      # Main agent workflow
│   │   ├── services/
│   │   │   ├── brand_context.py       # Brand guidelines
│   │   │   ├── batch_video_agent.py   # Video automation
│   │   │   ├── ideas_service.py       # Ideation logic
│   │   │   └── research_service.py    # Research automation
│   │   └── routes/                    # FastAPI endpoints
│   ├── cli.py                         # Command-line interface
│   └── requirements.txt
├── data/
│   └── campaign_memory/               # RAG memory storage
├── .env.example                       # Environment template
└── README.md
```

## 🔧 Configuration

### Environment Variables

```bash
# AI Providers
AI_PRIMARY_PROVIDER=groq
AI_FALLBACK_PROVIDER=openai
GROQ_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Research
TAVILY_API_KEY=your_key_here

# Video Generation (optional)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS_JSON='{...}'
```

### Advanced Configuration

See `code/config/default.yaml` for:

- Research depth settings
- Caching configuration
- Video generation parameters
- Model selection

## 🎯 Use Cases

### Marketing Agencies

- Generate 15+ campaign concepts in minutes
- Automated brand-compliant video creation
- Multi-market campaign adaptation

### Brands

- Rapid campaign ideation
- Consistent brand application
- Cost-effective video production

### Freelancers

- Professional campaign proposals
- Quick client presentations
- Scalable creative output

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install dev dependencies
pip install -r code/requirements-dev.txt

# Run tests
pytest code/tests/

# Format code
black code/
ruff check code/
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [GPT Researcher](https://github.com/assafelovic/gpt-researcher)
- Video generation via [Google Veo 3.1](https://deepmind.google/technologies/veo/)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Ai-Whisperers/Marketing-Agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ai-Whisperers/Marketing-Agent/discussions)
- **Email**: support@ai-whisperers.com

---

**Made with ❤️ by [Ai-Whisperers](https://github.com/Ai-Whisperers)**
