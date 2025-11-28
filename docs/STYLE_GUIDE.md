# Documentation Style Guide

Guidelines for writing consistent, high-quality documentation for Company Researcher.

## Overview

This style guide ensures documentation is:
- **Consistent** - Same structure and formatting throughout
- **Clear** - Easy to understand for all skill levels
- **Actionable** - Readers know exactly what to do
- **Maintainable** - Easy to update as the project evolves

---

## File Naming Conventions

### Documentation Files

| Type | Convention | Example |
|------|------------|---------|
| Guides | UPPERCASE with underscores | `SETUP.md`, `TROUBLESHOOTING.md` |
| Reference docs | UPPERCASE with underscores | `API_REFERENCE.md`, `DATA_MODELS.md` |
| Module docs | Numbered prefix, title case | `01-Agents.md`, `02-Core.md` |
| Issue files | ID prefix, lowercase with hyphens | `DO-001-no-api-docs.md` |
| Examples | lowercase with hyphens | `api-client.py`, `custom-agent.py` |

### Directories

- Use lowercase with hyphens: `docs/getting-started/`
- Or lowercase single words: `docs/guides/`, `docs/reference/`

---

## Document Structure

### Standard Template

```markdown
# Title

Brief description (1-2 sentences).

## Overview

Longer introduction explaining:
- What this document covers
- Who it's for
- Prerequisites (if any)

---

## Main Section 1

Content...

### Subsection

More specific content...

---

## Main Section 2

Content...

---

## Related Documentation

- [Link to related doc](./path.md)
- [Another related doc](./other.md)
```

### Required Sections

| Document Type | Required Sections |
|---------------|-------------------|
| Guide | Overview, Steps, Troubleshooting, Related |
| Reference | Overview, Details, Examples, Related |
| Tutorial | Prerequisites, Steps (numbered), Verification, Next Steps |
| Issue | Problem, Impact, Solution, Acceptance Criteria |

---

## Formatting Guidelines

### Headers

```markdown
# Document Title (H1) - Only one per document

## Main Section (H2) - Major topics

### Subsection (H3) - Subtopics

#### Minor Section (H4) - Use sparingly
```

**Rules:**
- Don't skip header levels (H1 → H3)
- Use sentence case for headers
- No periods at end of headers
- Add blank line before and after headers

### Code Blocks

Always specify the language:

````markdown
```python
def example():
    return "Hello"
```

```bash
pip install package
```

```json
{"key": "value"}
```
````

**For file paths, add a comment:**

````markdown
```python
# src/agents/custom_agent.py
class CustomAgent:
    pass
```
````

### Inline Code

Use backticks for:
- File names: `config.py`
- Function names: `get_settings()`
- Variable names: `api_key`
- Commands: `pip install`
- Values: `True`, `None`, `"string"`

### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data | Data | Data |
| Data | Data | Data |
```

**Rules:**
- Align columns with pipes
- Use header row
- Keep tables simple (max 5-6 columns)

### Lists

**Unordered lists** for items without sequence:
```markdown
- Item one
- Item two
- Item three
```

**Ordered lists** for steps or sequences:
```markdown
1. First step
2. Second step
3. Third step
```

**Nested lists:**
```markdown
- Parent item
  - Child item
  - Another child
