# Visual Reorganization Guide

## Current Problems (Highlighted)

```
src/
├── agents/ (11 files)           ✅ GOOD - Clear purpose
├── api/ (6 files)               ✅ GOOD - Clear purpose
├── cli/ (16 files)              ✅ GOOD - Clear purpose
│
├── core/ (102 files!)           ❌ BLOATED - Too many responsibilities
│   ├── agents/                  ⚠️  CONFLICTS with top-level agents/
│   ├── content/                 ⚠️  OVERLAPS with services/content/
│   ├── security/                ⚠️  OVERLAPS with services/security/
│   ├── url_utils/               ⚠️  CONFLICTS with utils/url_utils.py
│   ├── prompts/                 ⚠️  SPLIT from prompts/ and templates/
│   └── [16 other subdirs...]    ❌ TOO MANY - Core should be minimal
│
├── services/ (37 files)         ⚠️  OVERLAPS with infrastructure/
│   ├── ai/                      ⚠️  Also in infrastructure/ai/
│   ├── content/                 ⚠️  Also in core/content/
│   └── security/                ⚠️  Also in core/security/
│
├── infrastructure/ (64 files)   ⚠️  OVERLAPS with services/
│   └── ai/                      ⚠️  Also in services/ai/
│
├── prompts/ (9 .txt files)      ⚠️  FRAGMENTED across 3 places
├── templates/ (54 .md files)    ⚠️  Related to prompts/
│
├── utils/ (3 files)             ❌ TOO SMALL - Should merge
├── ui/ (1 file!)                ❌ TOO SMALL - Just streamlit_app.py
├── middleware/ (3 files)        ❌ TOO SMALL - Belongs in infrastructure/
├── plugins/ (3 files)           ❌ TOO SMALL - Belongs in infrastructure/
├── evaluation/ (2 files)        ❌ TOO SMALL - Belongs in services/quality/
├── data/ (4 files)              ⚠️  UNCLEAR - Generic name
└── dashboard/ (EMPTY!)          ❌ DELETE - Locked but empty

Total: 97 directories, ~345 Python files
```

---

## Proposed Structure (Option A - Layered)

```
src/
├── 📱 INTERFACES (Entry Points)
│   ├── api/                     ← Keep as-is
│   ├── cli/                     ← Keep as-is
│   └── apps/                    ← NEW: Separate applications
│       ├── web/                 ← Move ui/streamlit_app.py
│       └── mcp/                 ← Move mcp/
│
├── 🎯 DOMAIN (Business Logic)
│   ├── domain/                  ← Keep as-is (models, quant, research)
│   └── agents/                  ← Keep as-is (research agents)
│
├── 🚀 APPLICATION (Use Cases)
│   └── application/             ← NEW: Application services
│       ├── research/            ← Move services/research/
│       ├── quality/             ← Move services/quality/ + evaluation/
│       └── pipelines/           ← Move pipeline/
│
├── 🔧 INFRASTRUCTURE (External Concerns)
│   └── infrastructure/          ← CONSOLIDATE
│       ├── ai/                  ← Merge services/ai/ + infrastructure/ai/
│       ├── browser/             ← Keep
│       ├── cache/               ← Keep
│       ├── content/             ← Merge services/content/ + core/content/
│       ├── database/            ← Keep
│       ├── middleware/          ← Move middleware/
│       ├── network/             ← Keep
│       ├── plugins/             ← Move plugins/
│       ├── security/            ← Merge services/security/ + core/security/
│       └── sources/             ← Keep
│
├── 🛠️ TOOLS (External Integrations)
│   └── tools/                   ← Keep as-is (browser, search, data, etc.)
│
├── 💬 PROMPTS (All Prompt Content)
│   └── prompts/                 ← CONSOLIDATE
│       ├── management/          ← Move core/prompts/ (Python code)
│       ├── templates/           ← Move templates/ (.md files)
│       └── examples/            ← Move prompts/ (.txt files)
│
├── 📚 LIBRARIES (Shared Utilities)
│   ├── core/                    ← SLIM DOWN to 6 subdirs (~20 files)
│   │   ├── config/              ← Keep
│   │   ├── di/                  ← Keep
│   │   ├── exceptions/          ← Keep
│   │   ├── logging/             ← Keep
│   │   ├── types/               ← Keep
│   │   └── validation/          ← Keep
│   │
│   └── lib/                     ← NEW: Non-core libraries
│       ├── agent_interface/     ← Move core/agents/
│       ├── concurrency/         ← Move core/concurrency/
│       ├── filesystem/          ← Move core/filesystem/
│       ├── indexing/            ← Move core/indexing/
│       ├── managers/            ← Move core/managers/
│       ├── output/              ← Move core/output/
│       ├── resilience/          ← Move core/resilience/
│       ├── session/             ← Move core/session/
│       ├── streaming/           ← Move core/streaming/
│       ├── tracking/            ← Move core/tracking/
│       ├── url_utils/           ← Merge core/url_utils/ + utils/
│       └── workflow/            ← Move core/workflow/
│
└── graph/                       ← Keep (checkpointer only)
```

