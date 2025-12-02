# Core Module API Reference

The `src.core` module contains the fundamental components of the Company Researcher system.

## Configuration

::: src.core.config
    options:
      members:
        - Settings
        - get_settings

## AI Client

::: src.core.ai_client
    options:
      members:
        - AIClient

## Cached AI Client

::: src.core.cached_ai_client
    options:
      members:
        - CachedAIClient

## Rate Limited Client

::: src.core.rate_limited_client
    options:
      members:
        - RateLimitedClient

## Output Manager

::: src.core.output_manager
    options:
      members:
        - OutputManager
        - OutputFormat

## Knowledge Vault

::: src.core.vault
    options:
      members:
        - KnowledgeVault
        - VaultEntry

## URL Validator

::: src.core.url_validator
    options:
      members:
        - URLValidator
        - URLValidationError

## Circuit Breaker

::: src.core.circuit_breaker
    options:
      members:
        - CircuitBreaker
        - CircuitState

## Concurrency Manager

::: src.core.concurrency_manager
    options:
      members:
        - ConcurrencyManager
        - ConcurrencyStrategy
        - get_concurrency_manager

## Logger

::: src.core.logger
    options:
      members:
        - setup_logger
        - StructuredJSONFormatter

## Types

::: src.core.types
    options:
      show_if_no_docstring: true
