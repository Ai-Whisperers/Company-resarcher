# PERF-012: Filter Irrelevant Foreign Domain Results

## Problem

Search results return completely irrelevant websites that waste browser fetch time:
- Chinese sites (zhihu.com, baidu.com) for Paraguay telecom queries
- German solar forum (photovoltaikforum.com) matching "Tigo" (solar company vs telecom)
- Generic international sites with no Paraguay content

## Evidence from Logs

```
22:40:42 - Overall fetch timeout (60s) for https://www.zhihu.com/question/508424194
22:40:42 - Overall fetch timeout (60s) for https://www.zhihu.com/question/537871938
22:40:46 - Overall fetch timeout (60s) for https://www.zhihu.com/question/508424194
22:40:53 - Overall fetch timeout (60s) for https://www.zhihu.com/question/583363454

# German solar forum (wrong "Tigo"):
22:35:08 - Overall fetch timeout (60s) for https://www.photovoltaikforum.com/thread/218791-leistungsoptimierer-huawei-vs-tigo/
```

## Impact

- 60 seconds wasted per irrelevant URL
- For Vox Paraguay: 20+ Chinese URLs observed = 20+ minutes wasted
- For Tigo Paraguay: German solar forum URLs polluting results

## Proposed Solution

### 1. Domain Blocklist

Create a blocklist of domains known to be irrelevant for business research:

```python
IRRELEVANT_DOMAINS = {
    # Chinese sites (not relevant for Latin America research)
    "zhihu.com",
    "baidu.com",
    "tieba.baidu.com",
    "weibo.com",
    "bilibili.com",

    # Solar/energy forums (false match for "Tigo")
    "photovoltaikforum.com",
    "solarweb.net",

    # Generic non-business sites
    "pinterest.com",
    "tumblr.com",
    "quora.com",  # Often low-quality
}
```

### 2. Country/Language Relevance Filter

For company research, filter URLs based on expected regions:

```python
def is_relevant_for_country(url: str, target_country: str) -> bool:
    """Check if URL is likely relevant for target country research."""
    domain = extract_domain(url)

    # Known country TLDs
    if target_country == "Paraguay":
        # Accept: .py, .com, .org, regional sites
        # Reject: .cn, .de (unless specific business sites)
        if domain.endswith(('.cn', '.jp', '.kr', '.ru')):
            return False

    return True
```

### 3. Integration Points

- `src/tools/search/base.py`: Filter results before returning
- `src/core/url_validator.py`: Add domain relevance check
- `src/pipeline/comprehensive_research.py`: Pass country context

## Files to Modify

- `src/tools/search/base.py`
- `src/core/url_validator.py`
- New: `src/core/domain_filter.py`

## Configuration

Add to `config.yaml`:

```yaml
search:
  blocked_domains:
    - zhihu.com
    - baidu.com
    - photovoltaikforum.com

  # Filter by country relevance
  country_domain_filter: true
```

## Acceptance Criteria

- [ ] Chinese domains filtered for Latin America research
- [ ] German solar forums filtered for telecom research
- [ ] Logging shows "Filtered irrelevant domain: zhihu.com"
- [ ] Configurable blocklist in config.yaml
- [ ] BUG-049 filter already exists - extend it

## Priority

**HIGH** - Prevents wasted fetches on completely wrong content.

## Estimate

2 hours implementation + testing
