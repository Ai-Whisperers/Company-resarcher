"""
Local File Indexing for personalized context.

Provides infrastructure for scanning, indexing, and tracking changes
to local files for use in research and analysis.
"""

import asyncio
import hashlib
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..logging import setup_logger

logger = setup_logger("file_indexer")


class FileType(str, Enum):
    """Supported file types."""

    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    CODE = "code"
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    UNKNOWN = "unknown"


class IndexStatus(str, Enum):
    """File indexing status."""

    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileMetadata:
    """Metadata for an indexed file."""

    path: str
    file_name: str
    file_type: FileType
    size_bytes: int
    modified_at: datetime
    content_hash: str

    # Indexing info
    indexed_at: Optional[datetime] = None
    status: IndexStatus = IndexStatus.PENDING
    error_message: Optional[str] = None

    # Extracted content
    content: Optional[str] = None
    title: Optional[str] = None
    word_count: int = 0

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "file_name": self.file_name,
            "file_type": self.file_type.value,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at.isoformat(),
            "content_hash": self.content_hash,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "title": self.title,
            "word_count": self.word_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileMetadata":
        """Create from dictionary."""
        modified_at = data.get("modified_at")
        if isinstance(modified_at, str):
            modified_at = datetime.fromisoformat(modified_at)

        indexed_at = data.get("indexed_at")
        if isinstance(indexed_at, str):
            indexed_at = datetime.fromisoformat(indexed_at)

        return cls(
            path=data["path"],
            file_name=data["file_name"],
            file_type=FileType(data.get("file_type", "unknown")),
            size_bytes=data.get("size_bytes", 0),
            modified_at=modified_at or datetime.now(),
            content_hash=data.get("content_hash", ""),
            indexed_at=indexed_at,
            status=IndexStatus(data.get("status", "pending")),
            error_message=data.get("error_message"),
            title=data.get("title"),
            word_count=data.get("word_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class IndexConfig:
    """Configuration for file indexing."""

    # Directories
    include_dirs: List[str] = field(default_factory=list)
    exclude_dirs: List[str] = field(default_factory=lambda: [
        ".git", "__pycache__", "node_modules", ".venv", "venv",
        ".idea", ".vscode", "dist", "build", ".cache",
    ])

    # File patterns
    include_extensions: List[str] = field(default_factory=lambda: [
        ".txt", ".md", ".markdown", ".rst",
        ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h",
        ".json", ".yaml", ".yml", ".toml",
        ".csv", ".html", ".xml",
    ])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "*.min.js", "*.min.css", "package-lock.json",
        "*.pyc", "*.pyo", "*.log",
    ])

    # Size limits
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10MB
    min_file_size_bytes: int = 0

    # Content processing
    extract_content: bool = True
    max_content_length: int = 100000  # Characters

    # Change detection
    use_content_hash: bool = True
    use_mtime: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "include_dirs": self.include_dirs,
            "exclude_dirs": self.exclude_dirs,
            "include_extensions": self.include_extensions,
            "exclude_patterns": self.exclude_patterns,
            "max_file_size_bytes": self.max_file_size_bytes,
            "min_file_size_bytes": self.min_file_size_bytes,
            "extract_content": self.extract_content,
            "max_content_length": self.max_content_length,
            "use_content_hash": self.use_content_hash,
            "use_mtime": self.use_mtime,
        }


