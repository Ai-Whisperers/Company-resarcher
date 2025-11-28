"""Tests for the local file indexing system."""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from src.core.file_indexer import (
    ContentExtractor,
    FileIndexer,
    FileMetadata,
    FileType,
    IndexConfig,
    IndexStatus,
    get_file_indexer,
    reset_file_indexer,
)


class TestFileMetadata:
    """Tests for FileMetadata class."""

    def test_create_metadata(self):
        """Test creating file metadata."""
        meta = FileMetadata(
            path="/path/to/file.txt",
            file_name="file.txt",
            file_type=FileType.TEXT,
            size_bytes=1024,
            modified_at=datetime.now(),
            content_hash="abc123",
        )

        assert meta.path == "/path/to/file.txt"
        assert meta.file_type == FileType.TEXT
        assert meta.status == IndexStatus.PENDING

    def test_to_dict(self):
        """Test serialization."""
        meta = FileMetadata(
            path="/path/file.md",
            file_name="file.md",
            file_type=FileType.MARKDOWN,
            size_bytes=500,
            modified_at=datetime(2024, 1, 1, 12, 0, 0),
            content_hash="def456",
            status=IndexStatus.INDEXED,
            word_count=100,
        )
        data = meta.to_dict()

        assert data["path"] == "/path/file.md"
        assert data["file_type"] == "markdown"
        assert data["status"] == "indexed"
        assert data["word_count"] == 100

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "path": "/test/file.py",
            "file_name": "file.py",
            "file_type": "code",
            "size_bytes": 2048,
            "modified_at": "2024-01-15T10:30:00",
            "content_hash": "xyz789",
            "status": "indexed",
        }
        meta = FileMetadata.from_dict(data)

        assert meta.path == "/test/file.py"
        assert meta.file_type == FileType.CODE
        assert meta.status == IndexStatus.INDEXED


class TestIndexConfig:
    """Tests for IndexConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = IndexConfig()

        assert ".git" in config.exclude_dirs
        assert ".txt" in config.include_extensions
        assert config.max_file_size_bytes == 10 * 1024 * 1024

    def test_custom_config(self):
        """Test custom configuration."""
        config = IndexConfig(
            include_dirs=["/documents"],
            include_extensions=[".txt", ".md"],
            max_file_size_bytes=5 * 1024 * 1024,
        )

        assert config.include_dirs == ["/documents"]
        assert len(config.include_extensions) == 2

    def test_to_dict(self):
        """Test serialization."""
        config = IndexConfig(extract_content=False)
        data = config.to_dict()

        assert data["extract_content"] is False
        assert "include_extensions" in data


class TestContentExtractor:
    """Tests for ContentExtractor class."""

    def test_get_file_type_text(self):
        """Test file type detection for text."""
        assert ContentExtractor.get_file_type(Path("file.txt")) == FileType.TEXT
        assert ContentExtractor.get_file_type(Path("file.rst")) == FileType.TEXT

    def test_get_file_type_markdown(self):
        """Test file type detection for markdown."""
        assert ContentExtractor.get_file_type(Path("file.md")) == FileType.MARKDOWN
        assert ContentExtractor.get_file_type(Path("file.markdown")) == FileType.MARKDOWN

    def test_get_file_type_code(self):
        """Test file type detection for code."""
        assert ContentExtractor.get_file_type(Path("file.py")) == FileType.CODE
        assert ContentExtractor.get_file_type(Path("file.js")) == FileType.CODE
        assert ContentExtractor.get_file_type(Path("file.java")) == FileType.CODE

    def test_get_file_type_unknown(self):
        """Test unknown file type."""
        assert ContentExtractor.get_file_type(Path("file.xyz")) == FileType.UNKNOWN

    def test_extract_text_file(self):
        """Test extracting content from text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is test content.\nSecond line.")
            f.flush()

            content, title = ContentExtractor.extract(Path(f.name))

            assert content is not None
            assert "test content" in content

            Path(f.name).unlink()

    def test_extract_markdown_title(self):
        """Test extracting title from markdown."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# My Document Title\n\nContent here.")
            f.flush()

            content, title = ContentExtractor.extract(Path(f.name))

            assert title == "My Document Title"

            Path(f.name).unlink()

    def test_extract_html(self):
        """Test extracting content from HTML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><head><title>Page Title</title></head><body><p>Content</p></body></html>")
            f.flush()

            content, title = ContentExtractor.extract(Path(f.name))

            assert title == "Page Title"
            assert "Content" in content
            assert "<p>" not in content  # Tags should be stripped

            Path(f.name).unlink()


