# DO-023: No Documentation Search

## Status: RESOLVED - MkDocs Material Implemented

## Priority: Low

---

## Current State

| Feature | Status |
|---------|--------|
| Documentation in `/docs` | ✅ Exists |
| Organized structure | ✅ Implemented |
| GitHub basic search | ⚠️ Limited |
| Dedicated search | ❌ Not implemented |

**Location**: `docs/` directory - Markdown files only

---

## The Problem

Users cannot effectively search across documentation:

- Must manually browse directory structure
- GitHub search is keyword-only, no context
- No full-text search across all docs
- Hard to discover relevant information

---

## Do You Need Documentation Search?

### You DON'T need it if

- Small documentation set (< 20 pages)
- Team knows the docs well
- Internal tool with few users
- GitHub browsing is sufficient

### You DO need it if

- Growing documentation (50+ pages)
- External users / contributors
- Complex topics requiring cross-referencing
- Want professional documentation experience

---

## Option Analysis

### Option 1: GitHub Wiki (Minimal Effort)

**How it works**: Move docs to GitHub Wiki, get built-in search.

| Aspect | Assessment |
|--------|------------|
| **Effort** | Minimal - 1-2 hours |
| **Search Quality** | Basic keyword matching |
| **Customization** | Very limited |
| **Maintenance** | Zero |

**Pros**:

- Already have GitHub
- No deployment needed
- Built-in search
- Easy editing

**Cons**:

- Limited formatting
- No custom themes
- Separate from repo (harder to version)
- Search quality is basic

**Best for**: Quick solution, minimal docs

---

### Option 2: MkDocs + Material Theme (Recommended)

**How it works**: Static site generator, deploy to GitHub Pages.

| Aspect | Assessment |
|--------|------------|
| **Effort** | Low - 2-4 hours setup |
| **Search Quality** | Excellent (client-side) |
| **Customization** | Extensive |
| **Maintenance** | Minimal |

**Pros**:

- Python-based (fits your stack)
- Material theme is beautiful
- Built-in search with highlighting
- Markdown-native (no migration)
- Free hosting on GitHub Pages
- Excellent plugin ecosystem

**Cons**:

- Requires initial setup
- Another tool to maintain
- Build step required

**Best for**: Python projects, professional documentation

**Setup**:

```yaml
# mkdocs.yml
site_name: Company Researcher
site_url: https://yourorg.github.io/company-researcher/
repo_url: https://github.com/yourorg/company-researcher

theme:
  name: material
  features:
    - search.suggest
    - search.highlight
    - search.share
    - navigation.instant
    - navigation.sections
    - navigation.expand
    - content.code.copy
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search:
      lang: en
  - tags

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - admonition
  - toc:
      permalink: true

nav:
  - Home: index.md
  - Getting Started:
    - Setup: guides/SETUP.md
    - Configuration: guides/CONFIGURATION.md
  - Guides:
    - Security: guides/SECURITY.md
    - Troubleshooting: guides/TROUBLESHOOTING.md
  - API Reference: api/API_REFERENCE.md
  - Architecture: architecture/patterns/README.md
```

**GitHub Actions deployment**:

```yaml
# .github/workflows/docs.yml
name: Deploy Docs
on:
  push:
    branches: [main]
    paths: ['docs/**', 'mkdocs.yml']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install mkdocs-material
      - run: mkdocs gh-deploy --force
```

---

### Option 3: Docusaurus (React-Based)

**How it works**: React-based docs framework by Meta.

| Aspect | Assessment |
|--------|------------|
| **Effort** | Medium - 4-8 hours |
| **Search Quality** | Excellent (Algolia optional) |
| **Customization** | Maximum (React) |
| **Maintenance** | Medium |

**Pros**:

- Powerful versioning
- MDX support (React in Markdown)
- i18n built-in
- Large community

**Cons**:

- React knowledge helpful
- Heavier than MkDocs
- More complex setup
- Node.js dependency

