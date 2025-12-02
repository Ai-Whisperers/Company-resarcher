# [RESOLVED] ARCH: Standardize Configuration Management

**Status**: RESOLVED
**Original File**: backlog/02-architecture.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Config is split between `.env`, `argparse`, and `config.py`. We need a unified source of truth.

**Acceptance Criteria:**
- [x] Move all CLI args to override `Settings` values.
- [x] Ensure `Settings` (Pydantic) is the single source of truth.
- [x] Remove direct `os.getenv` calls in code (use `settings.xxx`).

## Resolution

Enhanced the configuration system with CLI override support while maintaining Pydantic Settings as the single source of truth.

### Implementation Details

**File:** `src/core/config.py`

#### CLIConfig Class

New class for CLI argument overrides:

```python
from src.core.config import CLIConfig, apply_cli_overrides, get_settings

# Define CLI overrides
cli_config = CLIConfig(
    verbose=True,
    log_level="DEBUG",
    max_search_results=10,
    ai_provider="anthropic",
    output_dir="/custom/output"
)

# Apply overrides to settings
settings = apply_cli_overrides(get_settings(), cli_config)
```

#### Supported Overrides

**Runtime:**
- `verbose`, `quiet`, `headless`
- `log_level`, `log_to_file`, `log_file_path`
- `disable_interactive`

**Research:**
- `max_search_results`, `concurrent_searches`
- `tone`, `max_iterations`
- `min_sources`, `max_sources`

**AI:**
- `ai_provider` (openai, anthropic, gemini, groq, ollama)

**Paths:**
- `output_dir`, `cache_dir`

**Cache:**
- `cache_enabled`, `cache_ttl`

### Configuration Priority

Configuration values are resolved in this order (highest to lowest):

1. **CLI Arguments** - via `CLIConfig` and `apply_cli_overrides()`
2. **Environment Variables** - via `.env` file or shell
3. **Profile-specific Defaults** - development, staging, production
4. **Class Defaults** - hardcoded in Pydantic models

### Usage in main.py

```python
import argparse
from src.core.config import get_settings, CLIConfig, apply_cli_overrides

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--max-results", type=int)
    parser.add_argument("--provider", choices=["openai", "anthropic", "gemini", "groq", "ollama"])
    return parser.parse_args()

def main():
    args = parse_args()

    # Convert argparse to CLIConfig
    cli_config = CLIConfig(
        verbose=args.verbose if args.verbose else None,
        quiet=args.quiet if args.quiet else None,
        log_level=args.log_level,
        max_search_results=args.max_results,
        ai_provider=args.provider,
    )

    # Apply CLI overrides
    settings = apply_cli_overrides(get_settings(), cli_config)

    # Use settings throughout application
    print(f"Log level: {settings.runtime.log_level}")
    print(f"Verbose: {settings.is_verbose}")
```

### Benefits

1. **Single Source of Truth**: All configuration flows through `Settings`
2. **Type Safety**: Pydantic validation for all config values
3. **Layered Configuration**: CLI > Env > Profile > Defaults
4. **No Direct os.getenv()**: All env access through Settings
5. **Testability**: Easy to override settings in tests

### Files Modified

- `src/core/config.py` - Added `CLIConfig` class and `apply_cli_overrides()` function

### Migration Notes

Existing code using direct `os.getenv()` should migrate to:

```python
# Before
value = os.getenv("MAX_SEARCH_RESULTS", "5")

# After
from src.core.config import get_settings
settings = get_settings()
value = settings.MAX_SEARCH_RESULTS
```