class TestFileIndexer:
    """Tests for FileIndexer class."""

    def setup_method(self):
        """Create temp directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_dir = tempfile.mkdtemp()
        self.indexer = FileIndexer(
            config=IndexConfig(),
            storage_path=Path(self.storage_dir),
        )

    def teardown_method(self):
        """Cleanup temp directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.storage_dir, ignore_errors=True)

    def _create_test_file(self, name: str, content: str) -> Path:
        """Create a test file."""
        path = Path(self.temp_dir) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_scan_directory(self):
        """Test directory scanning."""
        self._create_test_file("file1.txt", "Content 1")
        self._create_test_file("file2.md", "Content 2")
        self._create_test_file("subdir/file3.py", "print('hello')")

        files = self.indexer.scan_directory(self.temp_dir)

        assert len(files) == 3

    def test_scan_excludes_dirs(self):
        """Test excluded directories."""
        self._create_test_file("file.txt", "Content")
        self._create_test_file(".git/config", "git config")
        self._create_test_file("node_modules/package.json", "{}")

        files = self.indexer.scan_directory(self.temp_dir)

        # Should only find file.txt
        assert len(files) == 1
        assert files[0].name == "file.txt"

    def test_scan_filters_extensions(self):
        """Test extension filtering."""
        self._create_test_file("file.txt", "Content")
        self._create_test_file("image.png", "binary")
        self._create_test_file("data.exe", "binary")

        files = self.indexer.scan_directory(self.temp_dir)

        assert len(files) == 1
        assert files[0].suffix == ".txt"

    def test_index_file(self):
        """Test indexing a single file."""
        path = self._create_test_file("test.txt", "Hello World!")

        meta = self.indexer.index_file(path)

        assert meta.status == IndexStatus.INDEXED
        assert meta.content == "Hello World!"
        assert meta.word_count == 2

    def test_index_file_with_title(self):
        """Test extracting title from file."""
        path = self._create_test_file("doc.md", "# My Title\n\nContent here.")

        meta = self.indexer.index_file(path)

        assert meta.title == "My Title"

    def test_get_file(self):
        """Test getting indexed file."""
        path = self._create_test_file("test.txt", "Content")
        self.indexer.index_file(path)

        meta = self.indexer.get_file(str(path))

        assert meta is not None
        assert meta.file_name == "test.txt"

    def test_search_by_content(self):
        """Test searching by content."""
        self._create_test_file("python.txt", "Python programming language")
        self._create_test_file("java.txt", "Java programming language")
        self._create_test_file("other.txt", "Something else entirely")

        # Index all files
        files = self.indexer.scan_directory(self.temp_dir)
        for f in files:
            self.indexer.index_file(f)

        results = self.indexer.search("python")

        assert len(results) >= 1
        assert any("python" in r.file_name.lower() or
                   (r.content and "python" in r.content.lower())
                   for r in results)

    def test_search_by_filename(self):
        """Test searching by filename."""
        path = self._create_test_file("important_doc.txt", "Some content")
        self.indexer.index_file(path)

        results = self.indexer.search("important")

        assert len(results) == 1
        assert "important" in results[0].file_name

    def test_list_files(self):
        """Test listing indexed files."""
        self._create_test_file("file1.txt", "Content 1")
        self._create_test_file("file2.md", "Content 2")

        files = self.indexer.scan_directory(self.temp_dir)
        for f in files:
            self.indexer.index_file(f)

        all_files = self.indexer.list_files()
        assert len(all_files) == 2

    def test_list_files_by_type(self):
        """Test listing files by type."""
        self._create_test_file("file.txt", "Text")
        self._create_test_file("code.py", "print()")

        files = self.indexer.scan_directory(self.temp_dir)
        for f in files:
            self.indexer.index_file(f)

        text_files = self.indexer.list_files(file_type=FileType.TEXT)
        code_files = self.indexer.list_files(file_type=FileType.CODE)

        assert len(text_files) == 1
        assert len(code_files) == 1

    def test_remove_file(self):
        """Test removing a file from index."""
        path = self._create_test_file("test.txt", "Content")
        self.indexer.index_file(path)

        success = self.indexer.remove_file(str(path))
        assert success

        meta = self.indexer.get_file(str(path))
        assert meta is None

    def test_clear_index(self):
        """Test clearing the entire index."""
        self._create_test_file("file1.txt", "Content")
        self._create_test_file("file2.txt", "Content")

        files = self.indexer.scan_directory(self.temp_dir)
        for f in files:
            self.indexer.index_file(f)

        self.indexer.clear()

        all_files = self.indexer.list_files()
        assert len(all_files) == 0

    def test_reindex_changed(self):
        """Test re-indexing changed files."""
        path = self._create_test_file("test.txt", "Original content")
        self.indexer.index_file(path)

        # Modify the file
        import time
        time.sleep(0.1)  # Ensure mtime changes
        path.write_text("Updated content")

        changed = self.indexer.reindex_changed()

        assert len(changed) >= 1

    def test_get_statistics(self):
        """Test getting statistics."""
        self._create_test_file("file.txt", "Some words here")
        self._create_test_file("code.py", "print('hello')")

        files = self.indexer.scan_directory(self.temp_dir)
        for f in files:
            self.indexer.index_file(f)

        stats = self.indexer.get_statistics()

        assert stats["total_files"] == 2
        assert "by_type" in stats
        assert "by_status" in stats
        assert stats["total_words"] > 0

    def test_callback_on_index(self):
        """Test callback is called on index."""
        indexed_files = []

        def on_indexed(meta):
            indexed_files.append(meta)

        self.indexer.add_callback(on_indexed)
        path = self._create_test_file("test.txt", "Content")
        self.indexer.index_file(path)

        assert len(indexed_files) == 1

    def test_persistence(self):
        """Test index persists across instances."""
        path = self._create_test_file("persist.txt", "Persistent data")
        self.indexer.index_file(path)

        # Create new indexer with same storage
        new_indexer = FileIndexer(storage_path=Path(self.storage_dir))

        meta = new_indexer.get_file(str(path))
        assert meta is not None

    @pytest.mark.asyncio
    async def test_index_files_async(self):
        """Test async batch indexing."""
        for i in range(5):
            self._create_test_file(f"file{i}.txt", f"Content {i}")

        files = self.indexer.scan_directory(self.temp_dir)
        progress_calls = []

        def on_progress(current, total):
            progress_calls.append((current, total))

        results = await self.indexer.index_files(files, on_progress)

        assert len(results) == 5
        assert len(progress_calls) == 5


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_file_indexer()

    def teardown_method(self):
        """Reset after each test."""
        reset_file_indexer()

    def test_get_file_indexer_singleton(self):
        """Test singleton behavior."""
        i1 = get_file_indexer()
        i2 = get_file_indexer()
        assert i1 is i2

    def test_reset_file_indexer(self):
        """Test resetting singleton."""
        i1 = get_file_indexer()
        reset_file_indexer()
        i2 = get_file_indexer()
        assert i1 is not i2


