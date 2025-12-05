# Project Structure

This document describes the organized project structure after cleanup (Dec 2025).

## Root Directory (Clean!)

```
Company-researcher/
├── main.py                      # Entry point - run research
├── requirements.txt             # Python dependencies
├── README.md                    # Project overview
├── CHANGELOG.md                 # Version history
├── docker-compose.yml           # Main Docker configuration
├── Dockerfile                   # Docker image definition
├── .env                         # Environment variables (secrets)
├── .gitignore                   # Git ignore rules
├── pyproject.toml               # Python project configuration
├── mkdocs.yml                   # Documentation site config
├── alembic.ini                  # Database migration config
└── LICENSE                      # Project license
```

**Root contains ONLY essential configuration files.**

---

## Directories

### `/src/` - Source Code
Main application code organized by domain:
```
src/
├── agents/          # AI agents (comprehensive, investment, sales, etc.)
├── cli/             # Command-line interface
├── core/            # Core business logic
├── infrastructure/  # Infrastructure services
├── models/          # Data models (Pydantic)
├── pipeline/        # Research pipeline stages
├── services/        # Business services (AI, data, quality, research)
└── tools/           # Research tools (browser, search, etc.)
```

### `/scripts/` - Utility Scripts
Helper scripts for development and testing:
```
scripts/
├── debug/           # Debug scripts (debug_*.py)
│   ├── debug_base.py
│   ├── debug_factory_imports.py
│   ├── debug_import.py
│   └── ...
│
├── test/            # Test scripts (test_*.py)
│   ├── test_langsmith_clean.py
│   ├── test_langsmith_simple.py
│   ├── test_langfuse_integration.py
│   └── test_phoenix_install.py
│
├── setup/           # Setup & demo scripts
│   ├── run_professional_research.py
│   ├── run_test_research.py
│   ├── setup_phoenix_local.py
│   ├── start_phoenix.py
│   ├── demo_visual_workflow.py
│   ├── langfuse_setup_guide.py
│   └── docker-compose-langfuse.yml
│
└── tools/           # Utility tools
    ├── fix_imports.py
    └── verify_*.py
```

### `/docs/` - Documentation
All documentation and guides:
```
docs/
├── guides/                          # Setup & usage guides
│   ├── QUICK_START.md              # 5-min quick start
│   ├── YOUR_PROFESSIONAL_SETUP.md  # Complete setup guide
│   ├── PROFESSIONAL_LANGCHAIN_SETUP.md
│   ├── LANGSMITH_GUIDE.md
│   ├── LANGFUSE_SETUP.md
│   ├── LOCAL_TRACING_GUIDE.md
│   ├── QUICK_START_TRACING.md
│   └── ...
│
└── planning/                        # Old planning docs (archived)
    └── ... (moved to archive)
```

### `/tests/` - Test Suite
Automated tests:
```
tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── e2e/             # End-to-end tests
```

### `/data/` - Data Storage
Research outputs and cached data:
```
data/
├── output/          # Research reports
├── cache/           # Cached search results
└── database/        # SQLite databases
```

### `/logs/` - Application Logs
Log files:
```
logs/
└── debug.log        # Debug output
```

### `/backups/` - Backups
Configuration backups:
```
backups/
└── .env.env.backup  # Environment file backup
```

---

## Quick Reference

### Run Research
```bash
# From root directory
python main.py --name "Tesla" --industry "Automotive"
```

### Run Tests
```bash
# Test LangSmith integration
python scripts/test/test_langsmith_clean.py

# Run full test suite
pytest tests/
```

### Setup Tools
```bash
# Professional research with metrics
python scripts/setup/run_professional_research.py --name "Apple"

# Start Phoenix tracing
python scripts/setup/start_phoenix.py
```

### Debug Issues
```bash
# Debug import issues
python scripts/debug/debug_import.py

# Verify graph setup
python scripts/tools/verify_graph.py
```

---

## File Organization Rules

### Root Directory
**ONLY** keep:
- Entry points (main.py)
- Core config files (requirements.txt, pyproject.toml)
- Docker files (Dockerfile, docker-compose.yml)
- Documentation (README.md, CHANGELOG.md)
- Environment (.env, .gitignore)

### Scripts Directory
- `/scripts/debug/` - Debug utilities
- `/scripts/test/` - Test scripts
- `/scripts/setup/` - Setup & demo scripts
- `/scripts/tools/` - General utilities

### Documentation
- `/docs/guides/` - User-facing documentation
- `/docs/planning/` - Archived planning docs

### Generated Files
- `/logs/` - Log files
- `/data/` - Research outputs
- `/backups/` - Configuration backups

---

## Migration Guide

If you added files to root, move them to:

| File Type | Destination |
|-----------|-------------|
| `debug_*.py` | `scripts/debug/` |
| `test_*.py` | `scripts/test/` |
| `run_*.py`, `setup_*.py` | `scripts/setup/` |
| `fix_*.py`, `verify_*.py` | `scripts/tools/` |
| `*.md` (guides) | `docs/guides/` |
| `*.log` | `logs/` |
| Docker configs | `scripts/setup/` or root (main only) |

---

## Benefits of This Structure

### Before Cleanup
```
Root: 50+ files (cluttered, hard to navigate)
```

### After Cleanup
```
Root: 12 essential files (clean, professional)
Scripts: Organized by purpose
Docs: Centralized guides
Logs/Backups: Separate folders
```

### Professional Benefits
- ✓ Easy to navigate
- ✓ Clear file purposes
- ✓ Follows Python best practices
- ✓ Ready for team collaboration
- ✓ CI/CD friendly structure

---

## Maintenance

### Keep Root Clean
- Never add temporary files to root
- Use `/scripts/` for new utilities
- Use `/docs/guides/` for new documentation

### Regular Cleanup
- Monthly: Review and archive old logs
- Quarterly: Update documentation
- As needed: Move new scripts to proper folders

---

## Related Documentation

- **Quick Start:** [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md)
- **Professional Setup:** [docs/guides/YOUR_PROFESSIONAL_SETUP.md](docs/guides/YOUR_PROFESSIONAL_SETUP.md)
- **Architecture:** Check `/src/` subdirectories

---

**Last Updated:** December 5, 2025
**Cleanup Date:** December 5, 2025
**Files Organized:** 50+ files moved from root to organized structure
