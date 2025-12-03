"""
Runtime configuration and CLI overrides.
"""

import os
from typing import Optional, Literal, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from .settings import Settings


class RuntimeConfig(BaseModel):
    """Runtime configuration for application behavior."""

    headless: bool = False  # Run without UI, for CLI/API/CI use
    log_to_file: bool = False  # Redirect logs to file instead of stdout
    log_file_path: Optional[str] = None  # Path for log file
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    disable_interactive: bool = False  # Disable interactive prompts
    quiet: bool = False  # Suppress non-essential output
    verbose: bool = False  # Enable verbose output


class CLIConfig(BaseModel):
    """
    CLI argument overrides that take precedence over environment variables.

    This allows CLI arguments to override Settings values at runtime.
    Use apply_cli_overrides() to merge CLI args into settings.

    Example:
        cli_config = CLIConfig(
            verbose=True,
            log_level="DEBUG",
            max_search_results=10
        )
        settings = apply_cli_overrides(get_settings(), cli_config)
    """

    # Runtime overrides
    verbose: Optional[bool] = None
    quiet: Optional[bool] = None
    headless: Optional[bool] = None
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]] = None
    log_to_file: Optional[bool] = None
    log_file_path: Optional[str] = None
    disable_interactive: Optional[bool] = None

    # Research overrides
    max_search_results: Optional[int] = None
    concurrent_searches: Optional[int] = None
    tone: Optional[
        Literal["Objective", "Analytical", "Casual", "Professional", "Academic"]
    ] = None
    max_iterations: Optional[int] = None
    min_sources: Optional[int] = None
    max_sources: Optional[int] = None

    # AI provider override
    ai_provider: Optional[
        Literal["openai", "anthropic", "gemini", "groq", "ollama"]
    ] = None

    # Path overrides
    output_dir: Optional[str] = None
    cache_dir: Optional[str] = None

    # Cache overrides
    cache_enabled: Optional[bool] = None
    cache_ttl: Optional[int] = None


def apply_cli_overrides(settings: "Settings", cli: CLIConfig) -> "Settings":
    """
    Apply CLI configuration overrides to settings.

    CLI arguments take highest precedence over environment variables.
    This creates a modified settings instance without affecting the cached singleton.

    Args:
        settings: Base Settings instance
        cli: CLI configuration overrides

    Returns:
        Settings instance with CLI overrides applied
    """
    # Create a copy of settings data
    data = settings.model_dump()

    # Apply runtime overrides
    if cli.verbose is not None:
        data["runtime"]["verbose"] = cli.verbose
    if cli.quiet is not None:
        data["runtime"]["quiet"] = cli.quiet
    if cli.headless is not None:
        data["runtime"]["headless"] = cli.headless
    if cli.log_level is not None:
        data["runtime"]["log_level"] = cli.log_level
    if cli.log_to_file is not None:
        data["runtime"]["log_to_file"] = cli.log_to_file
    if cli.log_file_path is not None:
        data["runtime"]["log_file_path"] = cli.log_file_path
    if cli.disable_interactive is not None:
        data["runtime"]["disable_interactive"] = cli.disable_interactive

    # Apply research overrides
    if cli.max_search_results is not None:
        data["MAX_SEARCH_RESULTS"] = cli.max_search_results
    if cli.concurrent_searches is not None:
        data["CONCURRENT_SEARCHES"] = cli.concurrent_searches
    if cli.tone is not None:
        data["research"]["tone"] = cli.tone
    if cli.max_iterations is not None:
        data["research"]["max_iterations"] = cli.max_iterations
    if cli.min_sources is not None:
        data["research"]["min_sources"] = cli.min_sources
    if cli.max_sources is not None:
        data["research"]["max_sources"] = cli.max_sources

    # Apply AI provider override
    if cli.ai_provider is not None:
        data["ai"]["primary"] = cli.ai_provider

    # Apply cache overrides
    if cli.cache_enabled is not None:
        data["cache"]["enabled"] = cli.cache_enabled
    if cli.cache_ttl is not None:
        data["cache"]["default_ttl"] = cli.cache_ttl

    # Create new Settings with overrides (bypass validation for path overrides)
    # Import here to avoid circular dependency
    from .settings import Settings

    new_settings = Settings.model_validate(data)

    # Store path overrides as attributes (not in Pydantic model)
    if cli.output_dir is not None:
        new_settings._cli_output_dir = cli.output_dir
    if cli.cache_dir is not None:
        new_settings._cli_cache_dir = cli.cache_dir

    return new_settings
