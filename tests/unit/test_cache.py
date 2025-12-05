"""
Unit tests for AI cache module.

Tests the file-based caching system for AI responses, including:
- Cache key generation
- Cache get/set operations
- Thread safety
- Error handling
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import hashlib
from pathlib import Path
import threading
import time

from src.core.cache import AICache, get_ai_cache


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / ".cache" / "ai_responses"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def cache_instance(temp_cache_dir):
    """Create a fresh cache instance with temporary directory."""
    # Reset singleton
    AICache._instance = None

    with patch("src.core.cache.manager.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.BASE_DIR = temp_cache_dir.parent.parent
        mock_settings.get_cache_dir.return_value = temp_cache_dir
        mock_get_settings.return_value = mock_settings
        cache = AICache()
        cache.cache_dir = temp_cache_dir
        yield cache

    # Cleanup singleton
    AICache._instance = None


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton before and after each test."""
    AICache._instance = None
    yield
    AICache._instance = None


# =============================================================================
# Cache Key Generation Tests
# =============================================================================


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @pytest.mark.unit
    def test_generates_consistent_key(self, cache_instance):
        """Verify same inputs generate same key."""
        key1 = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)
        key2 = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)

        assert key1 == key2

    @pytest.mark.unit
    def test_different_prompts_different_keys(self, cache_instance):
        """Verify different prompts generate different keys."""
        key1 = cache_instance._get_cache_key("prompt1", "system", 0.7, 4096)
        key2 = cache_instance._get_cache_key("prompt2", "system", 0.7, 4096)

        assert key1 != key2

    @pytest.mark.unit
    def test_different_systems_different_keys(self, cache_instance):
        """Verify different system prompts generate different keys."""
        key1 = cache_instance._get_cache_key("prompt", "system1", 0.7, 4096)
        key2 = cache_instance._get_cache_key("prompt", "system2", 0.7, 4096)

        assert key1 != key2

    @pytest.mark.unit
    def test_different_temperatures_different_keys(self, cache_instance):
        """Verify different temperatures generate different keys."""
        key1 = cache_instance._get_cache_key("prompt", "system", 0.5, 4096)
        key2 = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)

        assert key1 != key2

    @pytest.mark.unit
    def test_different_max_tokens_different_keys(self, cache_instance):
        """Verify different max_tokens generate different keys."""
        key1 = cache_instance._get_cache_key("prompt", "system", 0.7, 2048)
        key2 = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)

        assert key1 != key2

    @pytest.mark.unit
    def test_none_system_handled(self, cache_instance):
        """Verify None system prompt is handled."""
        key = cache_instance._get_cache_key("prompt", None, 0.7, 4096)

        assert key is not None
        assert len(key) == 64  # SHA256 hex length

    @pytest.mark.unit
    def test_key_is_sha256_hex(self, cache_instance):
        """Verify key is valid SHA256 hexadecimal."""
        key = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)

        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    @pytest.mark.unit
    def test_unicode_in_prompt_handled(self, cache_instance):
        """Verify unicode characters in prompt are handled."""
        key = cache_instance._get_cache_key("测试 مرحبا 🚀", "system", 0.7, 4096)

        assert key is not None
        assert len(key) == 64


# =============================================================================
# Cache Get Tests
# =============================================================================


class TestCacheGet:
    """Tests for cache get operations."""

    @pytest.mark.unit
    def test_returns_none_for_missing_key(self, cache_instance):
        """Verify get returns None for non-existent key."""
        result = cache_instance.get("nonexistent", None, 0.7, 4096)

        assert result is None

    @pytest.mark.unit
    def test_returns_cached_response(self, cache_instance, temp_cache_dir):
        """Verify get returns cached response."""
        # Create a cache file manually
        key = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)
        cache_file = temp_cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({"response": "cached response"}))

        result = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result == "cached response"

    @pytest.mark.unit
    def test_returns_none_for_invalid_json(self, cache_instance, temp_cache_dir):
        """Verify get returns None for invalid JSON."""
        key = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)
        cache_file = temp_cache_dir / f"{key}.json"
        cache_file.write_text("not valid json {{{")

        result = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_missing_response_key(self, cache_instance, temp_cache_dir):
        """Verify get returns None when response key missing."""
        key = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)
        cache_file = temp_cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({"other": "data"}))

        result = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result is None


# =============================================================================
# Cache Set Tests
# =============================================================================


