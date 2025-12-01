"""
Semantic Caching Layer for AI Responses.

Provides intelligent caching that can match semantically similar prompts,
reducing redundant API calls and saving costs.

Features:
- Text normalization for fuzzy matching
- Configurable similarity threshold
- TTL-based expiration
- Exact match fallback for high-temperature prompts
- Cache statistics and cost savings tracking

Example:
    cache = SemanticCache()

    # Try to get cached response
    hit = await cache.get_semantic("What is the market size for AI?")
    if hit:
        response = hit.response

    # Store new response
    await cache.set("What is the market size for AI?", response)
"""

import asyncio
import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..core.config import get_settings
from ..core.logger import setup_logger

logger = setup_logger("semantic_cache")
settings = get_settings()

# Configuration
DEFAULT_TTL_SECONDS = int(os.getenv("SEMANTIC_CACHE_TTL_SECONDS", "86400"))  # 24 hours
SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.85"))
MAX_CACHE_SIZE_MB = int(os.getenv("SEMANTIC_CACHE_MAX_SIZE_MB", "100"))

# Common stop words to remove for similarity matching
STOP_WORDS = frozenset([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "and", "but", "if", "or", "because", "until",
    "while", "about", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "it", "its", "i", "you", "he", "she", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "our",
    "their", "please", "help", "want", "need", "like", "get", "give",
])


@dataclass
class CacheEntry:
    """A cached response with metadata."""

    prompt_hash: str
    prompt_normalized: str
    prompt_tokens: frozenset
    response: str
    system: Optional[str]
    temperature: float
    max_tokens: int
    created_at: float
    ttl_seconds: int
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.created_at + self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "prompt_hash": self.prompt_hash,
            "prompt_normalized": self.prompt_normalized,
            "prompt_tokens": list(self.prompt_tokens),
            "response": self.response,
            "system": self.system,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "hit_count": self.hit_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            prompt_hash=data["prompt_hash"],
            prompt_normalized=data["prompt_normalized"],
            prompt_tokens=frozenset(data["prompt_tokens"]),
            response=data["response"],
            system=data.get("system"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
            created_at=data["created_at"],
            ttl_seconds=data.get("ttl_seconds", DEFAULT_TTL_SECONDS),
            hit_count=data.get("hit_count", 0),
        )


@dataclass
class CacheHit:
    """Result of a cache lookup."""

    response: str
    similarity: float
    is_exact_match: bool
    entry: CacheEntry


