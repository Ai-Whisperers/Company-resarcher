# BUG-047: AI Provider Rate Limits Cause Mock Response Fallback

## Summary
When all AI providers (Groq, OpenAI) hit rate limits, the system falls back to generating MOCK responses that contain no actual analysis, resulting in reports filled with "N/A" values.

## Severity
**CRITICAL** - Renders entire research output useless

## Symptoms
```
19:32:35 - ai_client - WARNING - Selected provider groq failed: [groq] Error code: 429 - Rate limit reached for model `llama-3.3-70b-versatile`... Limit 100000, Used 99462, Requested 2578. Please try again in 29m22.56s.
19:32:35 - ai_client - INFO - Attempting fallback...
19:32:40 - ai_client - WARNING - Fallback provider failed: [openai] Rate limit exceeded
19:32:40 - ai_client - WARNING - All providers failed, using mock
19:32:40 - ai_client - INFO - Generating MOCK response
```

### Output Example (market.md)
```markdown
**TAM (Total Addressable Market):** N/A
**SAM (Serviceable Available Market):** N/A
**SOM (Serviceable Obtainable Market):** N/A
**CAGR:** N/A
**Forecast (2025-2030):** N/A
### Key Growth Drivers
- N/A
```

## Root Cause
1. **Groq**: Daily token limit (100,000 tokens) exhausted across organization
2. **OpenAI**: Rate limit exceeded (possibly billing tier limit)
3. **Fallback to Mock**: When all providers fail, system uses mock generator that returns empty/template responses

## Impact
- **All 5 research phases** produced empty analysis
- **Sources gathered but not analyzed** - wasted API calls/bandwidth
- **User receives unusable output** - must re-run later
- **No user notification** - appears successful but content is empty

## Affected Files
- `src/core/ai_client.py` - Provider selection and fallback logic
- `src/core/mock_ai.py` (if exists) - Mock response generator

## Proposed Solutions

### Solution 1: Add More AI Providers (Recommended)
Add Anthropic Claude and Google Gemini to the fallback chain:
```python
AI_PROVIDERS = [
    ("groq", GroqProvider),      # Fast, free tier
    ("openai", OpenAIProvider),  # Quality fallback
    ("anthropic", AnthropicProvider),  # New fallback
    ("gemini", GeminiProvider),  # New fallback (generous free tier)
    ("ollama", OllamaProvider),  # Local fallback (no rate limits)
]
```

### Solution 2: Graceful Degradation with User Notification
Instead of mock responses, return partial results with clear warnings:
```python
if all_providers_failed:
    return AnalysisResult(
        status="rate_limited",
        message="All AI providers rate limited. Try again in 30 minutes.",
        partial_data={"sources_gathered": len(sources)},
        retry_after=1800,
    )
```

### Solution 3: Request Queuing with Retry
Implement exponential backoff with queuing:
```python
class RateLimitAwareClient:
    async def generate_with_retry(self, prompt, max_retries=3):
        for attempt in range(max_retries):
            try:
                return await self._generate(prompt)
            except RateLimitError as e:
                wait_time = e.retry_after or (2 ** attempt * 10)
                logger.warning(f"Rate limited, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
        raise AllProvidersExhaustedError()
```

### Solution 4: Pre-flight Rate Limit Check
Before starting research, check remaining quota:
```python
async def check_quota_available(self) -> bool:
    for provider in self.providers:
        if await provider.has_remaining_quota():
            return True
    return False

# In orchestrator:
if not await ai_client.check_quota_available():
    raise InsufficientQuotaError("No AI providers available. Try again later.")
```

## Additional Recommendations

### 1. Add Ollama as Local Fallback
```python
# No rate limits, runs locally
self.providers.append(OllamaProvider(model="llama3.1:8b"))
```

### 2. Implement Token Usage Tracking
```python
class TokenTracker:
    def __init__(self):
        self.daily_usage = {}

    def can_make_request(self, provider: str, estimated_tokens: int) -> bool:
        limit = PROVIDER_LIMITS.get(provider, float('inf'))
        used = self.daily_usage.get(provider, 0)
        return used + estimated_tokens <= limit
```

### 3. Cache Analysis Results
```python
# Don't re-analyze same sources
cache_key = hash(sorted([s.url for s in sources]))
if cached := await cache.get(cache_key):
    return cached
```

## Test Cases
1. Mock all providers returning 429 → verify graceful error, no mock response
2. Verify Anthropic/Gemini are tried as fallbacks
3. Verify Ollama works as final fallback (if configured)
4. Verify retry logic respects Retry-After headers
5. Verify user sees clear message when rate limited

## Acceptance Criteria
- [ ] At least 4 AI providers in fallback chain
- [ ] No mock responses in production output
- [ ] Clear error message when all providers exhausted
- [ ] Retry-After headers respected
- [ ] Token usage tracked to predict failures

## Related Issues
- BUG-041: Analysis returns all N/A values (downstream effect)
- TECH-034: Add Ollama local fallback

## Labels
`critical`, `bug`, `ai-client`, `rate-limit`, `user-experience`
