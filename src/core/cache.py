import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Optional
from ..core.config import get_settings
from ..core.logger import setup_logger

logger = setup_logger("cache")
settings = get_settings()


class AICache:
    """
    Simple file-based cache for AI responses.
    Useful for development to avoid re-generating expensive responses.
    """

    def __init__(self):
        self.cache_dir = settings.BASE_DIR / ".cache" / "ai_responses"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(
        self, prompt: str, system: str | None, temperature: float, max_tokens: int
    ) -> str:
        """Generate a unique key for the request."""
        key_data = {
            "prompt": prompt,
            "system": system,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(
        self, prompt: str, system: str | None, temperature: float, max_tokens: int
    ) -> Optional[str]:
        """Retrieve response from cache."""
        key = self._get_cache_key(prompt, system, temperature, max_tokens)
        cache_file = self.cache_dir / f"{key}.pickle"

        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    return data["response"]
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        return None

    def set(
        self,
        prompt: str,
        response: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
    ):
        """Save response to cache."""
        key = self._get_cache_key(prompt, system, temperature, max_tokens)
        cache_file = self.cache_dir / f"{key}.pickle"

        try:
            data = {
                "prompt": prompt,
                "system": system,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response": response,
            }
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")


_cache_instance = None


def get_ai_cache() -> AICache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AICache()
    return _cache_instance