class TestCacheSet:
    """Tests for cache set operations."""

    @pytest.mark.unit
    def test_creates_cache_file(self, cache_instance, temp_cache_dir):
        """Verify set creates cache file."""
        cache_instance.set("prompt", "response", "system", 0.7, 4096)

        key = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)
        cache_file = temp_cache_dir / f"{key}.json"

        assert cache_file.exists()

    @pytest.mark.unit
    def test_cache_file_contains_response(self, cache_instance, temp_cache_dir):
        """Verify cache file contains the response."""
        cache_instance.set("prompt", "test response", "system", 0.7, 4096)

        key = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)
        cache_file = temp_cache_dir / f"{key}.json"
        data = json.loads(cache_file.read_text())

        assert data["response"] == "test response"

    @pytest.mark.unit
    def test_cache_file_contains_metadata(self, cache_instance, temp_cache_dir):
        """Verify cache file contains all metadata."""
        cache_instance.set("my prompt", "response", "my system", 0.5, 2048)

        key = cache_instance._get_cache_key("my prompt", "my system", 0.5, 2048)
        cache_file = temp_cache_dir / f"{key}.json"
        data = json.loads(cache_file.read_text())

        assert data["prompt"] == "my prompt"
        assert data["system"] == "my system"
        assert data["temperature"] == 0.5
        assert data["max_tokens"] == 2048

    @pytest.mark.unit
    def test_overwrites_existing_cache(self, cache_instance, temp_cache_dir):
        """Verify set overwrites existing cache entry."""
        cache_instance.set("prompt", "response1", "system", 0.7, 4096)
        cache_instance.set("prompt", "response2", "system", 0.7, 4096)

        result = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result == "response2"

    @pytest.mark.unit
    def test_handles_unicode_response(self, cache_instance, temp_cache_dir):
        """Verify unicode responses are cached correctly."""
        unicode_response = "Response with unicode: 你好 مرحبا 🎉"
        cache_instance.set("prompt", unicode_response, "system", 0.7, 4096)

        result = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result == unicode_response


# =============================================================================
# Cache Round-Trip Tests
# =============================================================================