class TestEdgeCases:
    """Tests for edge cases."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_dir = tempfile.mkdtemp()
        self.indexer = FileIndexer(storage_path=Path(self.storage_dir))

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.storage_dir, ignore_errors=True)

    def test_empty_file(self):
        """Test indexing empty file."""
        path = Path(self.temp_dir) / "empty.txt"
        path.write_text("")

        meta = self.indexer.index_file(path)

        assert meta.status == IndexStatus.INDEXED
        assert meta.word_count == 0

    def test_nonexistent_directory(self):
        """Test scanning nonexistent directory."""
        files = self.indexer.scan_directory("/nonexistent/path")
        assert files == []

    def test_unicode_content(self):
        """Test handling unicode content."""
        path = Path(self.temp_dir) / "unicode.txt"
        path.write_text("日本語テスト émoji 🎉", encoding="utf-8")

        meta = self.indexer.index_file(path)

        assert meta.status == IndexStatus.INDEXED
        assert "日本語" in meta.content

    def test_large_file_skipped(self):
        """Test large files are skipped."""
        config = IndexConfig(max_file_size_bytes=100)
        indexer = FileIndexer(config=config, storage_path=Path(self.storage_dir) / "small")

        path = Path(self.temp_dir) / "large.txt"
        path.write_text("x" * 200)

        files = indexer.scan_directory(self.temp_dir)
        assert len(files) == 0