---

## Before → After Comparison

### CORE MODULE (The Big Problem)

**BEFORE:** 102 files, 19 subdirectories
```
core/
├── agents/          ← Confusing (conflicts with top-level)
├── concurrency/     ← Not core
├── config/          ✓ Actually core
├── content/         ← Overlaps with services
├── di/              ✓ Actually core
├── exceptions/      ✓ Actually core
├── filesystem/      ← Not core
├── indexing/        ← Not core
├── logging/         ✓ Actually core
├── managers/        ← Not core
├── output/          ← Not core
├── prompts/         ← Split from prompts/templates
├── resilience/      ← Not core
├── security/        ← Overlaps with services
├── session/         ← Not core
├── streaming/       ← Not core
├── tracking/        ← Not core
├── types/           ✓ Actually core
├── url_utils/       ← Conflicts with utils/
├── validation/      ✓ Actually core
└── workflow/        ← Not core
```

**AFTER:** ~20 files, 6 subdirectories (80% reduction)
```
core/
├── config/          ← Configuration management
├── di/              ← Dependency injection
├── exceptions/      ← Custom exceptions
├── logging/         ← Logging setup
├── types/           ← Type definitions
└── validation/      ← Validation utilities
```

All other modules moved to `lib/` (non-core libraries)

---

### SERVICES vs INFRASTRUCTURE (The Overlap Problem)

**BEFORE:** Confusing overlap
```
services/                     infrastructure/
├── ai/ ────────────┐         ├── ai/ ←────────┘ (Which one?!)
├── content/        │         ├── browser/
├── data/           │         ├── cache/
├── quality/        │         ├── database/
├── research/       │         ├── network/
└── security/ ──────┼────────→└── sources/
                    └─ Also core/security/ (3 places!)
```

**AFTER:** Clear separation
```
application/                  infrastructure/
├── research/                 ├── ai/          ← MERGED services + infra
├── quality/                  ├── browser/
└── pipelines/                ├── cache/
                              ├── content/     ← MERGED services + core
                              ├── database/
                              ├── middleware/
                              ├── network/
                              ├── plugins/
                              ├── security/    ← MERGED services + core
                              └── sources/
```

**Rule:**
- `application/` = Business use cases (research workflows)
- `infrastructure/` = External dependencies (APIs, databases, caches)

---

### SMALL SCATTERED MODULES (The Clutter Problem)

**BEFORE:** 7 tiny directories
```
├── utils/ (3 files)          ← Merge into lib/
├── ui/ (1 file!)             ← Move to apps/web/
├── middleware/ (3 files)     ← Move to infrastructure/
├── plugins/ (3 files)        ← Move to infrastructure/
├── evaluation/ (2 files)     ← Move to application/quality/
├── data/ (4 files)           ← Unclear purpose
└── dashboard/ (EMPTY)        ← DELETE
```

