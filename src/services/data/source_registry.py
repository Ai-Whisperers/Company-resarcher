"""
Persistent Source Registry - Tracks fetched URLs across multiple research runs.

This service maintains a SQLite database per company that stores:
- All previously fetched URLs
- Content hashes for duplicate detection
- Data types extracted from each source
- Fetch dates and usefulness scores

This enables incremental research by:
1. Skipping already-fetched URLs
2. Detecting semantically similar content
3. Tracking which sources provided useful data
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from ...core.logging import setup_logger

logger = setup_logger("persistent_source_registry")


@dataclass
class SourceRecord:
    """A record of a previously fetched source."""
    url: str
    url_normalized: str
    content_hash: str
    title: str
    fetch_date: datetime
    data_types_found: Set[str] = field(default_factory=set)
    sections_used: Set[str] = field(default_factory=set)
    usefulness_score: float = 0.5  # 0.0 = useless, 1.0 = very useful
    content_length: int = 0
    is_stale: bool = False  # True if data is outdated

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "url": self.url,
            "url_normalized": self.url_normalized,
            "content_hash": self.content_hash,
            "title": self.title,
            "fetch_date": self.fetch_date.isoformat(),
            "data_types_found": list(self.data_types_found),
            "sections_used": list(self.sections_used),
            "usefulness_score": self.usefulness_score,
            "content_length": self.content_length,
            "is_stale": self.is_stale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceRecord":
        """Create from dictionary."""
        return cls(
            url=data["url"],
            url_normalized=data["url_normalized"],
            content_hash=data["content_hash"],
            title=data["title"],
            fetch_date=datetime.fromisoformat(data["fetch_date"]),
            data_types_found=set(data.get("data_types_found", [])),
            sections_used=set(data.get("sections_used", [])),
            usefulness_score=data.get("usefulness_score", 0.5),
            content_length=data.get("content_length", 0),
            is_stale=data.get("is_stale", False),
        )


@dataclass
class ContentFingerprint:
    """Fingerprint for detecting similar content."""
    hash_full: str  # Full content hash
    hash_normalized: str  # Hash of normalized content (lowercase, no whitespace)
    simhash: int  # Locality-sensitive hash for similarity detection
    key_phrases: Set[str]  # Important phrases for matching
    word_count: int


class PersistentSourceRegistry:
    """
    Persistent registry of fetched sources for a company.

    Stored in: outputs/{Company}/.meta/source_registry.db

    Usage:
        registry = PersistentSourceRegistry("outputs", "Claro Paraguay")

        # Check if URL was already fetched
        if registry.is_url_seen(url):
            skip_fetch()

        # Check for similar content
        if registry.has_similar_content(content):
            skip_processing()

        # Record new source
        registry.add_source(url, content, title, data_types)
    """

    # Content older than this is considered stale and worth re-fetching
    STALE_THRESHOLD_DAYS = 90

    # Similarity threshold for content deduplication (0.0 - 1.0)
    SIMILARITY_THRESHOLD = 0.85

    def __init__(self, base_dir: str, company_name: str):
        """
        Initialize registry for a company.

        Args:
            base_dir: Base output directory (e.g., "outputs")
            company_name: Company name for folder
        """
        self.base_dir = Path(base_dir).resolve()
        self.company_name = company_name
        self.safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)

        # Create .meta directory
        self.meta_dir = self.base_dir / self.safe_name / ".meta"
        self.meta_dir.mkdir(parents=True, exist_ok=True)

        # Database path
        self.db_path = self.meta_dir / "source_registry.db"

        # Initialize database
        self._init_db()

        # In-memory caches for fast lookups
        self._url_cache: Set[str] = set()
        self._hash_cache: Set[str] = set()
        self._load_caches()

        logger.info(f"Source registry initialized for {company_name} ({len(self._url_cache)} URLs cached)")

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    url_normalized TEXT NOT NULL UNIQUE,
                    content_hash TEXT NOT NULL,
                    content_hash_normalized TEXT,
                    title TEXT,
                    fetch_date TEXT NOT NULL,
                    data_types_found TEXT,
                    sections_used TEXT,
                    usefulness_score REAL DEFAULT 0.5,
                    content_length INTEGER DEFAULT 0,
                    is_stale INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_url_normalized ON sources(url_normalized);
                CREATE INDEX IF NOT EXISTS idx_content_hash ON sources(content_hash);
                CREATE INDEX IF NOT EXISTS idx_fetch_date ON sources(fetch_date);

                CREATE TABLE IF NOT EXISTS content_fingerprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    simhash INTEGER,
                    key_phrases TEXT,
                    word_count INTEGER,
                    FOREIGN KEY (source_id) REFERENCES sources(id)
                );

                CREATE INDEX IF NOT EXISTS idx_simhash ON content_fingerprints(simhash);

                CREATE TABLE IF NOT EXISTS registry_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def _load_caches(self) -> None:
        """Load URL and hash caches from database."""
        with sqlite3.connect(self.db_path) as conn:
            # Load normalized URLs
            cursor = conn.execute("SELECT url_normalized FROM sources")
            self._url_cache = {row[0] for row in cursor.fetchall()}

            # Load content hashes
            cursor = conn.execute("SELECT content_hash FROM sources")
            self._hash_cache = {row[0] for row in cursor.fetchall()}

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize URL for consistent matching.

        - Lowercase
        - Remove www. prefix
        - Remove trailing slashes
        - Remove common tracking parameters
        """
        try:
            parsed = urlparse(url.lower().strip())

            # Remove www. prefix
            netloc = parsed.netloc
            if netloc.startswith("www."):
                netloc = netloc[4:]

            # Remove trailing slash from path
            path = parsed.path.rstrip("/")

            # Remove common tracking parameters
            query = parsed.query
            if query:
                # Remove utm_*, fbclid, gclid, etc.
                params = query.split("&")
                filtered = [
                    p for p in params
                    if not any(p.startswith(prefix) for prefix in [
                        "utm_", "fbclid", "gclid", "ref=", "source=", "campaign="
                    ])
                ]
                query = "&".join(filtered)

            # Reconstruct URL
            normalized = f"{parsed.scheme}://{netloc}{path}"
            if query:
                normalized += f"?{query}"

            return normalized

        except Exception:
            return url.lower().strip()

    @staticmethod
    def hash_content(content: str) -> str:
        """Generate hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def hash_content_normalized(content: str) -> str:
        """Generate hash of normalized content (for fuzzy matching)."""
        # Normalize: lowercase, remove extra whitespace, remove punctuation
        normalized = re.sub(r'\s+', ' ', content.lower())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def compute_simhash(content: str, hash_bits: int = 64) -> int:
        """
        Compute SimHash for locality-sensitive hashing.

        Similar documents will have similar SimHash values,
        enabling fast similarity detection.
        """
        # Tokenize into words
        words = re.findall(r'\w+', content.lower())

        # Initialize bit counts
        bit_counts = [0] * hash_bits

        for word in words:
            # Hash each word
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)

            # Update bit counts
            for i in range(hash_bits):
                if (word_hash >> i) & 1:
                    bit_counts[i] += 1
                else:
                    bit_counts[i] -= 1

        # Convert to final hash
        simhash = 0
        for i in range(hash_bits):
            if bit_counts[i] > 0:
                simhash |= (1 << i)

        return simhash

    @staticmethod
    def simhash_similarity(hash1: int, hash2: int, hash_bits: int = 64) -> float:
        """
        Calculate similarity between two SimHash values.

        Returns value between 0.0 (different) and 1.0 (identical).
        """
        # Count differing bits (Hamming distance)
        xor = hash1 ^ hash2
        diff_bits = bin(xor).count('1')

        # Convert to similarity
        return 1.0 - (diff_bits / hash_bits)

    def is_url_seen(self, url: str) -> bool:
        """Check if URL has been fetched before."""
        normalized = self.normalize_url(url)
        return normalized in self._url_cache

    def is_content_seen(self, content: str) -> bool:
        """Check if exact content has been seen before."""
        content_hash = self.hash_content(content)
        return content_hash in self._hash_cache

    def has_similar_content(
        self,
        content: str,
        threshold: float = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if similar content exists in registry.

        Args:
            content: Content to check
            threshold: Similarity threshold (default: SIMILARITY_THRESHOLD)

        Returns:
            Tuple of (is_similar, similar_url_if_found)
        """
        if threshold is None:
            threshold = self.SIMILARITY_THRESHOLD

        # Quick exact match check
        content_hash = self.hash_content(content)
        if content_hash in self._hash_cache:
            return True, self._get_url_by_hash(content_hash)

        # Compute SimHash for similarity check
        new_simhash = self.compute_simhash(content)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT cf.simhash, s.url
                FROM content_fingerprints cf
                JOIN sources s ON cf.source_id = s.id
            """)

            for row in cursor.fetchall():
                existing_simhash, existing_url = row
                if existing_simhash is not None:
                    similarity = self.simhash_similarity(new_simhash, existing_simhash)
                    if similarity >= threshold:
                        logger.debug(
                            f"Found similar content ({similarity:.2%}): {existing_url[:50]}..."
                        )
                        return True, existing_url

        return False, None

    def _get_url_by_hash(self, content_hash: str) -> Optional[str]:
        """Get URL for a content hash."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT url FROM sources WHERE content_hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def get_source_record(self, url: str) -> Optional[SourceRecord]:
        """Get full source record for a URL."""
        normalized = self.normalize_url(url)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, url_normalized, content_hash, title, fetch_date,
                       data_types_found, sections_used, usefulness_score,
                       content_length, is_stale
                FROM sources WHERE url_normalized = ?
            """, (normalized,))

            row = cursor.fetchone()
            if not row:
                return None

            return SourceRecord(
                url=row[0],
                url_normalized=row[1],
                content_hash=row[2],
                title=row[3] or "",
                fetch_date=datetime.fromisoformat(row[4]),
                data_types_found=set(json.loads(row[5] or "[]")),
                sections_used=set(json.loads(row[6] or "[]")),
                usefulness_score=row[7] or 0.5,
                content_length=row[8] or 0,
                is_stale=bool(row[9]),
            )

    def add_source(
        self,
        url: str,
        content: str,
        title: str = "",
        data_types_found: Optional[Set[str]] = None,
        sections_used: Optional[Set[str]] = None,
        usefulness_score: float = 0.5,
    ) -> SourceRecord:
        """
        Add a new source to the registry.

        Args:
            url: Source URL
            content: Fetched content
            title: Page title
            data_types_found: Types of data extracted (e.g., "revenue", "market_share")
            sections_used: Output sections this source contributed to
            usefulness_score: How useful this source was (0.0 - 1.0)

        Returns:
            The created SourceRecord
        """
        normalized_url = self.normalize_url(url)
        content_hash = self.hash_content(content)
        content_hash_normalized = self.hash_content_normalized(content)
        simhash = self.compute_simhash(content)

        # Extract key phrases (top words by frequency)
        words = re.findall(r'\w{4,}', content.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:20]
        key_phrases = {w[0] for w in top_words}

        data_types = data_types_found or set()
        sections = sections_used or set()
        fetch_date = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            # Insert or update source
            cursor = conn.execute("""
                INSERT INTO sources (
                    url, url_normalized, content_hash, content_hash_normalized,
                    title, fetch_date, data_types_found, sections_used,
                    usefulness_score, content_length, is_stale, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                ON CONFLICT(url_normalized) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    content_hash_normalized = excluded.content_hash_normalized,
                    title = excluded.title,
                    fetch_date = excluded.fetch_date,
                    data_types_found = excluded.data_types_found,
                    sections_used = excluded.sections_used,
                    usefulness_score = excluded.usefulness_score,
                    content_length = excluded.content_length,
                    is_stale = 0,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                url, normalized_url, content_hash, content_hash_normalized,
                title, fetch_date.isoformat(),
                json.dumps(list(data_types)), json.dumps(list(sections)),
                usefulness_score, len(content),
            ))

            source_id = cursor.lastrowid

            # Insert fingerprint
            conn.execute("""
                INSERT OR REPLACE INTO content_fingerprints (
                    source_id, simhash, key_phrases, word_count
                ) VALUES (?, ?, ?, ?)
            """, (source_id, simhash, json.dumps(list(key_phrases)), len(words)))

        # Update caches
        self._url_cache.add(normalized_url)
        self._hash_cache.add(content_hash)

        logger.debug(f"Added source to registry: {url[:60]}...")

        return SourceRecord(
            url=url,
            url_normalized=normalized_url,
            content_hash=content_hash,
            title=title,
            fetch_date=fetch_date,
            data_types_found=data_types,
            sections_used=sections,
            usefulness_score=usefulness_score,
            content_length=len(content),
            is_stale=False,
        )

    def update_usefulness(self, url: str, score: float) -> None:
        """Update usefulness score for a source."""
        normalized = self.normalize_url(url)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sources SET usefulness_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE url_normalized = ?
            """, (score, normalized))

    def mark_stale(self, url: str) -> None:
        """Mark a source as stale (needs re-fetching)."""
        normalized = self.normalize_url(url)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sources SET is_stale = 1, updated_at = CURRENT_TIMESTAMP
                WHERE url_normalized = ?
            """, (normalized,))

    def get_stale_sources(self) -> List[SourceRecord]:
        """Get all sources marked as stale or older than threshold."""
        threshold_date = datetime.now() - timedelta(days=self.STALE_THRESHOLD_DAYS)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, url_normalized, content_hash, title, fetch_date,
                       data_types_found, sections_used, usefulness_score,
                       content_length, is_stale
                FROM sources
                WHERE is_stale = 1 OR fetch_date < ?
            """, (threshold_date.isoformat(),))

            records = []
            for row in cursor.fetchall():
                records.append(SourceRecord(
                    url=row[0],
                    url_normalized=row[1],
                    content_hash=row[2],
                    title=row[3] or "",
                    fetch_date=datetime.fromisoformat(row[4]),
                    data_types_found=set(json.loads(row[5] or "[]")),
                    sections_used=set(json.loads(row[6] or "[]")),
                    usefulness_score=row[7] or 0.5,
                    content_length=row[8] or 0,
                    is_stale=True,
                ))

            return records

    def get_high_value_sources(self, min_score: float = 0.7) -> List[SourceRecord]:
        """Get sources with high usefulness scores."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, url_normalized, content_hash, title, fetch_date,
                       data_types_found, sections_used, usefulness_score,
                       content_length, is_stale
                FROM sources
                WHERE usefulness_score >= ?
                ORDER BY usefulness_score DESC
            """, (min_score,))

            records = []
            for row in cursor.fetchall():
                records.append(SourceRecord(
                    url=row[0],
                    url_normalized=row[1],
                    content_hash=row[2],
                    title=row[3] or "",
                    fetch_date=datetime.fromisoformat(row[4]),
                    data_types_found=set(json.loads(row[5] or "[]")),
                    sections_used=set(json.loads(row[6] or "[]")),
                    usefulness_score=row[7] or 0.5,
                    content_length=row[8] or 0,
                    is_stale=bool(row[9]),
                ))

            return records

    def get_sources_for_data_type(self, data_type: str) -> List[SourceRecord]:
        """Get all sources that provided a specific data type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, url_normalized, content_hash, title, fetch_date,
                       data_types_found, sections_used, usefulness_score,
                       content_length, is_stale
                FROM sources
                WHERE data_types_found LIKE ?
            """, (f'%"{data_type}"%',))

            records = []
            for row in cursor.fetchall():
                records.append(SourceRecord(
                    url=row[0],
                    url_normalized=row[1],
                    content_hash=row[2],
                    title=row[3] or "",
                    fetch_date=datetime.fromisoformat(row[4]),
                    data_types_found=set(json.loads(row[5] or "[]")),
                    sections_used=set(json.loads(row[6] or "[]")),
                    usefulness_score=row[7] or 0.5,
                    content_length=row[8] or 0,
                    is_stale=bool(row[9]),
                ))

            return records

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sources")
            total_sources = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM sources WHERE is_stale = 1")
            stale_sources = cursor.fetchone()[0]

            cursor = conn.execute("SELECT AVG(usefulness_score) FROM sources")
            avg_usefulness = cursor.fetchone()[0] or 0.0

            cursor = conn.execute("SELECT SUM(content_length) FROM sources")
            total_content = cursor.fetchone()[0] or 0

            cursor = conn.execute("""
                SELECT fetch_date FROM sources ORDER BY fetch_date DESC LIMIT 1
            """)
            row = cursor.fetchone()
            last_fetch = datetime.fromisoformat(row[0]) if row else None

            # Data types breakdown
            cursor = conn.execute("SELECT data_types_found FROM sources")
            all_types: Dict[str, int] = {}
            for row in cursor.fetchall():
                types = json.loads(row[0] or "[]")
                for t in types:
                    all_types[t] = all_types.get(t, 0) + 1

        return {
            "total_sources": total_sources,
            "stale_sources": stale_sources,
            "fresh_sources": total_sources - stale_sources,
            "avg_usefulness_score": round(avg_usefulness, 2),
            "total_content_bytes": total_content,
            "last_fetch_date": last_fetch.isoformat() if last_fetch else None,
            "data_types_found": all_types,
        }

    def clear(self) -> None:
        """Clear all registry data (use with caution!)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM content_fingerprints")
            conn.execute("DELETE FROM sources")
            conn.execute("DELETE FROM registry_metadata")

        self._url_cache.clear()
        self._hash_cache.clear()

        logger.warning(f"Cleared source registry for {self.company_name}")


# =============================================================================
# Factory Function
# =============================================================================

_registries: Dict[str, PersistentSourceRegistry] = {}


def get_source_registry(
    company_name: str,
    base_dir: str = "outputs",
) -> PersistentSourceRegistry:
    """
    Get or create a source registry for a company.

    Args:
        company_name: Company name
        base_dir: Base output directory

    Returns:
        PersistentSourceRegistry instance
    """
    key = f"{base_dir}:{company_name}"

    if key not in _registries:
        _registries[key] = PersistentSourceRegistry(base_dir, company_name)

    return _registries[key]


def clear_registry_cache() -> None:
    """Clear the registry cache (for testing)."""
    global _registries
    _registries = {}


__all__ = [
    "SourceRecord",
    "ContentFingerprint",
    "PersistentSourceRegistry",
    "get_source_registry",
    "clear_registry_cache",
]
