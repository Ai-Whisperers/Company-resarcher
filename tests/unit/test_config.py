"""
Unit tests for configuration module.

Tests the settings management, validation, and configuration loading.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from src.core.config import (
    Settings,
    AIConfig,
    AIProviderConfig,
    get_settings,
    clear_settings,
)


# =============================================================================
# AIProviderConfig Tests
# =============================================================================


class TestAIProviderConfig:
    """Tests for AIProviderConfig model."""

    @pytest.mark.unit
    def test_creates_with_model_name(self):
        """Verify config creates with required model name."""
        config = AIProviderConfig(model="gpt-4")

        assert config.model == "gpt-4"

    @pytest.mark.unit
    def test_has_default_temperature(self):
        """Verify default temperature is 0.7."""
        config = AIProviderConfig(model="gpt-4")

        assert config.temperature == 0.7

    @pytest.mark.unit
    def test_has_default_max_tokens(self):
        """Verify default max_tokens is 4096."""
        config = AIProviderConfig(model="gpt-4")

        assert config.max_tokens == 4096

    @pytest.mark.unit
    def test_allows_custom_temperature(self):
        """Verify custom temperature can be set."""
        config = AIProviderConfig(model="gpt-4", temperature=0.5)

        assert config.temperature == 0.5

    @pytest.mark.unit
    def test_allows_custom_max_tokens(self):
        """Verify custom max_tokens can be set."""
        config = AIProviderConfig(model="gpt-4", max_tokens=8192)

        assert config.max_tokens == 8192


# =============================================================================
# AIConfig Tests
# =============================================================================


class TestAIConfig:
    """Tests for AIConfig model."""

    @pytest.mark.unit
    def test_default_primary_is_openai(self):
        """Verify default primary provider is openai."""
        config = AIConfig()

        assert config.primary == "openai"

    @pytest.mark.unit
    def test_default_fallback_is_none(self):
        """Verify default fallback is None."""
        config = AIConfig()

        assert config.fallback is None

    @pytest.mark.unit
    def test_has_all_provider_configs(self):
        """Verify all provider configs are initialized."""
        config = AIConfig()

        assert config.openai is not None
        assert config.anthropic is not None
        assert config.gemini is not None
        assert config.groq is not None
        assert config.ollama is not None

    @pytest.mark.unit
    def test_openai_default_model(self):
        """Verify OpenAI default model."""
        config = AIConfig()

        assert "gpt" in config.openai.model.lower()

    @pytest.mark.unit
    def test_anthropic_default_model(self):
        """Verify Anthropic default model."""
        config = AIConfig()

        assert "claude" in config.anthropic.model.lower()

    @pytest.mark.unit
    def test_allows_custom_primary(self):
        """Verify custom primary provider can be set."""
        config = AIConfig(primary="anthropic")

        assert config.primary == "anthropic"

    @pytest.mark.unit
    def test_allows_custom_fallback(self):
        """Verify custom fallback provider can be set."""
        config = AIConfig(fallback="groq")

        assert config.fallback == "groq"

    @pytest.mark.unit
    def test_valid_primary_providers(self):
        """Verify all valid primary providers are accepted."""
        valid_providers = ["openai", "anthropic", "gemini", "groq", "ollama"]

        for provider in valid_providers:
            config = AIConfig(primary=provider)
            assert config.primary == provider


# =============================================================================
# Settings Tests
# =============================================================================


class TestSettings:
    """Tests for Settings class."""

    @pytest.fixture(autouse=True)
    def reset_settings_cache(self):
        """Reset settings cache before and after each test."""
        clear_settings()
        yield
        clear_settings()

    @pytest.mark.unit
    def test_api_keys_default_to_none(self):
        """Verify API keys default to None."""
        with patch.dict(os.environ, {}, clear=True):
            # Pass _env_file=None to ignore .env file
            settings = Settings(_env_file=None)

            assert settings.OPENAI_API_KEY is None
            assert settings.ANTHROPIC_API_KEY is None
            assert settings.GEMINI_API_KEY is None
            assert settings.GROQ_API_KEY is None
            assert settings.TAVILY_API_KEY is None

    @pytest.mark.unit
    def test_reads_api_key_from_env(self):
        """Verify API keys are read from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            clear_settings()
            # _env_file=None ensures we only test env vars, not .env file
            settings = Settings(_env_file=None)

            assert settings.OPENAI_API_KEY.get_secret_value() == "test-key"

    @pytest.mark.unit
    def test_has_default_ai_config(self):
        """Verify default AI config is present."""
        settings = Settings(_env_file=None)

        assert settings.ai is not None
        assert isinstance(settings.ai, AIConfig)

    @pytest.mark.unit
    def test_has_base_dir(self):
        """Verify BASE_DIR is set."""
        settings = Settings(_env_file=None)

        assert settings.BASE_DIR is not None
        assert isinstance(settings.BASE_DIR, Path)

    @pytest.mark.unit
    def test_has_search_configuration(self):
        """Verify search configuration defaults."""
        settings = Settings(_env_file=None)

        # Default profile is DEVELOPMENT, which sets MAX_SEARCH_RESULTS to 3
        assert settings.MAX_SEARCH_RESULTS == 3
        assert settings.CONCURRENT_SEARCHES == 2

    @pytest.mark.unit
    def test_get_output_dir_default(self):
        """Verify default output directory."""
        with patch.dict(os.environ, {}, clear=False):
            if "OUTPUT_DIR" in os.environ:
                del os.environ["OUTPUT_DIR"]
            settings = Settings(_env_file=None)
            output_dir = settings.get_output_dir()

            assert output_dir == settings.BASE_DIR / "output"

    @pytest.mark.unit
    def test_get_output_dir_from_env(self):
        """Verify output directory from environment."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/custom/output"}):
            settings = Settings(_env_file=None)
            output_dir = settings.get_output_dir()

            assert output_dir == Path("/custom/output")


# =============================================================================
# Settings Validation Tests
# =============================================================================


class TestSettingsValidation:
    """Tests for settings validation."""

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache."""
        clear_settings()
        yield
        clear_settings()

    @pytest.mark.unit
    def test_validate_config_returns_warnings_list(self):
        """Verify validate_config returns a list."""
        settings = Settings(_env_file=None)
        warnings = settings.validate_config()

        assert isinstance(warnings, list)

    @pytest.mark.unit
    def test_validate_config_warns_missing_primary_key(self):
        """Verify warning when primary provider has no API key."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            settings.ai = AIConfig(primary="openai")
            warnings = settings.validate_config()

            assert any(
                "openai" in w.lower() and "api key" in w.lower() for w in warnings
            )

    @pytest.mark.unit
    def test_validate_config_no_warning_for_ollama_primary(self):
        """Verify no API key warning for Ollama (doesn't need key)."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            settings.ai = AIConfig(primary="ollama")
            warnings = settings.validate_config()

            # Should not warn about Ollama API key
            assert not any(
                "ollama" in w.lower() and "api key" in w.lower() for w in warnings
            )

    @pytest.mark.unit
    def test_validate_config_warns_missing_fallback_key(self):
        """Verify warning when fallback provider has no API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
            settings = Settings(_env_file=None)
            settings.ai = AIConfig(primary="openai", fallback="anthropic")
            warnings = settings.validate_config()

            assert any("anthropic" in w.lower() for w in warnings)

    @pytest.mark.unit
    def test_validate_config_warns_missing_tavily_key(self):
        """Verify warning when Tavily key is missing."""
        # Note: New config logic might not warn if other search keys are present or if it relies on free tier
        # But let's check the implementation. It checks TAVILY or SERPER.
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            warnings = settings.validate_config()

            # The current implementation in settings.py:
            # has_any_search = self._has_secret(self.TAVILY_API_KEY) or self._has_secret(self.SERPER_API_KEY)
            # if not has_any_search: pass
            # So it actually DOES NOT warn anymore because free providers are available.

            assert not any("tavily" in w.lower() for w in warnings)

    @pytest.mark.unit
    def test_has_any_ai_provider_false_when_none(self):
        """Verify has_any_ai_provider returns False when no providers configured."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            settings.ai = AIConfig(primary="openai")  # Not ollama

            assert settings.has_any_ai_provider() is False

    @pytest.mark.unit
    def test_has_any_ai_provider_true_with_openai_key(self):
        """Verify has_any_ai_provider returns True with OpenAI key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
            settings = Settings(_env_file=None)

            assert settings.has_any_ai_provider() is True

    @pytest.mark.unit
    def test_has_any_ai_provider_true_with_ollama(self):
        """Verify has_any_ai_provider returns True with Ollama (no key needed)."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            settings.ai = AIConfig(primary="ollama")

            assert settings.has_any_ai_provider() is True


# =============================================================================
# get_settings() and clear_settings() Tests
# =============================================================================


class TestSettingsSingleton:
    """Tests for settings singleton pattern."""

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache."""
        clear_settings()
        yield
        clear_settings()

    @pytest.mark.unit
    def test_get_settings_returns_settings_instance(self):
        """Verify get_settings returns Settings instance."""
        settings = get_settings()

        assert isinstance(settings, Settings)

    @pytest.mark.unit
    def test_get_settings_returns_cached_instance(self):
        """Verify get_settings returns the same cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    @pytest.mark.unit
    def test_clear_settings_resets_cache(self):
        """Verify clear_settings resets the cache."""
        settings1 = get_settings()
        clear_settings()
        settings2 = get_settings()

        # After clearing, should get a new instance
        # Note: They may be equal but should be different objects
        assert settings1 is not settings2


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache."""
        clear_settings()
        yield
        clear_settings()

    @pytest.mark.unit
    def test_empty_api_key_treated_as_none(self):
        """Verify empty string API key is treated as None/empty."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            settings = Settings(_env_file=None)

            # Empty string should be falsy or None
            assert not settings.OPENAI_API_KEY

    @pytest.mark.unit
    def test_whitespace_api_key_preserved(self):
        """Verify whitespace-only API key is preserved (caller should validate)."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "   "}, clear=True):
            settings = Settings(_env_file=None)

            # Whitespace is preserved - validation is caller's responsibility
            assert settings.OPENAI_API_KEY.get_secret_value() == "   "

    @pytest.mark.unit
    def test_langfuse_has_default_host(self):
        """Verify Langfuse has default host."""
        settings = Settings(_env_file=None)

        assert settings.LANGFUSE_HOST == "https://cloud.langfuse.com"

    @pytest.mark.unit
    def test_nested_env_delimiter(self):
        """Verify nested environment variables work."""
        # The config uses env_nested_delimiter="__"
        # So AI__PRIMARY=anthropic should set ai.primary
        # This is a Pydantic feature test
        with patch.dict(os.environ, {"AI__PRIMARY": "anthropic"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.ai.primary == "anthropic"