@dataclass
class CacheStats:
    """Cache statistics."""

    total_requests: int = 0
    exact_hits: int = 0
    semantic_hits: int = 0
    misses: int = 0
    entries_count: int = 0
    cache_size_bytes: int = 0
    estimated_cost_savings: float = 0.0  # Estimated $ saved

    @property
    def hit_rate(self) -> float:
        """Total hit rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return ((self.exact_hits + self.semantic_hits) / self.total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "exact_hits": self.exact_hits,
            "semantic_hits": self.semantic_hits,
            "misses": self.misses,
            "hit_rate_percent": round(self.hit_rate, 2),
            "entries_count": self.entries_count,
            "cache_size_mb": round(self.cache_size_bytes / 1024 / 1024, 2),
            "estimated_cost_savings_usd": round(self.estimated_cost_savings, 4),
        }


class SemanticCache:
    """
    Semantic caching for AI responses.

    Matches prompts using text similarity, not just exact hash matching.
    This catches variations in phrasing that would produce the same response.

    Features:
    - Normalizes text (lowercase, removes punctuation/stopwords)
    - Uses Jaccard similarity on token sets
    - Falls back to exact matching for high-temperature prompts
    - Configurable similarity threshold
    - TTL-based expiration

    Example:
        cache = SemanticCache()

        # These prompts would match semantically:
        # "What is the market size for AI in healthcare?"
        # "What's the AI healthcare market size?"
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        default_ttl: int = DEFAULT_TTL_SECONDS,
    ):
        self.cache_dir = cache_dir or (settings.BASE_DIR / ".cache" / "semantic")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = similarity_threshold
        self.default_ttl = default_ttl

        self._lock = threading.Lock()
        self._stats = CacheStats()

        # In-memory index of entries for fast similarity matching
        self._entries: Dict[str, CacheEntry] = {}

        # Load existing cache on init
        self._load_cache()

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for similarity matching.

        - Lowercase
        - Remove punctuation
        - Remove extra whitespace
        """
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text

    def _tokenize(self, text: str) -> frozenset:
        """
        Tokenize text into a set of words (minus stop words).

        Returns frozenset for efficient hashing and comparison.
        """
        normalized = self._normalize_text(text)
        words = normalized.split()
        # Remove stop words
        tokens = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        return frozenset(tokens)

    def _compute_similarity(self, tokens1: frozenset, tokens2: frozenset) -> float:
        """
        Compute Jaccard similarity between two token sets.

        Returns value between 0.0 and 1.0.
        """
        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def _get_hash(self, prompt: str, system: Optional[str] = None) -> str:
        """Get SHA256 hash for exact matching."""
        key_data = f"{prompt}|{system or ''}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _load_cache(self) -> None:
        """Load cache entries from disk."""
        index_file = self.cache_dir / "index.json"
        if not index_file.exists():
            return

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for entry_data in data.get("entries", []):
                try:
                    entry = CacheEntry.from_dict(entry_data)
                    if not entry.is_expired():
                        self._entries[entry.prompt_hash] = entry
                except (KeyError, TypeError) as e:
                    logger.warning(f"Skipping invalid cache entry: {e}")

            self._stats.entries_count = len(self._entries)
            logger.info(f"Loaded {len(self._entries)} semantic cache entries")

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load semantic cache: {e}")

    def _save_cache(self) -> None:
        """Save cache entries to disk."""
        index_file = self.cache_dir / "index.json"

        try:
            # Remove expired entries
            valid_entries = {
                h: e for h, e in self._entries.items() if not e.is_expired()
            }
            self._entries = valid_entries

            data = {
                "entries": [e.to_dict() for e in self._entries.values()],
                "stats": self._stats.to_dict(),
                "saved_at": time.time(),
            }

            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            self._stats.entries_count = len(self._entries)

        except (IOError, TypeError) as e:
            logger.error(f"Failed to save semantic cache: {e}")

    def get(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Optional[CacheHit]:
        """
        Get cached response for a prompt.

        First tries exact match, then semantic match if temperature is low.

        Args:
            prompt: The prompt to look up
            system: Optional system prompt
            temperature: LLM temperature (high temp skips semantic matching)
            max_tokens: Max tokens (must match for cache hit)

        Returns:
            CacheHit if found, None otherwise
        """
        with self._lock:
            self._stats.total_requests += 1

            prompt_hash = self._get_hash(prompt, system)

            # Try exact match first
            if prompt_hash in self._entries:
                entry = self._entries[prompt_hash]
                if not entry.is_expired():
                    entry.hit_count += 1
                    self._stats.exact_hits += 1
                    self._estimate_savings()
                    return CacheHit(
                        response=entry.response,
                        similarity=1.0,
                        is_exact_match=True,
                        entry=entry,
                    )

            # Skip semantic matching for high-temperature prompts
            # (they're meant to be creative/varied)
            if temperature > 0.5:
                self._stats.misses += 1
                return None

            # Try semantic matching
            prompt_tokens = self._tokenize(prompt)
            best_match: Optional[CacheEntry] = None
            best_similarity = 0.0

            for entry in self._entries.values():
                if entry.is_expired():
                    continue

                # Skip if max_tokens is significantly different
                if abs(entry.max_tokens - max_tokens) > 1000:
                    continue

                similarity = self._compute_similarity(prompt_tokens, entry.prompt_tokens)

                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = entry

            if best_match:
                best_match.hit_count += 1
                self._stats.semantic_hits += 1
                self._estimate_savings()
                logger.debug(f"Semantic cache hit (similarity={best_similarity:.2f})")
                return CacheHit(
                    response=best_match.response,
                    similarity=best_similarity,
                    is_exact_match=False,
                    entry=best_match,
                )

            self._stats.misses += 1
            return None

    def set(
        self,
        prompt: str,
        response: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Store a response in the cache.

        Args:
            prompt: The prompt
            response: The AI response
            system: Optional system prompt
            temperature: LLM temperature
            max_tokens: Max tokens used
            ttl_seconds: Time to live (uses default if not specified)
        """
        with self._lock:
            prompt_hash = self._get_hash(prompt, system)

            entry = CacheEntry(
                prompt_hash=prompt_hash,
                prompt_normalized=self._normalize_text(prompt),
                prompt_tokens=self._tokenize(prompt),
                response=response,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                created_at=time.time(),
                ttl_seconds=ttl_seconds or self.default_ttl,
            )

            self._entries[prompt_hash] = entry
            self._stats.entries_count = len(self._entries)

            # Persist to disk (could be made async/batched for performance)
            self._save_cache()

    def _estimate_savings(self) -> None:
        """Estimate cost savings from cache hits."""
        # Assume average cost of $0.01 per request (mix of models)
        cost_per_request = 0.01
        total_hits = self._stats.exact_hits + self._stats.semantic_hits
        self._stats.estimated_cost_savings = total_hits * cost_per_request

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            # Update size
            try:
                total_size = sum(
                    f.stat().st_size for f in self.cache_dir.iterdir() if f.is_file()
                )
                self._stats.cache_size_bytes = total_size
            except OSError:
                pass
            return self._stats

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._entries.clear()
            self._stats = CacheStats()
            # Remove files
            for f in self.cache_dir.iterdir():
                if f.is_file():
                    f.unlink()
            logger.info("Semantic cache cleared")

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        with self._lock:
            before_count = len(self._entries)
            self._entries = {
                h: e for h, e in self._entries.items() if not e.is_expired()
            }
            removed = before_count - len(self._entries)
            if removed > 0:
                self._save_cache()
                logger.info(f"Cleaned up {removed} expired cache entries")
            return removed


# Singleton instance
_semantic_cache: Optional[SemanticCache] = None
_cache_lock = threading.Lock()


def get_semantic_cache() -> SemanticCache:
    """Get the singleton SemanticCache instance (thread-safe)."""
    global _semantic_cache
    if _semantic_cache is None:
        with _cache_lock:
            if _semantic_cache is None:
                _semantic_cache = SemanticCache()
    return _semantic_cache


__all__ = [
    "SemanticCache",
    "CacheEntry",
    "CacheHit",
    "CacheStats",
    "get_semantic_cache",
]
