"""
Base configuration classes and utilities.
"""

import os
import threading
from enum import Enum
from typing import Optional, Any
from pydantic import SecretStr


class Profile(str, Enum):
    """Application environment profiles."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def from_env(cls) -> "Profile":
        """Get profile from environment variable."""
        env_value = os.getenv("APP_PROFILE", os.getenv("ENVIRONMENT", "development"))
        try:
            return cls(env_value.lower())
        except ValueError:
            return cls.DEVELOPMENT


class KeyRotationStrategy(str, Enum):
    """API key rotation strategies (SEC-001)."""

    ROUND_ROBIN = "round_robin"  # Rotate through keys sequentially
    FAILOVER = "failover"  # Use primary until it fails, then fallback


class APIKeyPool:
    """
    Thread-safe API key rotation pool (SEC-001).

    Supports multiple API keys per provider with round-robin or failover strategy.
    Keys can be provided as comma-separated values in env vars:
        OPENAI_API_KEY=key1,key2,key3

    Usage:
        pool = APIKeyPool(["key1", "key2"], strategy=KeyRotationStrategy.ROUND_ROBIN)
        key = pool.get_key()  # Returns next key in rotation
        pool.mark_failed("key1")  # Mark key as failed (will skip in rotation)
    """

    def __init__(
        self,
        keys: list[str],
        strategy: KeyRotationStrategy = KeyRotationStrategy.ROUND_ROBIN,
    ):
        self._keys = [k.strip() for k in keys if k and k.strip()]
        self._strategy = strategy
        self._current_index = 0
        self._failed_keys: set[str] = set()
        self._lock = threading.Lock()

    @property
    def available_keys(self) -> list[str]:
        """Get list of non-failed keys."""
        with self._lock:
            return [k for k in self._keys if k not in self._failed_keys]

    @property
    def has_keys(self) -> bool:
        """Check if any keys are available."""
        return len(self.available_keys) > 0

    @property
    def key_count(self) -> int:
        """Get total number of keys (including failed)."""
        return len(self._keys)

    def get_key(self) -> Optional[str]:
        """
        Get the next API key based on rotation strategy.

        Returns:
            API key string, or None if no keys available.
        """
        with self._lock:
            available = [k for k in self._keys if k not in self._failed_keys]
            if not available:
                return None

            if self._strategy == KeyRotationStrategy.FAILOVER:
                # Always return first available key
                return available[0]

            # Round-robin: cycle through available keys
            self._current_index = self._current_index % len(available)
            key = available[self._current_index]
            self._current_index = (self._current_index + 1) % len(available)
            return key

    def mark_failed(self, key: str) -> None:
        """Mark a key as failed (will be skipped in rotation)."""
        with self._lock:
            self._failed_keys.add(key)

    def mark_recovered(self, key: str) -> None:
        """Mark a previously failed key as recovered."""
        with self._lock:
            self._failed_keys.discard(key)

    def reset(self) -> None:
        """Reset all failed keys and rotation index."""
        with self._lock:
            self._failed_keys.clear()
            self._current_index = 0

    @classmethod
    def from_env(
        cls,
        env_var: str,
        strategy: KeyRotationStrategy = KeyRotationStrategy.ROUND_ROBIN,
    ) -> "APIKeyPool":
        """
        Create key pool from environment variable.

        Supports comma-separated keys: OPENAI_API_KEY=key1,key2,key3
        """
        value = os.getenv(env_var, "")
        keys = [k.strip() for k in value.split(",") if k.strip()]
        return cls(keys, strategy)

    @classmethod
    def from_secret(
        cls,
        secret: Optional[SecretStr],
        strategy: KeyRotationStrategy = KeyRotationStrategy.ROUND_ROBIN,
    ) -> "APIKeyPool":
        """Create key pool from a SecretStr (may contain comma-separated keys)."""
        if not secret:
            return cls([], strategy)
        value = secret.get_secret_value()
        keys = [k.strip() for k in value.split(",") if k.strip()]
        return cls(keys, strategy)


class ProfileDefaults:
    """Profile-specific default configurations."""

    @staticmethod
    def get_defaults(profile: Profile) -> dict[str, Any]:
        """Get default configuration values for a profile."""
        defaults = {
            Profile.DEVELOPMENT: {
                "runtime": {
                    "log_level": "DEBUG",
                    "verbose": True,
                },
                "MAX_SEARCH_RESULTS": 3,
                "CONCURRENT_SEARCHES": 2,
            },
            Profile.STAGING: {
                "runtime": {
                    "log_level": "INFO",
                    "verbose": False,
                },
                "MAX_SEARCH_RESULTS": 5,
                "CONCURRENT_SEARCHES": 3,
            },
            Profile.PRODUCTION: {
                "runtime": {
                    "log_level": "WARNING",
                    "verbose": False,
                    "headless": True,
                },
                "MAX_SEARCH_RESULTS": 10,
                "CONCURRENT_SEARCHES": 5,
            },
        }
        return defaults.get(profile, {})