class TestCacheRoundTrip:
    """Tests for cache set then get operations."""

    @pytest.mark.unit
    def test_set_then_get_returns_value(self, cache_instance):
        """Verify set followed by get returns the value."""
        cache_instance.set("prompt", "response", "system", 0.7, 4096)
        result = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result == "response"

    @pytest.mark.unit
    def test_different_params_independent(self, cache_instance):
        """Verify different parameters have independent cache entries."""
        cache_instance.set("prompt", "response1", "system", 0.5, 4096)
        cache_instance.set("prompt", "response2", "system", 0.7, 4096)

        result1 = cache_instance.get("prompt", "system", 0.5, 4096)
        result2 = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result1 == "response1"
        assert result2 == "response2"


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for singleton pattern."""

    @pytest.mark.unit
    def test_get_ai_cache_returns_same_instance(self):
        """Verify get_ai_cache returns the same instance."""
        with patch("src.core.cache.settings") as mock_settings:
            mock_settings.BASE_DIR = Path("/tmp")

            AICache._instance = None
            cache1 = get_ai_cache()
            cache2 = get_ai_cache()

            assert cache1 is cache2

    @pytest.mark.unit
    def test_singleton_created_once(self):
        """Verify singleton is only created once."""
        with patch("src.core.cache.settings") as mock_settings:
            mock_settings.BASE_DIR = Path("/tmp")

            AICache._instance = None

            with patch.object(AICache, "__init__", return_value=None) as mock_init:
                # First call should create instance
                cache1 = AICache()
                cache1._initialized = True

                # Mock the singleton to return same instance
                AICache._instance = cache1

                # Second call should reuse instance
                cache2 = AICache()

                # __init__ called but should return early if _initialized
                assert cache1 is cache2


# =============================================================================
# Thread Safety Tests
# =============================================================================


class TestThreadSafety:
    """Tests for thread safety."""

    @pytest.mark.unit
    def test_concurrent_get_operations(self, cache_instance, temp_cache_dir):
        """Verify concurrent get operations are thread-safe."""
        # Pre-populate cache
        cache_instance.set("prompt", "response", "system", 0.7, 4096)

        results = []
        errors = []

        def get_cache():
            try:
                result = cache_instance.get("prompt", "system", 0.7, 4096)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_cache) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(r == "response" for r in results)

    @pytest.mark.unit
    def test_concurrent_set_operations(self, cache_instance):
        """Verify concurrent set operations don't crash."""
        errors = []

        def set_cache(i):
            try:
                cache_instance.set(f"prompt{i}", f"response{i}", "system", 0.7, 4096)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=set_cache, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    @pytest.mark.unit
    def test_aicache_singleton_thread_safety(self):
        """Verify AICache singleton is thread-safe (CQ-001 fix verification)."""
        from src.core.cache.manager import AICache

        # Reset singleton
        AICache._instance = None

        instances = []
        errors = []

        def get_instance():
            try:
                instances.append(AICache())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_instance) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        # All instances should be the same object
        instance_ids = [id(i) for i in instances]
        assert len(set(instance_ids)) == 1, f"Multiple instances created: {set(instance_ids)}"

        # Cleanup
        AICache._instance = None

    @pytest.mark.unit
    def test_cachemanager_singleton_thread_safety(self):
        """Verify CacheManager singleton is thread-safe (CQ-001 fix verification)."""
        from src.core.cache.manager import CacheManager

        # Reset singleton
        CacheManager._instance = None

        instances = []
        errors = []

        def get_instance():
            try:
                instances.append(CacheManager())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_instance) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        # All instances should be the same object
        instance_ids = [id(i) for i in instances]
        assert len(set(instance_ids)) == 1, f"Multiple instances created: {set(instance_ids)}"

        # Cleanup
        CacheManager._instance = None

    @pytest.mark.unit
    def test_get_cache_manager_thread_safety(self):
        """Verify get_cache_manager() is thread-safe."""
        from src.core.cache.manager import get_cache_manager, CacheManager
        import src.core.cache.manager as manager_module

        # Reset singleton
        CacheManager._instance = None
        manager_module._cache_manager = None

        instances = []
        errors = []

        def get_instance():
            try:
                instances.append(get_cache_manager())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_instance) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        # All instances should be the same object
        instance_ids = [id(i) for i in instances]
        assert len(set(instance_ids)) == 1, f"Multiple global managers: {set(instance_ids)}"

        # Cleanup
        CacheManager._instance = None
        manager_module._cache_manager = None

    @pytest.mark.unit
    def test_get_cache_concurrent_access(self):
        """Verify concurrent get_cache() calls are thread-safe."""
        from src.core.cache.manager import CacheManager

        # Reset and create fresh manager
        CacheManager._instance = None
        manager = CacheManager()

        caches = []
        errors = []

        def get_cache():
            try:
                cache = manager.get_cache("test_cache")
                caches.append(cache)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_cache) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        # All caches should be the same object (same name = same cache)
        cache_ids = [id(c) for c in caches]
        assert len(set(cache_ids)) == 1, f"Multiple caches created for same name: {set(cache_ids)}"

        # Cleanup
        CacheManager._instance = None


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.unit
    def test_get_handles_io_error(self, cache_instance, temp_cache_dir):
        """Verify get handles IO errors gracefully."""
        key = cache_instance._get_cache_key("prompt", "system", 0.7, 4096)
        cache_file = temp_cache_dir / f"{key}.json"

        # Create a directory with same name to cause IO error
        cache_file.mkdir(parents=True, exist_ok=True)

        result = cache_instance.get("prompt", "system", 0.7, 4096)

        # Should return None, not raise
        assert result is None

    @pytest.mark.unit
    def test_set_handles_permission_error(self, cache_instance):
        """Verify set handles permission errors gracefully."""
        # Make cache_dir read-only (this may not work on all systems)
        original_dir = cache_instance.cache_dir

        with patch.object(cache_instance, "cache_dir", Path("/nonexistent/path")):
            # Should not raise, just log warning
            cache_instance.set("prompt", "response", "system", 0.7, 4096)

        cache_instance.cache_dir = original_dir


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.unit
    def test_empty_prompt(self, cache_instance):
        """Verify empty prompt is handled."""
        cache_instance.set("", "response", "system", 0.7, 4096)
        result = cache_instance.get("", "system", 0.7, 4096)

        assert result == "response"

    @pytest.mark.unit
    def test_empty_response(self, cache_instance):
        """Verify empty response is cached."""
        cache_instance.set("prompt", "", "system", 0.7, 4096)
        result = cache_instance.get("prompt", "system", 0.7, 4096)

        assert result == ""

    @pytest.mark.unit
    def test_very_long_prompt(self, cache_instance):
        """Verify very long prompt is handled."""
        long_prompt = "x" * 100000
        cache_instance.set(long_prompt, "response", "system", 0.7, 4096)
        result = cache_instance.get(long_prompt, "system", 0.7, 4096)

        assert result == "response"

    @pytest.mark.unit
    def test_special_characters_in_prompt(self, cache_instance):
        """Verify special characters in prompt are handled."""
        special_prompt = 'prompt with "quotes" and \n newlines and \t tabs'
        cache_instance.set(special_prompt, "response", "system", 0.7, 4096)
        result = cache_instance.get(special_prompt, "system", 0.7, 4096)

        assert result == "response"

    @pytest.mark.unit
    def test_zero_temperature(self, cache_instance):
        """Verify zero temperature is handled."""
        cache_instance.set("prompt", "response", "system", 0.0, 4096)
        result = cache_instance.get("prompt", "system", 0.0, 4096)

        assert result == "response"

    @pytest.mark.unit
    def test_very_large_max_tokens(self, cache_instance):
        """Verify very large max_tokens is handled."""
        cache_instance.set("prompt", "response", "system", 0.7, 1000000)
        result = cache_instance.get("prompt", "system", 0.7, 1000000)

        assert result == "response"
