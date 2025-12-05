"""
File-based Cache Implementation.

Uses JSON files for persistence. Safe, simple, and works without external dependencies.
"""

import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .base import BaseCache, CacheEntry

logger = logging.getLogger(__name__)


class FileCache(BaseCache):
    """
    File-based JSON cache implementation.

    Features:
    - JSON serialization (safe, no pickle vulnerabilities)
    - Thread-safe operations
    - Automatic expiration checking
    - Directory-based key organization

    Usage:
        cache = FileCache(Path(".cache/my_cache"))
        cache.set("key", {"data": "value"}, ttl=3600)
        data = cache.get("key")
    """

    def __init__(
        self,
        cache_dir: Path,
        default_ttl: Optional[int] = None,
    ):
        """
        Initialize file cache.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default TTL in seconds (None = no expiry)
        """
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a cache key."""
        # Hash the key for safe filenames
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{key_hash}.json"

    def _read_entry(self, file_path: Path) -> Optional[CacheEntry]:
        """Read and parse a cache entry from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entry = CacheEntry(
                value=data.get("value"),
                created_at=data.get("created_at", time.time()),
                expires_at=data.get("expires_at"),
                hits=data.get("hits", 0),
                metadata=data.get("metadata", {}),
            )

            # Check expiration
            if entry.is_expired:
                file_path.unlink(missing_ok=True)
                return None

            return entry

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read cache file: {e}")
            return None

    def _write_entry(self, file_path: Path, entry: CacheEntry) -> bool:
        """Write a cache entry to file."""
        try:
            data = {
                "value": entry.value,
                "created_at": entry.created_at,
                "expires_at": entry.expires_at,
                "hits": entry.hits,
                "metadata": entry.metadata,
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, TypeError) as e:
            logger.warning(f"Failed to write cache file: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        with self._lock:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                self._misses += 1
                return None

            entry = self._read_entry(file_path)
            if entry is None:
                self._misses += 1
                return None

            # Update hit count
            entry.hits += 1
            self._write_entry(file_path, entry)
            self._hits += 1

            return entry.value

    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry with metadata."""
        with self._lock:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                self._misses += 1
                return None

            entry = self._read_entry(file_path)
            if entry is None:
                self._misses += 1
                return None

            self._hits += 1
            return entry

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set a value in the cache."""
        with self._lock:
            file_path = self._get_file_path(key)

            # Calculate expiration
            effective_ttl = ttl if ttl is not None else self._default_ttl
            expires_at = None
            if effective_ttl is not None:
                expires_at = time.time() + effective_ttl

            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
                hits=0,
                metadata=metadata or {},
            )

            return self._write_entry(file_path, entry)

    def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        with self._lock:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            file_path = self._get_file_path(key)
            if not file_path.exists():
                return False

            entry = self._read_entry(file_path)
            return entry is not None

    def clear(self) -> int:
        """Clear all entries from the cache."""
        with self._lock:
            count = 0
            for file_path in self._cache_dir.glob("*.json"):
                try:
                    file_path.unlink()
                    count += 1
                except IOError:
                    pass
            self._hits = 0
            self._misses = 0
            return count

    def cleanup_expired(self) -> int:
        """Remove expired entries from the cache."""
        with self._lock:
            count = 0
            for file_path in self._cache_dir.glob("*.json"):
                entry = self._read_entry(file_path)
                if entry is None:  # Already deleted if expired
                    count += 1
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            file_count = len(list(self._cache_dir.glob("*.json")))
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            return {
                "backend": "file",
                "cache_dir": str(self._cache_dir),
                "entries": file_count,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "default_ttl": self._default_ttl,
            }

    def __repr__(self) -> str:
        return f"<FileCache dir={self._cache_dir}>"
