# Appendices

## Appendix A: File Mapping

### Files to Delete After Migration

- `src/core/configs.py` (merged into config/)
- `src/core/constants.py` (merged into config/defaults.py)
- `src/core/rate_limiter.py` (replaced by rate_limiting/)

### Files to Split

- `src/graph/graph_builder.py` (1,981 lines) → graph/builder/
- `src/pipeline/comprehensive_research.py` (1,400 lines) → pipeline/orchestration/
- `src/graph/state.py` (1,210 lines) → graph/state/
- `src/api/app.py` (1,114 lines) → api/routers/
- `src/core/validators.py` (980 lines) → core/validation/
- `src/core/ai_client.py` (963 lines) → core/ai/

### Files to Refactor In Place

- `src/core/cache.py` - Implement CacheProvider interface
- All 47 tool files - Extend BaseTool
- All search providers - Extend HTTPSearchProvider
- All AI client wrappers - Extend DelegatingAIClient

## Appendix B: New Package Structure

### Packages to Create

```
src/core/rate_limiting/     # Unified rate limiting
src/core/cache/             # Cache interface
src/core/ai/                # AI client reorganization
src/tools/search/http/      # HTTP provider base
src/core/storage/           # File I/O patterns
```

### Key New Classes

| Class                | Purpose                                 |
| -------------------- | --------------------------------------- |
| RateLimiterManager   | Unified rate limiting for all providers |
| CacheProvider        | Abstract cache interface                |
| CacheManager         | Cache facade                            |
| ProviderFactory      | Creates AI client instances             |
| FallbackChainManager | Manages provider fallback order         |
| DelegatingAIClient   | Base for AI client wrappers             |
| HTTPSearchProvider   | Base for HTTP search providers          |
| ProviderErrorParser  | Unified error detection                 |
| ServiceBase          | Standard service interface              |
| FileStorage          | Generic file I/O                        |
