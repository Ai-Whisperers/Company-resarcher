# BUG-039: Dictionary and Translation Sites Polluting Search Results

## Priority: HIGH
## Category: Bug/Search Quality
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Search queries for company "Personal Paraguay" are returning dictionary and translation websites that define the English word "personal" instead of results about the company. This fundamentally breaks research quality.

## Problem Statement

When searching for "Personal Paraguay", search engines interpret "Personal" as the English adjective rather than the company name, returning:
- Chinese-English dictionaries (iciba.com, dictionary.cambridge.org/zhs)
- Encyclopedia entries for the word "personal" (baike.baidu.com)
- Translation sites

These irrelevant results consume the limited search result slots and provide zero useful data.

## Evidence from Output

### Market Report Sources (6 of 12 are dictionaries):
```markdown
- [personal是什么意思_personal的翻译_音标_读音_用法_例句_爱词霸在线词典](https://www.iciba.com/word?w=personal)
- [PERSONAL中文(简体)翻译：剑桥词典](https://dictionary.cambridge.org/zhs/词典/英语-汉语-简体/personal)
- [Personal（英文单词）_百度百科](https://baike.baidu.com/item/Personal/19655771)
- [personal是什么意思_personal的翻译_音标_读音_用法_例句_爱词霸在线词典](https://www.iciba.com/word?w=personal) (DUPLICATE)
- [PERSONAL中文(简体)翻译：剑桥词典](https://dictionary.cambridge.org/zhs/词典/英语-汉语-简体/personal) (DUPLICATE)
- [Personal（英文单词）_百度百科](https://baike.baidu.com/item/Personal/19655771) (DUPLICATE)
```

### Brand Report Sources:
```markdown
- [personal是什么意思_personal的翻译_音标_读音_用法_例句_爱词霸在线词典](https://www.iciba.com/word?w=personal)
- [PERSONAL中文(简体)翻译：剑桥词典](https://dictionary.cambridge.org/zhs/词典/英语-汉语-简体/personal)
- [Personal（英文单词）_百度百科](https://baike.baidu.com/item/Personal/19655771)
```

## Root Cause Analysis

### 1. Query Construction Problem
Current queries are too generic:
```python
queries = [
    f"{company_name} market share industry",  # "Personal Paraguay market share industry"
    f"{company_name} industry trends",
]
```

Without quotes or additional context, search engines match "Personal" as the word.

### 2. No Domain Filtering
DuckDuckGo's `ddgs.text()` doesn't filter out dictionary/translation domains.

### 3. No Content Validation
Fetched pages aren't validated for relevance before being included.

## Affected Domains

| Domain | Type | Should Block |
|--------|------|--------------|
| iciba.com | Chinese-English dictionary | YES |
| dictionary.cambridge.org | Dictionary | YES (when /zhs/ path) |
| baike.baidu.com | Chinese encyclopedia | CONDITIONAL |
| translate.google.com | Translation | YES |
| dict.cc | Dictionary | YES |
| linguee.com | Translation | YES |
| wordreference.com | Dictionary | YES |
| merriam-webster.com | Dictionary | CONDITIONAL |
| thesaurus.com | Thesaurus | YES |

## Proposed Solutions

### Solution 1: Domain Blocklist (Immediate Fix)

```python
# src/tools/search/filters.py

BLOCKED_DOMAINS = [
    # Dictionaries
    "iciba.com",
    "dict.cc",
    "linguee.com",
    "wordreference.com",
    "thesaurus.com",
    "vocabulary.com",
    # Translation sites
    "translate.google.com",
    "deepl.com/translator",
    # Chinese sites (unless researching Chinese companies)
    "baike.baidu.com",
    "dictionary.cambridge.org/zhs",
    "dictionary.cambridge.org/zht",
]

def is_blocked_domain(url: str) -> bool:
    """Check if URL is from a blocked domain."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    for blocked in BLOCKED_DOMAINS:
        if "/" in blocked:
            # Check domain + path
            if blocked in f"{domain}{path}":
                return True
        else:
            # Check domain only
            if domain.endswith(blocked) or domain == blocked:
                return True
    return False
```

