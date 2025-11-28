# DO-019: No FAQ Section

**Priority**: Low
**Category**: Documentation
**Status**: Open
**Effort**: Small (1-2 hours, ongoing)

## Problem

No FAQ document exists to answer common questions.

## Impact

- Repeated questions in issues/support
- Information scattered across docs
- Quick answers hard to find

## Common Questions to Address

### General
- What is Company Researcher?
- What LLM providers are supported?
- Is this free to use?
- What are the system requirements?

### Setup
- Why am I getting API key errors?
- How do I use local models (Ollama)?
- Can I run this without OpenAI?

### Usage
- How long does a research task take?
- How do I research a private company?
- Can I customize the output format?
- How do I add new data sources?

### Technical
- Why are results sometimes incomplete?
- How does the smart router work?
- What's the difference between agents?
- How is data cached?

### Troubleshooting
- Why am I getting rate limited?
- Why does browser scraping fail?
- How do I debug issues?

## Solution

Create `docs/FAQ.md` with:
1. Categorized questions
2. Concise answers
3. Links to detailed docs
4. Last updated date

## FAQ Template

```markdown
# Frequently Asked Questions

Last updated: YYYY-MM-DD

## General

### What is Company Researcher?
Company Researcher is an autonomous multi-agent system...

### What LLM providers are supported?
We support OpenAI, Anthropic, Google Gemini, Groq, and Ollama...

## Setup

### Why am I getting API key errors?
Ensure your `.env` file contains valid API keys...
[See: Configuration Guide](./guides/CONFIGURATION.md)
```

## Acceptance Criteria

- [ ] FAQ document created
- [ ] Top 15-20 questions answered
- [ ] Links to detailed documentation
- [ ] Process for adding new FAQs
