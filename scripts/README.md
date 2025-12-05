# Scripts Directory

Helper scripts organized by purpose.

## Subdirectories

### `/debug/` - Debug Scripts
Scripts to debug import issues, module problems, and dependencies:
- `debug_base.py` - Debug base agent imports
- `debug_factory_imports.py` - Debug factory imports
- `debug_import.py` - General import debugging
- `debug_langgraph.py` - Debug LangGraph setup
- And more...

**Usage:**
```bash
python scripts/debug/debug_import.py
```

---

### `/test/` - Test Scripts
Scripts to test LangSmith, LangFuse, Phoenix integrations:
- `test_langsmith_clean.py` - Test LangSmith (Windows-compatible)
- `test_langsmith_simple.py` - Simple LangSmith test
- `test_langfuse_integration.py` - Test LangFuse integration
- `test_phoenix_install.py` - Verify Phoenix installation

**Usage:**
```bash
python scripts/test/test_langsmith_clean.py
```

---

### `/setup/` - Setup & Demo Scripts
Scripts to set up services and run demonstrations:
- `run_professional_research.py` - Research with metrics & tracing
- `run_test_research.py` - Simple test research
- `setup_phoenix_local.py` - Setup Phoenix tracing
- `start_phoenix.py` - Start Phoenix server
- `demo_visual_workflow.py` - Workflow visualization demo
- `langfuse_setup_guide.py` - LangFuse setup helper
- `docker-compose-langfuse.yml` - LangFuse Docker config

**Usage:**
```bash
# Run professional research
python scripts/setup/run_professional_research.py --name "Tesla"

# Start Phoenix tracing
python scripts/setup/start_phoenix.py
```

---

### `/tools/` - Utility Tools
General utility scripts:
- `fix_imports.py` - Fix import issues automatically
- `verify_graph.py` - Verify graph configuration
- `verify_imports.py` - Verify all imports work

**Usage:**
```bash
python scripts/tools/fix_imports.py
```

---

## Quick Reference

```bash
# From root directory

# Debug imports
python scripts/debug/debug_import.py

# Test LangSmith
python scripts/test/test_langsmith_clean.py

# Run research with tracing
python scripts/setup/run_professional_research.py --name "Apple"

# Fix imports
python scripts/tools/fix_imports.py
```

---

## Adding New Scripts

When adding new scripts:
1. **Debug scripts** → `/scripts/debug/`
2. **Test scripts** → `/scripts/test/`
3. **Setup/demo scripts** → `/scripts/setup/`
4. **Utility tools** → `/scripts/tools/`

**Never add scripts to root directory!**

---

See [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) for complete project organization.