### Solution 2: Quote Company Name in Queries

```python
# src/pipeline/stages/research.py

def generate_queries(company_name: str, phase: str) -> List[str]:
    # Use quotes to force exact match
    quoted_name = f'"{company_name}"'

    templates = {
        "market": [
            f'{quoted_name} market share',
            f'{quoted_name} industry analysis',
            f'{quoted_name} market position',
        ],
        # ...
    }
```

### Solution 3: Add Industry Context to Queries

```python
# With company context enrichment (FE-009)
queries = [
    f'"{company_name}" {industry} market share',  # "Personal Paraguay" telecommunications market share
    f'{company_name} {geography} {industry}',     # Personal Paraguay Paraguay mobile operator
]
```

### Solution 4: Content Relevance Validation

```python
# src/services/content_validator.py

class ContentRelevanceValidator:
    """Validate fetched content is relevant to the company."""

    DICTIONARY_PATTERNS = [
        r"pronunciation[:\s]",
        r"definition[:\s]",
        r"noun|verb|adjective|adverb",
        r"synonyms?[:\s]",
        r"antonyms?[:\s]",
        r"etymology[:\s]",
        r"word origin",
        r"translate|translation",
        r"词典|翻译|发音",  # Chinese dictionary terms
    ]

    def is_dictionary_content(self, content: str) -> bool:
        content_lower = content.lower()
        matches = sum(1 for p in self.DICTIONARY_PATTERNS
                     if re.search(p, content_lower))
        return matches >= 3  # If 3+ dictionary patterns, it's a dictionary page

    def is_relevant(self, content: str, company_name: str, context: dict) -> float:
        """Return relevance score 0-1."""
        if self.is_dictionary_content(content):
            return 0.0

        score = 0.0
        content_lower = content.lower()

        # Company name mentioned
        if company_name.lower() in content_lower:
            score += 0.4

        # Industry keywords
        for keyword in context.get("industry_keywords", []):
            if keyword.lower() in content_lower:
                score += 0.1

        # Geographic context
        if context.get("geography", "").lower() in content_lower:
            score += 0.2

        return min(1.0, score)
```

## Implementation Plan

### Phase 1: Domain Blocklist (Quick Win)
1. Create `src/tools/search/filters.py` with blocklist
2. Apply filter in `SearchManager.search()` after getting results
3. Log filtered URLs for monitoring

### Phase 2: Query Improvement
1. Add quotes around company name
2. Add industry context when available
3. Test query variations for better results

### Phase 3: Content Validation
1. Implement `ContentRelevanceValidator`
2. Filter results after fetching content
3. Add relevance scores to sources

## Files to Create/Modify

- New: `src/tools/search/filters.py` - Domain blocklist and filters
- New: `src/services/content_validator.py` - Content relevance validation
- Modify: `src/tools/search/manager.py` - Apply filters to results
- Modify: `src/pipeline/stages/research.py` - Improve query generation

## Acceptance Criteria

- [ ] Dictionary sites are never included in results
- [ ] Translation sites are filtered out
- [ ] At least 80% of results are relevant to the company
- [ ] Duplicate URLs are removed
- [ ] Logs show how many results were filtered

## Testing Plan

1. Search for "Personal Paraguay" - verify no dictionary results
2. Search for "Apple Inc" - verify no apple fruit results
3. Search for "Amazon" - verify company, not rainforest
4. Test with various company names that are common words

## Metrics to Track

- % of results filtered as dictionaries
- % of results that mention company name
- Average relevance score of results
- User satisfaction with research quality

## Related Issues

- BUG-035: Wrong company context in search queries
- FE-009: Company context enrichment
- FE-010: Source quality filtering

## Notes

This is a manifestation of the "word sense disambiguation" problem. The company name "Personal" is ambiguous - it could mean the telecom company or the English adjective. Without context, search engines default to the more common interpretation.