class ContentExtractor:
    """Extracts content from various file types."""

    # Extension to file type mapping
    EXTENSION_MAP = {
        ".txt": FileType.TEXT,
        ".md": FileType.MARKDOWN,
        ".markdown": FileType.MARKDOWN,
        ".rst": FileType.TEXT,
        ".py": FileType.CODE,
        ".js": FileType.CODE,
        ".ts": FileType.CODE,
        ".java": FileType.CODE,
        ".cpp": FileType.CODE,
        ".c": FileType.CODE,
        ".h": FileType.CODE,
        ".go": FileType.CODE,
        ".rs": FileType.CODE,
        ".rb": FileType.CODE,
        ".php": FileType.CODE,
        ".json": FileType.JSON,
        ".yaml": FileType.TEXT,
        ".yml": FileType.TEXT,
        ".toml": FileType.TEXT,
        ".csv": FileType.CSV,
        ".html": FileType.HTML,
        ".htm": FileType.HTML,
        ".xml": FileType.TEXT,
        ".pdf": FileType.PDF,
    }

    @classmethod
    def get_file_type(cls, path: Path) -> FileType:
        """Determine file type from extension."""
        ext = path.suffix.lower()
        return cls.EXTENSION_MAP.get(ext, FileType.UNKNOWN)

    @classmethod
    def extract(
        cls,
        path: Path,
        max_length: int = 100000,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Extract content and title from a file.

        Returns:
            Tuple of (content, title).
        """
        file_type = cls.get_file_type(path)

        try:
            if file_type == FileType.PDF:
                return cls._extract_pdf(path, max_length)
            elif file_type in (FileType.TEXT, FileType.CODE, FileType.JSON,
                               FileType.CSV, FileType.MARKDOWN):
                return cls._extract_text(path, max_length)
            elif file_type == FileType.HTML:
                return cls._extract_html(path, max_length)
            else:
                return None, None
        except Exception as e:
            logger.warning(f"Failed to extract content from {path}: {e}")
            return None, None

    @classmethod
    def _extract_text(
        cls,
        path: Path,
        max_length: int,
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract content from text files."""
        encodings = ["utf-8", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                content = path.read_text(encoding=encoding)
                content = content[:max_length]

                # Extract title from first line or markdown header
                title = None
                lines = content.split("\n")
                if lines:
                    first_line = lines[0].strip()
                    if first_line.startswith("# "):
                        title = first_line[2:].strip()
                    elif first_line and len(first_line) < 100:
                        title = first_line

                return content, title
            except UnicodeDecodeError:
                continue

        return None, None

    @classmethod
    def _extract_html(
        cls,
        path: Path,
        max_length: int,
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract content from HTML files."""
        content, _ = cls._extract_text(path, max_length * 2)
        if not content:
            return None, None

        # Simple HTML tag stripping
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Extract title
        title = None
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

        return text[:max_length], title

    @classmethod
    def _extract_pdf(
        cls,
        path: Path,
        max_length: int,
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract content from PDF files (placeholder)."""
        # PDF extraction requires external libraries (pypdf, pdfplumber, etc.)
        # Return placeholder for now
        return f"[PDF file: {path.name}]", path.stem


class FileIndexer:
    """
    Indexes local files for personalized context.

    Scans directories, tracks changes, and extracts content.
    """

    def __init__(
        self,
        config: Optional[IndexConfig] = None,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize the indexer.

        Args:
            config: Indexing configuration.
            storage_path: Path to store index data.
        """
        self.config = config or IndexConfig()
        self.storage_path = storage_path or Path("./file_index")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._index: Dict[str, FileMetadata] = {}
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[FileMetadata], None]] = []

        self._load_index()

    def _load_index(self) -> None:
        """Load existing index from storage."""
        import json

        index_file = self.storage_path / "index.json"
        if index_file.exists():
            try:
                data = json.loads(index_file.read_text())
                for item in data:
                    meta = FileMetadata.from_dict(item)
                    self._index[meta.path] = meta
                logger.info(f"Loaded index with {len(self._index)} files")
            except Exception as e:
                logger.warning(f"Failed to load index: {e}")

    def _save_index(self) -> None:
        """Save index to storage."""
        import json

        index_file = self.storage_path / "index.json"
        data = [m.to_dict() for m in self._index.values()]
        index_file.write_text(json.dumps(data, indent=2))

    def _compute_hash(self, path: Path) -> str:
        """Compute content hash for a file."""
        hasher = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]
        except (OSError, IOError) as e:
            # Log file I/O errors (BUG-008)
            logger.debug(f"Failed to compute hash for {path}: {e}")
            return ""

    def _should_index(self, path: Path) -> bool:
        """Check if a file should be indexed."""
        # Check extension
        if self.config.include_extensions:
            if path.suffix.lower() not in self.config.include_extensions:
                return False

        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if path.match(pattern):
                return False

        # Check size
        try:
            size = path.stat().st_size
            if size > self.config.max_file_size_bytes:
                return False
            if size < self.config.min_file_size_bytes:
                return False
        except OSError:
            return False

        return True

    def _has_changed(self, path: Path, existing: FileMetadata) -> bool:
        """Check if a file has changed since last index."""
        try:
            stat = path.stat()

            # Check mtime
            if self.config.use_mtime:
                current_mtime = datetime.fromtimestamp(stat.st_mtime)
                if current_mtime > existing.modified_at:
                    return True

            # Check content hash
            if self.config.use_content_hash:
                current_hash = self._compute_hash(path)
                if current_hash != existing.content_hash:
                    return True

            return False
        except (OSError, IOError) as e:
            # Log file access errors (BUG-008)
            logger.debug(f"Failed to check if {path} changed: {e}")
            return True  # Assume changed if we can't check

    def add_callback(self, callback: Callable[[FileMetadata], None]) -> None:
        """Add callback for index updates."""
        self._callbacks.append(callback)

    def _notify_callbacks(self, meta: FileMetadata) -> None:
        """Notify callbacks of file indexed."""
        for callback in self._callbacks:
            try:
                callback(meta)
            except Exception as e:
                logger.warning(f"Callback error: {e}")

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
    ) -> List[Path]:
        """
        Scan a directory for indexable files.

        Args:
            directory: Directory path to scan.
            recursive: Whether to scan subdirectories.

        Returns:
            List of file paths to index.
        """
        dir_path = Path(directory).expanduser().resolve()
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []

        files: List[Path] = []

        if recursive:
            for root, dirs, filenames in os.walk(dir_path):
                # Filter excluded directories
                dirs[:] = [d for d in dirs if d not in self.config.exclude_dirs]

                for filename in filenames:
                    file_path = Path(root) / filename
                    if self._should_index(file_path):
                        files.append(file_path)
        else:
            for item in dir_path.iterdir():
                if item.is_file() and self._should_index(item):
                    files.append(item)

        logger.info(f"Found {len(files)} files to index in {directory}")
        return files

    def index_file(self, path: Path) -> FileMetadata:
        """
        Index a single file.

        Args:
            path: File path to index.

        Returns:
            FileMetadata for the indexed file.
        """
        path = Path(path).resolve()
        path_str = str(path)

        try:
            stat = path.stat()

            # Create metadata
            meta = FileMetadata(
                path=path_str,
                file_name=path.name,
                file_type=ContentExtractor.get_file_type(path),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                content_hash=self._compute_hash(path),
            )

            # Extract content
            if self.config.extract_content:
                content, title = ContentExtractor.extract(
                    path, self.config.max_content_length
                )
                meta.content = content
                meta.title = title or path.stem
                if content:
                    meta.word_count = len(content.split())

            meta.indexed_at = datetime.now()
            meta.status = IndexStatus.INDEXED

        except Exception as e:
            meta = FileMetadata(
                path=path_str,
                file_name=path.name,
                file_type=FileType.UNKNOWN,
                size_bytes=0,
                modified_at=datetime.now(),
                content_hash="",
                status=IndexStatus.FAILED,
                error_message=str(e),
            )
            logger.error(f"Failed to index {path}: {e}")

        with self._lock:
            self._index[path_str] = meta
            self._save_index()

        self._notify_callbacks(meta)
        return meta

    async def index_files(
        self,
        files: List[Path],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[FileMetadata]:
        """
        Index multiple files.

        Args:
            files: List of file paths.
            progress_callback: Optional callback(current, total).

        Returns:
            List of FileMetadata.
        """
        results = []
        total = len(files)

        for i, file_path in enumerate(files):
            meta = self.index_file(file_path)
            results.append(meta)

            if progress_callback:
                progress_callback(i + 1, total)

            # Yield to event loop periodically
            if i % 10 == 0:
                await asyncio.sleep(0)

        return results

    def reindex_changed(self) -> List[FileMetadata]:
        """
        Re-index files that have changed.

        Returns:
            List of re-indexed FileMetadata.
        """
        changed = []

        with self._lock:
            paths = list(self._index.keys())

        for path_str in paths:
            path = Path(path_str)

            if not path.exists():
                # File deleted
                with self._lock:
                    if path_str in self._index:
                        del self._index[path_str]
                continue

            existing = self._index.get(path_str)
            if existing and self._has_changed(path, existing):
                meta = self.index_file(path)
                changed.append(meta)

        if changed:
            with self._lock:
                self._save_index()

        logger.info(f"Re-indexed {len(changed)} changed files")
        return changed

    def get_file(self, path: str) -> Optional[FileMetadata]:
        """Get metadata for a specific file."""
        return self._index.get(str(Path(path).resolve()))

    def search(
        self,
        query: str,
        file_types: Optional[List[FileType]] = None,
        limit: int = 10,
    ) -> List[FileMetadata]:
        """
        Search indexed files by content.

        Args:
            query: Search query.
            file_types: Filter by file types.
            limit: Maximum results.

        Returns:
            List of matching FileMetadata.
        """
        query_lower = query.lower()
        results: List[tuple[float, FileMetadata]] = []

        for meta in self._index.values():
            if meta.status != IndexStatus.INDEXED:
                continue

            if file_types and meta.file_type not in file_types:
                continue

            score = 0.0

            # Check title
            if meta.title and query_lower in meta.title.lower():
                score += 2.0

            # Check filename
            if query_lower in meta.file_name.lower():
                score += 1.5

            # Check content
            if meta.content and query_lower in meta.content.lower():
                # Count occurrences
                count = meta.content.lower().count(query_lower)
                score += min(count * 0.1, 1.0)

            if score > 0:
                results.append((score, meta))

        # Sort by score
        results.sort(key=lambda x: x[0], reverse=True)
        return [meta for _, meta in results[:limit]]

    def list_files(
        self,
        file_type: Optional[FileType] = None,
        status: Optional[IndexStatus] = None,
        directory: Optional[str] = None,
    ) -> List[FileMetadata]:
        """
        List indexed files with optional filters.

        Args:
            file_type: Filter by file type.
            status: Filter by status.
            directory: Filter by directory prefix.

        Returns:
            List of FileMetadata.
        """
        results = []

        for meta in self._index.values():
            if file_type and meta.file_type != file_type:
                continue
            if status and meta.status != status:
                continue
            if directory and not meta.path.startswith(directory):
                continue

            results.append(meta)

        return sorted(results, key=lambda m: m.indexed_at or datetime.min, reverse=True)

    def remove_file(self, path: str) -> bool:
        """Remove a file from the index."""
        path_str = str(Path(path).resolve())
        with self._lock:
            if path_str in self._index:
                del self._index[path_str]
                self._save_index()
                return True
        return False

    def clear(self) -> None:
        """Clear the entire index."""
        with self._lock:
            self._index.clear()
            self._save_index()

    def get_statistics(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        total = len(self._index)
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        total_size = 0
        total_words = 0

        for meta in self._index.values():
            by_type[meta.file_type.value] = by_type.get(meta.file_type.value, 0) + 1
            by_status[meta.status.value] = by_status.get(meta.status.value, 0) + 1
            total_size += meta.size_bytes
            total_words += meta.word_count

        return {
            "total_files": total,
            "by_type": by_type,
            "by_status": by_status,
            "total_size_bytes": total_size,
            "total_words": total_words,
        }


# Global instance
_indexer: Optional[FileIndexer] = None
_global_lock = threading.Lock()


def get_file_indexer(config: Optional[IndexConfig] = None) -> FileIndexer:
    """Get or create the global file indexer."""
    global _indexer
    with _global_lock:
        if _indexer is None:
            _indexer = FileIndexer(config)
        return _indexer


def reset_file_indexer() -> None:
    """Reset the global indexer (for testing)."""
    global _indexer
    with _global_lock:
        _indexer = None
