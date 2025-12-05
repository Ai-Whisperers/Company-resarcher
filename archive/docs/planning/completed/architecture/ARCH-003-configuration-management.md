# ARCH-003: Centralized Configuration Management

## Priority: Medium
## Category: Architecture
## Status: Complete ✅

## Summary

Consolidate all configuration into a single, validated configuration system.

## Implementation Tasks

- [x] Merge all config classes into config.py
- [x] Add configuration validation
- [x] Support configuration profiles (dev, staging, prod)
- [ ] Add configuration hot-reloading (deferred - not needed currently)
- [x] Document all configuration options

## Implementation Details

### Location

`src/core/config.py`

### Features Implemented

1. **Environment Profiles**

   ```python
   from src.core.config import Profile, get_profile, is_production

   # Profiles: development, staging, production
   # Set via APP_PROFILE or ENVIRONMENT env var
   profile = get_profile()

   if is_production():
       # Production-specific logic
   ```

2. **Profile-Specific Defaults**

   | Setting | Development | Staging | Production |
   |---------|-------------|---------|------------|
   | log_level | DEBUG | INFO | WARNING |
   | verbose | True | False | False |
   | headless | False | False | True |
   | MAX_SEARCH_RESULTS | 3 | 5 | 10 |
   | CONCURRENT_SEARCHES | 2 | 3 | 5 |

3. **Configuration Priority**

   1. Environment variables (highest)
   2. `.env` file
   3. Profile-specific defaults
   4. Class defaults (lowest)

4. **Nested Configuration**

   ```bash
   # Set nested config via environment
   export AI__PRIMARY=anthropic
   export RUNTIME__LOG_LEVEL=DEBUG
   ```

5. **Validation**

   ```python
   settings = get_settings()
   warnings = settings.validate_config()
   # Returns list of validation warnings (graceful degradation)
   ```

6. **SecretStr Protection**

   API keys use `SecretStr` to prevent accidental exposure in logs/repr.

### Configuration Classes

- `Profile` - Environment enum (development, staging, production)
- `ProfileDefaults` - Profile-specific default values
- `AIProviderConfig` - Per-provider AI settings (model, temperature, max_tokens)
- `AIConfig` - AI provider selection and configuration
- `RuntimeConfig` - Runtime behavior (headless, logging, verbosity)
- `Settings` - Main settings class with all configuration

### Helper Functions

- `get_settings()` - Get cached settings instance
- `get_profile()` - Get current profile
- `is_production()` - Check if production profile
- `is_development()` - Check if development profile
- `clear_settings()` - Clear cache (for testing)
