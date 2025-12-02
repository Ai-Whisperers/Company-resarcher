# DO-017: Inconsistent Documentation Style

**Priority**: Medium
**Category**: Documentation
**Status**: Open
**Effort**: Medium (ongoing)

## Problem

Documentation across the project uses inconsistent formatting, structure, and terminology.

## Impact

- Difficult to navigate documentation
- Inconsistent user experience
- Harder to maintain
- Professional appearance diminished

## Inconsistencies Found

### 1. File Naming
- `CONTRIBUTING.md` (uppercase)
- `research_schema_design.md` (lowercase with underscores)
- `01-Agents.md` (numbered)
- `QUICK_START_TOOLS.md` (mixed)

### 2. Header Styles
- Some use emoji headers (`## 🚀 Getting Started`)
- Some use plain headers (`## Getting Started`)
- Inconsistent heading levels

### 3. Code Block Languages
- Some specify language (` ```python`)
- Some don't (` ``` `)

### 4. Link Formats
- Relative links (`./docs/...`)
- Absolute links (`docs/...`)
- Some broken links

### 5. Terminology
- "LLM" vs "AI Model" vs "Model"
- "Agent" vs "Specialist"
- "Research" vs "Analysis"

## Solution

Create `docs/STYLE_GUIDE.md` defining:
1. File naming conventions
2. Header structure
3. Code block formatting
4. Link conventions
5. Terminology glossary
6. Template for new documents

## Style Guide Excerpt

```markdown
## Documentation Style Guide

### File Naming
- Guide files: UPPERCASE with underscores (e.g., `QUICK_START.md`)
- Technical docs: lowercase with hyphens (e.g., `api-reference.md`)
- Module docs: numbered prefix (e.g., `01-agents.md`)

### Headers
- Use plain text headers (no emojis in technical docs)
- Start with H1 (`#`) for title
- Use H2 (`##`) for main sections
- Don't skip heading levels

### Code Blocks
- Always specify language
- Include file path in comment if relevant
```

## Acceptance Criteria

- [ ] Style guide created
- [ ] Existing docs audited for inconsistencies
- [ ] High-visibility docs updated to match style
- [ ] Templates provided for common doc types
