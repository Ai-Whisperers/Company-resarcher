"""
API Key Management with Rotation Support.

This module provides secure API key management with:
- Multiple keys per provider for redundancy
- Round-robin and failover rotation strategies
- Automatic key exhaustion detection
- Key health tracking

Usage:
    from src.core.managers.key_manager import KeyManager, get_key_manager

    manager = get_key_manager()
    key = manager.get_key("openai")  # Gets next available key
    manager.mark_exhausted("openai", key)  # Mark key as exhausted
"""

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from threading import Lock
from typing import Optional, List, Dict
from pydantic import SecretStr

from src.core.logging import get_logger

logger = get_logger(__name__)


class RotationStrategy(str, Enum):
    """Key rotation strategies."""
    ROUND_ROBIN = "round_robin"  # Cycle through keys evenly
    FAILOVER = "failover"  # Use primary until exhausted, then switch
    RANDOM = "random"  # Random selection


@dataclass
class KeyHealth:
    """Track health status of an API key."""
    key_hash: str  # Hash of key for identification (not the key itself)
    is_exhausted: bool = False
    exhausted_at: Optional[float] = None
    error_count: int = 0
    last_used: Optional[float] = None
    request_count: int = 0

    def mark_exhausted(self):
        """Mark key as exhausted."""
        self.is_exhausted = True
        self.exhausted_at = time.time()

    def reset(self):
        """Reset key health (e.g., after cooldown)."""
        self.is_exhausted = False
        self.exhausted_at = None
        self.error_count = 0

    def is_available(self, cooldown_seconds: int = 3600) -> bool:
        """Check if key is available for use."""
        if not self.is_exhausted:
            return True
        # Check if cooldown period has passed
        if self.exhausted_at and (time.time() - self.exhausted_at) > cooldown_seconds:
            self.reset()
            return True
        return False


@dataclass
class ProviderKeys:
    """Manage keys for a single provider."""
    provider: str
    keys: List[SecretStr] = field(default_factory=list)
    health: Dict[str, KeyHealth] = field(default_factory=dict)
    current_index: int = 0
    strategy: RotationStrategy = RotationStrategy.ROUND_ROBIN
    lock: Lock = field(default_factory=Lock)

    def _key_hash(self, key: SecretStr) -> str:
        """Get hash of key for tracking (without exposing the key)."""
        value = key.get_secret_value()
        # Use last 8 chars as identifier
        return f"{self.provider}_{value[-8:]}" if len(value) > 8 else f"{self.provider}_{hash(value)}"

    def add_key(self, key: SecretStr):
        """Add a key to the pool."""
        if key and key.get_secret_value():
            self.keys.append(key)
            key_hash = self._key_hash(key)
            self.health[key_hash] = KeyHealth(key_hash=key_hash)

    def get_next_key(self, cooldown_seconds: int = 3600) -> Optional[SecretStr]:
        """Get next available key based on rotation strategy."""
        with self.lock:
            if not self.keys:
                return None

            available_keys = [
                (i, k) for i, k in enumerate(self.keys)
                if self.health.get(self._key_hash(k), KeyHealth(key_hash="")).is_available(cooldown_seconds)
            ]

            if not available_keys:
                logger.warning(f"All keys for {self.provider} are exhausted")
                return None

            if self.strategy == RotationStrategy.ROUND_ROBIN:
                # Find next available key from current position
                for _ in range(len(self.keys)):
                    idx = self.current_index % len(self.keys)
                    key = self.keys[idx]
                    key_hash = self._key_hash(key)
                    self.current_index = (self.current_index + 1) % len(self.keys)

                    if self.health.get(key_hash, KeyHealth(key_hash="")).is_available(cooldown_seconds):
                        health = self.health[key_hash]
                        health.last_used = time.time()
                        health.request_count += 1
                        return key
                return None

            elif self.strategy == RotationStrategy.FAILOVER:
                # Use first available key
                for idx, key in available_keys:
                    key_hash = self._key_hash(key)
                    health = self.health[key_hash]
                    health.last_used = time.time()
                    health.request_count += 1
                    return key
                return None

            else:  # RANDOM
                import random
                idx, key = random.choice(available_keys)
                key_hash = self._key_hash(key)
                health = self.health[key_hash]
                health.last_used = time.time()
                health.request_count += 1
                return key

    def mark_exhausted(self, key: SecretStr):
        """Mark a key as exhausted."""
        key_hash = self._key_hash(key)
        if key_hash in self.health:
            self.health[key_hash].mark_exhausted()
            logger.warning(f"Key {key_hash} marked as exhausted")

    def mark_error(self, key: SecretStr):
        """Record an error for a key."""
        key_hash = self._key_hash(key)
        if key_hash in self.health:
            self.health[key_hash].error_count += 1
            # Auto-exhaust after too many errors
            if self.health[key_hash].error_count >= 5:
                self.mark_exhausted(key)

    def get_status(self) -> Dict:
        """Get status of all keys."""
        return {
            "provider": self.provider,
            "total_keys": len(self.keys),
            "available_keys": sum(1 for k in self.keys if self.health.get(self._key_hash(k), KeyHealth(key_hash="")).is_available()),
            "strategy": self.strategy.value,
            "keys": [
                {
                    "id": h.key_hash,
                    "is_exhausted": h.is_exhausted,
                    "error_count": h.error_count,
                    "request_count": h.request_count,
                }
                for h in self.health.values()
            ]
        }


