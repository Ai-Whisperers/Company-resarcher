# PERF-014: Reduce Browser Fetch Timeout for Known-Slow Sites

## Problem

The browser uses a fixed 60-second timeout for all URLs. Many sites consistently timeout or fail, wasting the full 60 seconds every time.

## Evidence from Logs

```
22:39:28 - modular_browser_tool - ERROR - Overall fetch timeout (60s) for https://www.vox.com.py/
22:40:01 - modular_browser_tool - ERROR - Overall fetch timeout (60s) for https://www.vox.com.py/  ← 60s again
22:40:05 - modular_browser_tool - ERROR - Overall fetch timeout (60s) for https://www.vox.com.py/  ← 60s again
22:40:23 - modular_browser_tool - ERROR - Overall fetch timeout (60s) for https://www.vox.com.py/  ← 60s again
```

Same site timing out repeatedly at 60s each.

## Impact

- 60 seconds per timeout (vs 30s for search)
- For Vox Paraguay: 100+ browser timeouts = 100+ minutes of waiting
- Many sites (Instagram, Facebook, LinkedIn) often timeout due to anti-bot measures

## Proposed Solution

### 1. Domain-Based Timeout Tiers

```python
TIMEOUT_TIERS = {
    # Fast timeout for known-problematic sites
    "fast": {
        "timeout": 15,
        "domains": [
            "instagram.com",
            "facebook.com",
            "twitter.com",
            "x.com",
            "linkedin.com",  # Requires auth
            "zhihu.com",
            "baidu.com",
        ]
    },
    # Medium timeout for social/dynamic sites
    "medium": {
        "timeout": 30,
        "domains": [
            "youtube.com",
            "reddit.com",
        ]
    },
    # Default timeout for general sites
    "default": {
        "timeout": 45,  # Reduced from 60
    }
}

def get_timeout_for_url(url: str) -> int:
    domain = extract_domain(url)
    for tier_name, tier in TIMEOUT_TIERS.items():
        if "domains" in tier and domain in tier["domains"]:
            return tier["timeout"]
    return TIMEOUT_TIERS["default"]["timeout"]
```

### 2. Failed Domain Tracking

Track domains that consistently fail and reduce their timeout:

```python
class DomainTimeoutTracker:
    def __init__(self):
        self.failure_counts: Dict[str, int] = {}
        self.success_counts: Dict[str, int] = {}

    def record_result(self, domain: str, success: bool):
        if success:
            self.success_counts[domain] = self.success_counts.get(domain, 0) + 1
        else:
            self.failure_counts[domain] = self.failure_counts.get(domain, 0) + 1

    def get_adjusted_timeout(self, domain: str, base_timeout: int) -> int:
        failures = self.failure_counts.get(domain, 0)
        successes = self.success_counts.get(domain, 0)

        # If domain fails >3 times with no success, reduce timeout
        if failures >= 3 and successes == 0:
            return min(base_timeout, 15)

        # If domain fails >50% of time, reduce timeout
        total = failures + successes
        if total >= 5 and failures / total > 0.5:
            return min(base_timeout, 20)

        return base_timeout
```

### 3. Circuit Breaker for Domains

Stop trying domains that fail 5+ times in a row:

```python
class DomainCircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self.consecutive_failures: Dict[str, int] = {}
        self.threshold = failure_threshold

    def is_open(self, domain: str) -> bool:
        return self.consecutive_failures.get(domain, 0) >= self.threshold

    def record_failure(self, domain: str):
        self.consecutive_failures[domain] = self.consecutive_failures.get(domain, 0) + 1

    def record_success(self, domain: str):
        self.consecutive_failures[domain] = 0
```

## Files to Modify

- `src/tools/browser/tool.py`
- `src/tools/browser/manager.py`
- New: `src/core/domain_timeout.py`

## Acceptance Criteria

- [ ] Social media sites use 15s timeout instead of 60s
- [ ] Default timeout reduced to 45s
- [ ] Domains that fail 3+ times get reduced timeout
- [ ] Circuit breaker stops fetching after 5 consecutive failures
- [ ] Configurable timeout tiers in config.yaml

## Priority

**HIGH** - Browser timeouts are the biggest time sink.

## Estimate

3-4 hours implementation + testing