- Another parent
```

### Links

**Internal links (relative):**
```markdown
[Setup Guide](./guides/SETUP.md)
[API Reference](../api/API_REFERENCE.md)
```

**External links:**
```markdown
[FastAPI Documentation](https://fastapi.tiangolo.com/)
```

**Anchor links:**
```markdown
[See Configuration](#configuration)
```

---

## Writing Style

### Tone

- **Professional but friendly** - Not overly formal
- **Direct** - Get to the point quickly
- **Inclusive** - Use "you" instead of "the user"
- **Active voice** - "Run the command" not "The command should be run"

### Examples

**Good:**
> Run `pip install` to install dependencies.

**Avoid:**
> The dependencies should be installed by running the pip install command.

**Good:**
> You can configure multiple LLM providers.

**Avoid:**
> Users are able to configure multiple LLM providers.

### Capitalization

| Term | Correct | Incorrect |
|------|---------|-----------|
| Product name | Company Researcher | company researcher |
| Technologies | Python, FastAPI, LangGraph | python, fastapi, langgraph |
| Concepts | REST API, LLM | Rest Api, Llm |
| Our terms | ResearchState, SmartRouter | Researchstate, Smartrouter |

### Terminology Consistency

Use these terms consistently:

| Preferred | Avoid |
|-----------|-------|
| LLM | AI model, language model |
| agent | specialist, worker |
| research task | research job, research request |
| API key | api key, API Key |
| environment variable | env var, ENV variable |

---

## Code Examples

### Principles

1. **Working code** - Examples should run without modification
2. **Complete** - Include imports and setup
3. **Commented** - Explain non-obvious parts
4. **Realistic** - Use real-world scenarios

### Format

```python
"""
Brief description of what this example demonstrates.
"""
import module

# Setup
client = Client()

# Main operation
result = client.do_something(
    param="value",  # Explain if not obvious
)

# Handle result
print(result)
```

### Bad vs Good Examples

**Bad:**
```python
# Just call the function
result = do_thing()
```

**Good:**
```python
"""
Demonstrate API client usage.
"""
from src.client import ResearchClient

# Initialize client with default settings
client = ResearchClient(base_url="http://localhost:8000")

# Start research (returns task_id)
task_id = client.start_research(
    company_name="Apple",
    url="https://apple.com"
)

print(f"Started task: {task_id}")
```

---

## Common Patterns

### Warning/Note Boxes

**Note:**
```markdown
> **Note:** This requires Python 3.10 or higher.
```

**Warning:**
```markdown
> **Warning:** This will delete all data. Make a backup first.
```

**Tip:**
```markdown
> **Tip:** Use `--local` flag for free research without API keys.
```

### Version/Compatibility Notes

```markdown
> **Requires:** Company Researcher v1.0+
```

```markdown
> **Deprecated:** This feature will be removed in v2.0. Use `new_function()` instead.
```

### Command Line Examples

Show both command and expected output:

```markdown
```bash
python main.py --name "Apple"
```

Output:
```
Starting research for: Apple
[████████████████████] 100%
Research completed! Output saved to: output/Apple/
```
```

---

## Documentation Types

### API Reference

Structure:
1. Endpoint (method + path)
2. Description
3. Parameters (table)
4. Request example
5. Response example
6. Error codes

### Tutorials

Structure:
1. Goal statement
2. Prerequisites
3. Time estimate
4. Numbered steps with explanations
5. Verification step
6. Next steps

### Troubleshooting

Structure:
1. Error message or symptom
2. Possible causes
3. Solution steps
4. Prevention tips

---

## Checklist

Before submitting documentation:

- [ ] File follows naming convention
- [ ] Document has clear title and overview
- [ ] All code blocks have language specified
- [ ] All links work (internal and external)
- [ ] No spelling or grammar errors
- [ ] Consistent with existing docs
- [ ] Reviewed for accuracy
- [ ] Tested any code examples

---

## Tools

### Linting

```bash
# Install markdownlint
npm install -g markdownlint-cli

# Check files
markdownlint docs/**/*.md
```

### Link Checking

```bash
# Install markdown-link-check
npm install -g markdown-link-check

# Check links
find docs -name "*.md" -exec markdown-link-check {} \;
```

### Spell Checking

```bash
# Install cspell
npm install -g cspell

# Check spelling
cspell "docs/**/*.md"
```

---

## Contributing Documentation

1. Follow this style guide
2. Use the appropriate template
3. Test all code examples
4. Verify all links work
5. Submit PR with clear description
6. Respond to review feedback

See [Contributing Guide](./guides/CONTRIBUTING.md) for more details.
