# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive documentation suite:
  - API Reference documentation
  - Setup and installation guide
  - Configuration reference
  - Troubleshooting guide
- Documentation backlog tracking (25 issues identified)

### Changed

- Updated README with correct documentation links
- Reorganized documentation structure

## [1.0.0] - 2024-XX-XX

### Added

- **Multi-Agent Research System**
  - ResearchOrchestrator for coordinating research workflow
  - Specialist agents: FinancialAgent, MarketAnalyst, CompetitorScout, BrandAuditor, SalesAgent
  - InsightGenerator for cross-referencing data
  - ReportWriter for markdown generation
  - LogicCritic for QA and feedback loops

- **LangGraph Architecture**
  - StateGraph-based workflow orchestration
  - 3-Wave execution model (Gathering, Analysis, Writing)
  - ResearchState blackboard pattern for agent communication

- **AI Provider Support**
  - OpenAI (GPT-4o)
  - Anthropic (Claude 3.5 Sonnet)
  - Google Gemini (Gemini 2.0 Flash)
  - Groq (Llama 3.1)
  - Ollama (local models)

- **Smart AI Client**
  - Multi-provider abstraction
  - Automatic fallback on rate limits
  - Response caching layer
  - Rate limiting to prevent 429 errors
  - Smart router for model selection by task complexity

- **Research Tools**
  - Web browser with Playwright (anti-bot handling)
  - Tavily search integration
  - DuckDuckGo fallback search
  - Financial data via yfinance
  - News aggregation via NewsAPI
  - SEC filings scraper
  - YouTube video/transcript search
  - PDF parsing with LlamaParse
  - Structured data extraction

- **REST API**
  - FastAPI-based async API
  - Background task processing
  - Rate limiting (10 req/min per IP)
  - Request size limits
  - Health check endpoints
  - SQLite/PostgreSQL task persistence

- **Output System**
  - V2 Research Schema with 20+ report types
  - Jinja2 templating for consistent output
  - Source tracking and audit logging
  - Markdown report generation

- **Streamlit UI**
  - Web interface for research tasks
  - Real-time progress tracking

### Technical Features

- Async/await throughout
- Pydantic models for type safety
- Dependency injection pattern
- Robust JSON parsing for noisy LLM outputs
- Colored console + file logging
- Token counting for cost estimation

## [0.1.0] - Initial Development

### Added

- Project scaffolding
- Basic agent architecture
- Initial documentation
- Core configuration system

---

## Release Notes Format

Each release includes:

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features to be removed
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

## Contributing

When contributing, please update this changelog under the `[Unreleased]` section following the format above.
