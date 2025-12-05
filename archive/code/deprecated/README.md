# Deprecated Code Archive

**Archived:** 2025-12-05
**Reason:** Legacy code cleanup - migrated to new architecture

---

## What's in this Archive

This directory contains deprecated code that has been removed from the active codebase but preserved for reference.

### 1. src_graph/ - LangGraph-based Orchestration System

**Lines of Code:** ~2,500 lines
**Status:** DEPRECATED - Replaced by PipelineOrchestrator

**What was it?**
- Legacy LangGraph-based research workflow orchestration
- Complex state management system (ResearchState)
- Graph-based execution with nodes and edges
- Multi-phase research workflow (gather → analyze → review → write)

**Why deprecated?**
- Over-engineered for current requirements
- Pipeline architecture is simpler and more maintainable
- Removed LangGraph dependency complexity
- Better separation of concerns with new pipeline stages

**Migration Path:**
```python
# OLD (Deprecated):
from src.graph import ResearchGraph, ResearchState
graph = ResearchGraph()
result = await graph.execute(state)

# NEW (Current):
from src.pipeline.orchestrator import PipelineOrchestrator
orchestrator = PipelineOrchestrator()
result = await orchestrator.conduct_research("Company Name")
```

**What's still active:**
- LangGraph checkpointing (src/graph/checkpointer.py) - NEW feature for resumable workflows

**Contents:**
- state.py (1,400+ lines) - Complex state management
- graph_builder.py (800+ lines) - Graph construction logic
- research_graph.py - LangGraph execution
- components/ - Graph component modules
- framework/ - Graph framework abstractions
- nodes/ - Individual workflow nodes

---

### 2. agents/ - Deprecated Agent Components

**Lines of Code:** ~1,200 lines
**Status:** DEPRECATED - Replaced by PipelineOrchestrator

**orchestrator.py - Legacy Research Orchestrator**

**What was it?**
- Original multi-agent orchestration system
- Parallel specialist agent execution
- Insight generation and report compilation
- Global singleton pattern

**Why deprecated?**
- Replaced by cleaner pipeline architecture
- Better error handling in new system
- Removed global state and singletons
- Improved testability and maintainability

**test_orchestrator.py** - Unit tests for deprecated orchestrator
**test_research_workflow.py** - E2E tests for deprecated workflow

---

## Files Not in Archive (Still Active)

The following deprecated patterns remain in the codebase for backward compatibility:

### Legacy Methods (Monitor for Removal)

**to_legacy_dict() Methods** (~300 lines across files)
- `FinancialData.to_legacy_dict()` - [src/domain/models/base.py:268](../../src/domain/models/base.py#L268)
- `MarketData.to_legacy_dict()` - [src/domain/models/base.py:341](../../src/domain/models/base.py#L341)
- `CompetitorData.to_legacy_dict()` - [src/domain/models/base.py:440](../../src/domain/models/base.py#L440)
- `BrandData.to_legacy_dict()` - [src/domain/models/base.py:499](../../src/domain/models/base.py#L499)
- `SalesData.to_legacy_dict()` - [src/domain/models/base.py:554](../../src/domain/models/base.py#L554)
- `ResearchContext.to_legacy_dicts()` - [src/domain/models/base.py:861](../../src/domain/models/base.py#L861)

**Used By:**
- [src/agents/insight_generator.py](../../src/agents/insight_generator.py)
- Can be removed once all consumers migrate to typed Pydantic models

---

## Cleanup Impact

**Before Cleanup:**
- src/graph: 2,500+ lines
- orchestrator.py: 1,200+ lines
- Tests: 400+ lines
- **Total: ~4,100 lines**

**After Cleanup:**
- src/graph: 400 lines (checkpointer only)
- **Reduction: ~3,700 lines (90% reduction)**

**Benefits:**
- Simpler architecture for new developers
- Faster imports (no deprecation warnings)
- Less maintenance burden
- Clearer separation between old and new patterns

---

## How to Use Archived Code

**DO NOT** directly import archived code in new features.

**Reference Only:**
- Understanding legacy patterns
- Extracting useful algorithms
- Migration assistance
- Historical context

**If you need something from here:**
1. Review the new implementation in src/pipeline/
2. If functionality is missing, discuss adding it to the new architecture
3. Avoid copying deprecated patterns

---

## Next Deprecation Candidates

The following items are marked for future removal:

1. **AIClientManager** (src/infrastructure/ai/legacy_client.py)
   - Status: Deprecated, fallback for non-LangChain models
   - Replacement: LangChain Runnable models
   - Timeline: Remove in v2.0

2. **to_legacy_dict() methods** (various files)
   - Status: Backward compatibility for dict-based consumers
   - Replacement: Native Pydantic model usage
   - Timeline: Monitor usage, remove when consumers migrated

3. **Static output mode** (src/core/output/dynamic_output_manager.py)
   - Status: Legacy constant
   - Replacement: Dynamic output (adaptive based on company type)
   - Timeline: Can remove immediately if not used

4. **Deprecated search operators** (src/tools/search/tool.py)
   - "link:" operator marked as unreliable
   - Timeline: Can remove immediately

---

## Archive Maintenance

**Do NOT:**
- Modify archived code (it's frozen)
- Add new features to archived modules
- Fix bugs in archived code

**DO:**
- Keep archive for reference
- Update this README if more items archived
- Delete entire archive directory after v2.0 release

---

## Questions?

See the main [LEGACY_CODE_AUDIT.md](../../../LEGACY_CODE_AUDIT.md) for complete deprecation analysis.

For new development, always refer to:
- src/pipeline/ - Current orchestration
- src/agents/ (without orchestrator.py) - Current agents
- src/domain/models/ - Typed data models