**Best for**: React projects, versioned docs, i18n needs

---

### Option 4: VitePress (Vue-Based)

**How it works**: Vue-based docs framework, fast builds.

| Aspect | Assessment |
|--------|------------|
| **Effort** | Medium - 4-6 hours |
| **Search Quality** | Excellent (local) |
| **Customization** | High (Vue) |
| **Maintenance** | Low |

**Pros**:

- Extremely fast builds
- Vue 3 integration
- Lightweight
- Great DX

**Cons**:

- Vue knowledge helpful
- Smaller community than Docusaurus
- Less plugins than MkDocs

**Best for**: Vue projects, speed-focused

---

### Option 5: Algolia DocSearch (Add-On)

**How it works**: External search service, free for open source.

| Aspect | Assessment |
|--------|------------|
| **Effort** | Low - 2 hours (with existing site) |
| **Search Quality** | Best-in-class |
| **Customization** | Appearance only |
| **Maintenance** | Zero |

**Pros**:

- Industry-leading search quality
- Typo tolerance
- Instant results
- Free for open source

**Cons**:

- Requires public documentation site
- External dependency
- Application process for free tier

**Best for**: Open source projects with existing docs site

---

## Decision Matrix

| Criteria | GitHub Wiki | MkDocs | Docusaurus | VitePress | Algolia |
|----------|-------------|--------|------------|-----------|---------|
| Setup Time | 1-2 hours | 2-4 hours | 4-8 hours | 4-6 hours | 2 hours* |
| Search Quality | Basic | Excellent | Excellent | Excellent | Best |
| Python Ecosystem | ❌ | ✅ | ❌ | ❌ | N/A |
| React Knowledge | ❌ | ❌ | ⚠️ | ❌ | ❌ |
| Maintenance | Zero | Minimal | Medium | Low | Zero |
| Free Hosting | ✅ | ✅ | ✅ | ✅ | ✅* |
| Fits Current Use Case | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |

*Algolia requires existing docs site

---

## Recommendation

### For This Project: **MkDocs + Material Theme**

**Rationale**:

1. Python project = Python tooling makes sense
2. Material theme is polished and professional
3. Built-in search is excellent (no external deps)
4. Minimal setup, your Markdown works as-is
5. Free GitHub Pages hosting
6. Easy CI/CD integration

### Quick Start

```bash
# Install
pip install mkdocs-material

# Create config (mkdocs.yml at repo root)
# Move docs/index.md or create one

# Local preview
mkdocs serve

# Deploy to GitHub Pages
mkdocs gh-deploy
```

---

## Implementation Checklist

If you choose **MkDocs + Material**:

- [ ] Install: `pip install mkdocs-material`
- [ ] Create `mkdocs.yml` at repo root
- [ ] Create `docs/index.md` as homepage
- [ ] Configure navigation in `mkdocs.yml`
- [ ] Test locally: `mkdocs serve`
- [ ] Add GitHub Action for auto-deploy
- [ ] Enable GitHub Pages in repo settings
- [ ] Update README with docs link

**Estimated time**: 2-4 hours

---

## Example File Structure

```text
company-researcher/
├── mkdocs.yml              # MkDocs configuration
├── docs/
│   ├── index.md            # Homepage
│   ├── guides/
│   │   ├── SETUP.md
│   │   ├── CONFIGURATION.md
│   │   └── TROUBLESHOOTING.md
│   ├── api/
│   │   └── API_REFERENCE.md
│   └── architecture/
│       └── patterns/
│           └── README.md
└── .github/
    └── workflows/
        └── docs.yml        # Auto-deploy action
```

---

## References

- [MkDocs Material - Getting Started](https://squidfunk.github.io/mkdocs-material/getting-started/)
- [MkDocs Material - Search](https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/)
- [Docusaurus](https://docusaurus.io/)
- [VitePress](https://vitepress.dev/)
- [Algolia DocSearch](https://docsearch.algolia.com/)

---

## Related Issues

None - standalone documentation improvement.
