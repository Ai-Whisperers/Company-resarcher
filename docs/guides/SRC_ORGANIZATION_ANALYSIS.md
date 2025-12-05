# src/ Directory Organization Analysis

**Generated:** 2025-12-05
**Total Python Files:** ~345 files across 97 directories

---

## Current Structure Issues

### 1. **core/ is Bloated (102 files, 19 subdirectories)**

The `core/` module has become a catch-all for everything:

```
core/
├── agents/           # Conflicts with top-level agents/
├── concurrency/
├── config/
├── content/          # Overlaps with services/content/
├── di/
├── exceptions/
├── filesystem/
├── indexing/
├── logging/
├── managers/
├── output/
├── prompts/
├── resilience/
├── security/         # Overlaps with services/security/
├── session/
├── streaming/
├── tracking/
├── types/
├── url_utils/        # Conflicts with top-level utils/
├── validation/
└── workflow/
```

**Problem:** Too many responsibilities, unclear boundaries

---

### 2. **Confusing Naming Conflicts**

| Top Level | Core Subdirectory | Issue |
|-----------|-------------------|-------|
| `agents/` (11 files) | `core/agents/` (2 files) | Different purposes but confusing |
| `utils/` (3 files) | `core/url_utils/` | Duplication - utils has url_utils.py |
| N/A | `core/content/` | Overlaps with `services/content/` |
| N/A | `core/security/` | Overlaps with `services/security/` |
| `prompts/` (txt files) | `core/prompts/` (Python) | Same concept, different formats |

---

### 3. **services/ vs infrastructure/ Overlap**

Both have AI, security, and data-related modules:

**services/**
- ai/
- content/
- data/
- quality/
- research/
- security/

**infrastructure/**
- ai/
- browser/
- cache/
- database/
- network/
- sources/

**Unclear Distinction:** When to use services vs infrastructure?

---

### 4. **Small, Scattered Directories**

| Directory | Files | Issue |
|-----------|-------|-------|
| `ui/` | 1 file (streamlit_app.py) | Should be in apps/ or separate |
| `utils/` | 3 files | Merge into core/ or specific modules |
| `middleware/` | 3 files | Could be in infrastructure/ |
| `plugins/` | 3 files | Could be in infrastructure/ |
| `evaluation/` | 2 files | Could be in services/quality/ |
| `data/` | 4 files | Generic name, unclear purpose |
| `dashboard/` | EMPTY | Delete |

---

### 5. **Prompts Fragmentation**

- `prompts/` - 9 .txt files (brand, competitive, etc.)
- `core/prompts/` - Python files for prompt management
- `templates/` - 54 .md files organized by section

**Problem:** Related content split across 3 locations

---

## Recommended Reorganization

### Option A: Clean Layered Architecture (Recommended)

```
src/
├── api/                    # FastAPI endpoints (keep as-is)
│   └── ...
│
├── cli/                    # Command-line interface (keep as-is)
│   └── ...
│
├── domain/                 # Business logic & models (keep as-is)
│   ├── models/
│   ├── quant/
│   ├── research/
│   └── strategies/
│
├── application/            # NEW: Application services (use cases)
│   ├── research/          # ← Move services/research/
│   ├── quality/           # ← Move services/quality/
│   └── pipelines/         # ← Move pipeline/
│
├── infrastructure/         # External concerns (CONSOLIDATE)
│   ├── ai/               # ← Keep infrastructure/ai/ + services/ai/
│   ├── browser/          # ← Keep
│   ├── cache/            # ← Keep
│   ├── database/         # ← Keep
│   ├── network/          # ← Keep
│   ├── sources/          # ← Keep
│   ├── content/          # ← Merge services/content/ + core/content/
│   ├── security/         # ← Merge services/security/ + core/security/
│   ├── middleware/       # ← Move middleware/
│   └── plugins/          # ← Move plugins/
│
├── agents/                 # Research agents (keep as-is)
│   └── ...
│
├── tools/                  # External tool integrations (keep as-is)
│   └── ...
│
├── core/                   # SLIM DOWN - Only true core utilities
│   ├── config/           # Configuration management
│   ├── di/               # Dependency injection
│   ├── exceptions/       # Custom exceptions
│   ├── logging/          # Logging utilities
│   ├── types/            # Type definitions
│   └── validation/       # Validation utilities
│
├── lib/                    # NEW: Shared libraries (non-core)
│   ├── concurrency/      # ← Move from core/
│   ├── filesystem/       # ← Move from core/
│   ├── indexing/         # ← Move from core/
│   ├── managers/         # ← Move from core/
│   ├── output/           # ← Move from core/
│   ├── resilience/       # ← Move from core/
│   ├── session/          # ← Move from core/
│   ├── streaming/        # ← Move from core/
│   ├── tracking/         # ← Move from core/
│   ├── url_utils/        # ← Merge core/url_utils/ + utils/url_utils
│   ├── workflow/         # ← Move from core/
│   └── agents/           # ← Move core/agents/ (computer interface)
│
├── prompts/                # CONSOLIDATE: All prompt-related
│   ├── management/       # ← Move core/prompts/ (Python)
│   ├── templates/        # ← Move templates/ (.md files)
│   └── examples/         # ← Move prompts/ (.txt files)
│
├── apps/                   # NEW: Separate applications
│   ├── web/              # ← Move ui/streamlit_app.py
│   └── mcp/              # ← Move mcp/
│
└── shared/                 # NEW: Truly shared utilities
    ├── data/             # ← Move data/ (if needed)
    └── utils/            # ← Merge utils/ misc files
```

**Benefits:**
- Clear separation of concerns
- Easy to find modules by responsibility
- Follows Clean/Hexagonal Architecture
- core/ is actually core (not a dumping ground)

---

### Option B: Feature-Based Organization (Alternative)

```
src/
├── features/               # NEW: Organize by feature
│   ├── research/
│   │   ├── agents/
│   │   ├── pipeline/
│   │   ├── services/
│   │   └── tools/
│   ├── analysis/
│   │   ├── quant/
│   │   ├── evaluation/
│   │   └── ...
│   └── output/
│       ├── templates/
│       ├── rendering/
│       └── ...
│
├── infrastructure/
│   └── ... (as in Option A)
│
├── core/
│   └── ... (slim, as in Option A)
│
├── api/
│   └── ...
│
└── cli/
    └── ...
```

**Benefits:**
- Related code grouped together
- Easier to find all code for a feature
- Good for microservices migration

**Drawbacks:**
- Can lead to duplication across features
- Less clear layering

---

## Migration Priority

### Phase 1: Quick Wins (Low Risk)
1. ✅ Delete `dashboard/` (empty)
2. ✅ Merge `utils/` into `lib/url_utils/`
3. ✅ Move `ui/streamlit_app.py` to `apps/web/`
4. ✅ Move `middleware/` to `infrastructure/middleware/`
5. ✅ Move `plugins/` to `infrastructure/plugins/`
6. ✅ Move `evaluation/` to `application/quality/evaluation/`

### Phase 2: Core Cleanup (Medium Risk)
1. Create `lib/` directory
2. Move non-core modules from `core/` to `lib/`:
   - concurrency → lib/concurrency
   - filesystem → lib/filesystem
   - indexing → lib/indexing
   - managers → lib/managers
   - output → lib/output
   - resilience → lib/resilience
   - session → lib/session
   - streaming → lib/streaming
   - tracking → lib/tracking
   - url_utils → lib/url_utils (merge with utils/)
   - workflow → lib/workflow
   - agents → lib/agent_interface

### Phase 3: Service Layer (Higher Risk)
1. Create `application/` directory
2. Move `services/` → `application/`
3. Move `pipeline/` → `application/pipelines/`
4. Merge service overlaps:
   - services/content + core/content → infrastructure/content
   - services/security + core/security → infrastructure/security
   - services/ai + infrastructure/ai → infrastructure/ai (consolidate)

### Phase 4: Prompts Consolidation (Low Risk)
1. Create unified `prompts/` structure
2. Move `templates/` → `prompts/templates/`
3. Move `prompts/*.txt` → `prompts/examples/`
4. Move `core/prompts/` → `prompts/management/`

---

## File Count Impact

**Before (Current):**
- core/: 102 files (19 subdirs)
- Total directories: 97

**After (Option A):**
- core/: ~20 files (6 subdirs) - **80% reduction**
- lib/: ~60 files (11 subdirs)
- infrastructure/: ~90 files
- application/: ~40 files
- Total directories: ~70 (**28% reduction**)

---

## Decision Matrix

| Aspect | Option A (Layered) | Option B (Feature-Based) | Keep Current |
|--------|-------------------|-------------------------|--------------|
| **Clarity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Migration Effort** | Medium | High | None |
| **Maintenance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Scalability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Learning Curve** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Breaking Changes** | Medium | High | None |

---

## Recommendation

**Choose Option A: Clean Layered Architecture**

**Why:**
1. Industry standard approach (Domain-Driven Design)
2. Clear boundaries between layers
3. Easier to test (dependency flow is clear)
4. Moderate migration effort
5. Scalable for future growth

**Start with Phase 1 (Quick Wins)** - low risk, immediate benefit

**Migration can be gradual** - both old and new structures can coexist during transition

---

## Implementation Steps

### Step 1: Create New Structure (No Breaking Changes)
```bash
mkdir -p src/lib/{concurrency,filesystem,indexing,managers,output,resilience,session,streaming,tracking,url_utils,workflow,agent_interface}
mkdir -p src/application/{research,quality,pipelines}
mkdir -p src/apps/{web,mcp}
mkdir -p src/prompts/{management,templates,examples}
```

### Step 2: Copy Files (Preserve Originals)
- Copy files to new locations
- Update imports in new files
- Add __init__.py files
- Test imports work

### Step 3: Update Imports Throughout Codebase
- Use search/replace for import paths
- Test after each batch of changes
- Run full test suite

### Step 4: Remove Old Files
- After all imports updated
- Delete original files
- Remove empty directories

---

## Risk Mitigation

1. **Version Control:** Create feature branch for reorganization
2. **Tests:** Run full test suite after each phase
3. **Gradual Migration:** One phase at a time
4. **Backwards Compatibility:** Keep __init__.py files that re-export from new locations temporarily

---

## Next Steps

1. Review this proposal
2. Decide: Option A, Option B, or hybrid
3. Approve Phase 1 (Quick Wins)
4. Create reorganization branch
5. Start migration