**AFTER:** Consolidated
```
├── apps/web/                 ← ui/streamlit_app.py
├── infrastructure/
│   ├── middleware/           ← middleware/
│   └── plugins/              ← plugins/
├── application/quality/
│   └── evaluation/           ← evaluation/
└── lib/
    └── url_utils/            ← utils/ merged here
```

---

## Migration Flow Chart

```
Phase 1: Quick Wins (✅ Low Risk)
    │
    ├─→ Delete dashboard/
    ├─→ Move ui/ → apps/web/
    ├─→ Move middleware/ → infrastructure/
    ├─→ Move plugins/ → infrastructure/
    └─→ Move evaluation/ → application/quality/

    ⏱️ Time: 1-2 hours
    ✅ Breaking Changes: None (just moves)

Phase 2: Core Cleanup (⚠️ Medium Risk)
    │
    ├─→ Create lib/ directory
    ├─→ Move 11 subdirs from core/ → lib/
    ├─→ Merge utils/ → lib/url_utils/
    └─→ Update imports (automated)

    ⏱️ Time: 4-6 hours
    ⚠️ Breaking Changes: Import paths change

Phase 3: Service Layer (⚠️ Higher Risk)
    │
    ├─→ Create application/ directory
    ├─→ Move services/ → application/
    ├─→ Move pipeline/ → application/pipelines/
    ├─→ Consolidate overlaps:
    │   ├─→ services/ai + infra/ai → infra/ai
    │   ├─→ services/content + core/content → infra/content
    │   └─→ services/security + core/security → infra/security
    └─→ Update imports

    ⏱️ Time: 8-12 hours
    ⚠️ Breaking Changes: Major import changes

Phase 4: Prompts (✅ Low Risk)
    │
    ├─→ Create prompts/ structure
    ├─→ Move templates/ → prompts/templates/
    ├─→ Move prompts/*.txt → prompts/examples/
    └─→ Move core/prompts/ → prompts/management/

    ⏱️ Time: 2-3 hours
    ✅ Breaking Changes: Minimal
```

---

## Impact Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Total Directories** | 97 | 70 | -28% ✅ |
| **core/ Files** | 102 | 20 | -80% ✅ |
| **Top-level Dirs** | 24 | 10 | -58% ✅ |
| **Empty Dirs** | 1 | 0 | -100% ✅ |
| **Naming Conflicts** | 4 | 0 | -100% ✅ |
| **Overlapping Modules** | 3 pairs | 0 | -100% ✅ |

---

## Example Import Changes

### Before
```python
from src.core.content.relevance_filter import filter_sources
from src.services.content import ContentService
from src.core.url_utils.domain_filter import is_domain_allowed
from src.utils.url_utils import parse_url
```

### After (Phase 2+3 Complete)
```python
from src.infrastructure.content.relevance_filter import filter_sources
from src.infrastructure.content import ContentService
from src.lib.url_utils.domain_filter import is_domain_allowed
from src.lib.url_utils import parse_url
```

**Clearer meaning:**
- `infrastructure.*` = External dependencies
- `lib.*` = Internal utilities
- `application.*` = Business logic

---

## Risk Mitigation Strategy

1. **Git Branch:** Create `refactor/src-reorganization`
2. **Backwards Compatibility:** Add shim `__init__.py` files that re-export
   ```python
   # src/core/content/__init__.py (temporary)
   from src.infrastructure.content import *
   import warnings
   warnings.warn("Import from src.infrastructure.content instead")
   ```
3. **Test Coverage:** Run tests after each phase
4. **Gradual Rollout:** One phase per week
5. **Rollback Plan:** Keep old structure for 1 release cycle

---

## Recommended Action

**Start with Phase 1 (Quick Wins) - Today**

1. Close IDE (unlock dashboard/)
2. Delete empty `dashboard/` directory
3. Move 5 small modules
4. Run tests
5. Commit

**Total time:** 1-2 hours
**Risk:** Very low
**Benefit:** Immediate cleanup

Then evaluate if Phase 2-4 are worth the effort based on team priorities.
