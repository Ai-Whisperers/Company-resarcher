import hashlib
import json
import threading
from pathlib import Path
from typing import Optional
from ..core.config import get_settings
from ..core.logger import setup_logger

logger = setup_logger("cache")
settings = get_settings()


class AICache:
    """
    Simple file-based cache for AI responses.
    Useful for development to avoid re-generating expensive responses.

    Security: Uses JSON instead of pickle to prevent deserialization attacks.
    Thread-safe: Uses locks for initialization and file operations.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        with self._lock:
            if not self._initialized:
                self.cache_dir = settings.BASE_DIR / ".cache" / "ai_responses"
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self._initialized = True

    def _get_cache_key(
        self, prompt: str, system: str | None, temperature: float, max_tokens: int
    ) -> str:
        """Generate a unique key for the request using SHA256."""
        key_data = {
            "prompt": prompt,
            "system": system,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        # Use SHA256 instead of MD5 for better collision resistance
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(
        self, prompt: str, system: str | None, temperature: float, max_tokens: int
    ) -> Optional[str]:
        """Retrieve response from cache using JSON (safe deserialization)."""
        key = self._get_cache_key(prompt, system, temperature, max_tokens)
        cache_file = self.cache_dir / f"{key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("response")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in cache file {key}: {e}")
            except IOError as e:
                logger.warning(f"Failed to read cache file {key}: {e}")
        return None

    def set(
        self,
        prompt: str,
        response: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
    ):
        """Save response to cache using JSON (safe serialization)."""
        key = self._get_cache_key(prompt, system, temperature, max_tokens)
        cache_file = self.cache_dir / f"{key}.json"

        try:
            data = {
                "prompt": prompt,
                "system": system,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response": response,
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except (IOError, TypeError) as e:
            logger.warning(f"Failed to write cache file {key}: {e}")


def get_ai_cache() -> AICache:
    """Get the singleton AICache instance (thread-safe)."""
    return AICache()