class KeyManager:
    """
    Centralized API key management with rotation support.

    Supports multiple keys per provider with automatic rotation
    when keys are exhausted or experience errors.
    """

    def __init__(
        self,
        strategy: RotationStrategy = RotationStrategy.ROUND_ROBIN,
        cooldown_seconds: int = 3600
    ):
        self.strategy = strategy
        self.cooldown_seconds = cooldown_seconds
        self.providers: Dict[str, ProviderKeys] = {}
        self._lock = Lock()

        # Initialize from environment
        self._load_from_environment()

    def _load_from_environment(self):
        """Load API keys from environment variables."""
        # Define provider key patterns
        # Format: PROVIDER_API_KEY, PROVIDER_API_KEY_2, PROVIDER_API_KEY_3, etc.
        providers = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "groq": "GROQ_API_KEY",
            "tavily": "TAVILY_API_KEY",
            "serper": "SERPER_API_KEY",
            "serpapi": "SERPAPI_API_KEY",
            "newsapi": "NEWSAPI_KEY",
            "jina": "JINA_API_KEY",
            "langsearch": "LANGSEARCH_API_KEY",
        }

        for provider, base_env_var in providers.items():
            provider_keys = ProviderKeys(provider=provider, strategy=self.strategy)

            # Load primary key
            primary_key = os.getenv(base_env_var)
            if primary_key:
                provider_keys.add_key(SecretStr(primary_key))

            # Load additional keys (KEY_2, KEY_3, etc.)
            for i in range(2, 11):  # Support up to 10 keys per provider
                key = os.getenv(f"{base_env_var}_{i}")
                if key:
                    provider_keys.add_key(SecretStr(key))

            if provider_keys.keys:
                self.providers[provider] = provider_keys
                logger.debug(f"Loaded {len(provider_keys.keys)} key(s) for {provider}")

    def get_key(self, provider: str) -> Optional[str]:
        """
        Get next available API key for a provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")

        Returns:
            API key string or None if no keys available
        """
        provider = provider.lower()
        if provider not in self.providers:
            # Fallback to direct environment variable
            env_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "gemini": "GEMINI_API_KEY",
                "groq": "GROQ_API_KEY",
                "tavily": "TAVILY_API_KEY",
            }
            env_var = env_map.get(provider)
            if env_var:
                return os.getenv(env_var)
            return None

        key = self.providers[provider].get_next_key(self.cooldown_seconds)
        return key.get_secret_value() if key else None

    def mark_exhausted(self, provider: str, key: str):
        """Mark a key as exhausted (rate limited, quota exceeded)."""
        provider = provider.lower()
        if provider in self.providers:
            # Find the key and mark it
            for k in self.providers[provider].keys:
                if k.get_secret_value() == key:
                    self.providers[provider].mark_exhausted(k)
                    break

    def mark_error(self, provider: str, key: str):
        """Record an error for a key."""
        provider = provider.lower()
        if provider in self.providers:
            for k in self.providers[provider].keys:
                if k.get_secret_value() == key:
                    self.providers[provider].mark_error(k)
                    break

    def has_available_key(self, provider: str) -> bool:
        """Check if provider has any available keys."""
        provider = provider.lower()
        if provider not in self.providers:
            # Check direct environment variable
            return bool(self.get_key(provider))
        return self.providers[provider].get_next_key(self.cooldown_seconds) is not None

    def get_status(self) -> Dict:
        """Get status of all providers and keys."""
        return {
            "strategy": self.strategy.value,
            "cooldown_seconds": self.cooldown_seconds,
            "providers": {
                name: prov.get_status()
                for name, prov in self.providers.items()
            }
        }

    def set_strategy(self, strategy: RotationStrategy):
        """Change rotation strategy for all providers."""
        self.strategy = strategy
        for provider in self.providers.values():
            provider.strategy = strategy


@lru_cache()
def get_key_manager() -> KeyManager:
    """Get cached KeyManager instance."""
    strategy_env = os.getenv("KEY_ROTATION_STRATEGY", "round_robin").lower()
    strategy = RotationStrategy(strategy_env) if strategy_env in [s.value for s in RotationStrategy] else RotationStrategy.ROUND_ROBIN

    cooldown = int(os.getenv("KEY_EXHAUSTION_COOLDOWN_SECONDS", "3600"))

    return KeyManager(strategy=strategy, cooldown_seconds=cooldown)


def clear_key_manager():
    """Clear cached KeyManager (useful for testing)."""
    get_key_manager.cache_clear()


__all__ = [
    "KeyManager",
    "KeyHealth",
    "ProviderKeys",
    "RotationStrategy",
    "get_key_manager",
    "clear_key_manager",
]
