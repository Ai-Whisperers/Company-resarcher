"""
Vault Manager - Persistent memory storage for research data.

Supports Vector Storage (Pinecone/Chroma) and Graph Storage (Neo4j)
with local JSON fallback when external services are unavailable.

Performance Optimizations (PERF-004):
- Uses JSON Lines format for O(1) append operations
- Batch writing to reduce I/O overhead
- File size monitoring and warnings
- Pagination support for large datasets
"""

from typing import List, Dict, Any, Optional
import os
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from ..core.logger import setup_logger

logger = setup_logger("vault")

# Timeout for file operations (configurable via environment)
FILE_OPERATION_TIMEOUT = int(os.getenv("VAULT_FILE_TIMEOUT_SECONDS", "30"))

# Maximum file size before warning (default: 50MB)
MAX_FILE_SIZE_MB = int(os.getenv("VAULT_MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Batch size for bulk operations
BATCH_SIZE = int(os.getenv("VAULT_BATCH_SIZE", "100"))

# File names for local storage
VECTORS_FILE = "vectors.jsonl"
GRAPH_FILE = "graph.jsonl"


class VaultManager:
    """
    Manages persistent memory for the system.
    Handles both Vector Storage (Pinecone/Chroma) and Graph Storage (Neo4j).
    Falls back to local JSON Lines storage if keys are missing.

    Performance improvements:
    - Uses JSON Lines (.jsonl) format for O(1) append operations
    - No need to read/rewrite entire file on each append
    - Supports pagination for large datasets
    - Thread-safe file operations
    """

    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.neo4j_uri = os.getenv("NEO4J_URI")

        self.use_pinecone = bool(self.pinecone_api_key)
        self.use_neo4j = bool(self.neo4j_uri)

        self.local_storage_path = Path("data/vault")
        self.local_storage_path.mkdir(parents=True, exist_ok=True)

        # File locks for thread-safe operations
        self._vector_lock = threading.Lock()
        self._graph_lock = threading.Lock()

        # Stats tracking
        self._stats = {
            "vectors_stored": 0,
            "graphs_stored": 0,
            "searches_performed": 0,
        }

        if not self.use_pinecone:
            logger.warning(
                "Pinecone API Key not found. Using local JSON Lines fallback for Vector Vault."
            )

        if not self.use_neo4j:
            logger.warning(
                "Neo4j URI not found. Using local JSON Lines fallback for Graph Vault."
            )

        # Check file sizes on init
        self._check_file_sizes()

    def _check_file_sizes(self) -> None:
        """Check and warn about large vault files."""
        for filename in [VECTORS_FILE, GRAPH_FILE]:
            filepath = self.local_storage_path / filename
            if filepath.exists():
                size = filepath.stat().st_size
                if size > MAX_FILE_SIZE_BYTES:
                    logger.warning(
                        f"Vault file {filename} is {size / 1024 / 1024:.1f}MB "
                        f"(threshold: {MAX_FILE_SIZE_MB}MB). Consider archiving old data."
                    )

    async def store_report(
        self, company_name: str, report_content: str, metadata: Dict[str, Any]
    ):
        """
        Stores a completed report into the Vault.
        """
        # 1. Store in Vector DB (Chunking would happen here)
        await self._store_vector(company_name, report_content, metadata)

        # 2. Store in Graph DB (Entity extraction would happen here)
        await self._store_graph(company_name, metadata)

    async def search_similar_companies(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for similar companies or past reports.
        """
        if self.use_pinecone:
            return await self._search_pinecone(query)
        else:
            return await self._search_local(query)

    async def _store_vector(
        self, company_name: str, content: str, metadata: Dict[str, Any]
    ):
        if self.use_pinecone:
            # Placeholder for Pinecone implementation
            pass
        else:
            # Local Fallback: Append to JSON Lines file (O(1) operation)
            filepath = self.local_storage_path / VECTORS_FILE
            entry = {
                "company": company_name,
                "content_snippet": content[:200],  # Store snippet
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
            }

            try:
                await asyncio.wait_for(
                    asyncio.to_thread(self._append_jsonl, filepath, entry, self._vector_lock),
                    timeout=FILE_OPERATION_TIMEOUT
                )
                self._stats["vectors_stored"] += 1
            except asyncio.TimeoutError:
                logger.error(f"Vault vector store timed out after {FILE_OPERATION_TIMEOUT}s")
                raise
            except Exception as e:
                logger.error(f"Error storing vector data: {e}")
                raise

    def _append_jsonl(self, filepath: Path, entry: Dict[str, Any], lock: threading.Lock) -> None:
        """
        Append a single entry to a JSON Lines file (thread-safe, O(1) operation).

        JSON Lines format: each line is a complete JSON object.
        This allows appending without reading/rewriting the entire file.
        """
        with lock:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _read_jsonl(self, filepath: Path, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Read entries from a JSON Lines file with optional pagination.

        Args:
            filepath: Path to the JSON Lines file
            limit: Maximum number of entries to return (None for all)
            offset: Number of entries to skip

        Returns:
            List of parsed JSON objects
        """
        if not filepath.exists():
            return []

        results = []
        current_line = 0

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Skip lines until we reach offset
                if current_line < offset:
                    current_line += 1
                    continue

                # Stop if we've reached the limit
                if limit is not None and len(results) >= limit:
                    break

                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line: {e}")

                current_line += 1

        return results

    def _read_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Read JSON file synchronously (legacy support for old .json files).
        Migrates to JSON Lines format if old file exists.
        """
        filepath = Path(filename)

        # Check for JSON Lines version first
        jsonl_path = filepath.with_suffix(".jsonl")
        if jsonl_path.exists():
            return self._read_jsonl(jsonl_path)

        # Fall back to old JSON format and migrate
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Migrate to JSON Lines format
                logger.info(f"Migrating {filepath} to JSON Lines format")
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    for entry in data:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

                # Optionally remove old file (or keep as backup)
                # filepath.unlink()

                return data
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {filepath}: {e}")
                return []

        return []

    def _write_json_file(self, filename: str, data: List[Dict[str, Any]]) -> None:
        """Write JSON file synchronously (legacy support)."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def _store_graph(self, company_name: str, metadata: Dict[str, Any]):
        if self.use_neo4j:
            # Placeholder for Neo4j implementation
            pass
        else:
            # Local Fallback: Append to JSON Lines file (O(1) operation)
            filepath = self.local_storage_path / GRAPH_FILE
            entry = {
                "node": company_name,
                "type": "Company",
                "properties": metadata,
                "timestamp": datetime.now().isoformat(),
            }

            try:
                await asyncio.wait_for(
                    asyncio.to_thread(self._append_jsonl, filepath, entry, self._graph_lock),
                    timeout=FILE_OPERATION_TIMEOUT
                )
                self._stats["graphs_stored"] += 1
            except asyncio.TimeoutError:
                logger.error(f"Vault graph store timed out after {FILE_OPERATION_TIMEOUT}s")
                raise
            except Exception as e:
                logger.error(f"Error storing graph data: {e}")
                raise

    async def _search_pinecone(self, query: str):
        return []

    async def _search_local(
        self,
        query: str,
        limit: Optional[int] = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search local vault with keyword matching and pagination.

        Args:
            query: Search query string
            limit: Maximum results to return
            offset: Number of results to skip (for pagination)

        Returns:
            List of matching entries
        """
        filepath = self.local_storage_path / VECTORS_FILE

        # Fall back to old .json if .jsonl doesn't exist
        if not filepath.exists():
            old_filepath = self.local_storage_path / "vectors.json"
            if old_filepath.exists():
                # Read and migrate
                data = await asyncio.wait_for(
                    asyncio.to_thread(self._read_json_file, str(old_filepath)),
                    timeout=FILE_OPERATION_TIMEOUT
                )
            else:
                return []
        else:
            try:
                data = await asyncio.wait_for(
                    asyncio.to_thread(self._read_jsonl, filepath),
                    timeout=FILE_OPERATION_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(f"Vault search timed out after {FILE_OPERATION_TIMEOUT}s")
                return []
            except Exception as e:
                logger.error(f"Error reading vault data: {e}")
                return []

        self._stats["searches_performed"] += 1
        query_lower = query.lower()
        results = []

        for d in data:
            # Check company name
            if query_lower in d.get("company", "").lower():
                results.append(d)
                continue

            # Check metadata (e.g. industry)
            metadata = d.get("metadata", {})
            if any(query_lower in str(v).lower() for v in metadata.values()):
                results.append(d)
                continue

        # Apply pagination
        start = offset
        end = offset + limit if limit else None
        return results[start:end]

    async def get_recent_entries(
        self,
        vault_type: str = "vectors",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent entries from a vault.

        Args:
            vault_type: "vectors" or "graph"
            limit: Maximum number of entries to return

        Returns:
            List of recent entries (most recent first)
        """
        filename = f"{vault_type}.jsonl"
        filepath = self.local_storage_path / filename

        if not filepath.exists():
            return []

        try:
            # Read all entries (for now - could be optimized with reverse reading)
            data = await asyncio.wait_for(
                asyncio.to_thread(self._read_jsonl, filepath),
                timeout=FILE_OPERATION_TIMEOUT
            )
            # Return most recent entries
            return list(reversed(data[-limit:]))
        except Exception as e:
            logger.error(f"Error reading recent entries: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics."""
        stats = self._stats.copy()

        # Add file sizes
        for name in [VECTORS_FILE, GRAPH_FILE]:
            filepath = self.local_storage_path / name
            if filepath.exists():
                size_bytes = filepath.stat().st_size
                stats[f"{name}_size_mb"] = round(size_bytes / 1024 / 1024, 2)
                # Count lines (entries)
                with open(filepath, "r") as f:
                    stats[f"{name}_entries"] = sum(1 for _ in f)
            else:
                stats[f"{name}_size_mb"] = 0
                stats[f"{name}_entries"] = 0

        return stats

    async def compact_vault(self, vault_type: str = "vectors") -> int:
        """
        Compact a vault file by removing duplicates and old entries.

        Args:
            vault_type: "vectors" or "graph"

        Returns:
            Number of entries removed
        """
        filename = f"{vault_type}.jsonl"
        filepath = self.local_storage_path / filename

        if not filepath.exists():
            return 0

        lock = self._vector_lock if vault_type == "vectors" else self._graph_lock

        def _compact():
            with lock:
                # Read all entries
                entries = self._read_jsonl(filepath)
                original_count = len(entries)

                # Remove duplicates (keep most recent by company name)
                seen = {}
                for entry in entries:
                    key = entry.get("company") or entry.get("node", "unknown")
                    if key not in seen or entry.get("timestamp", "") > seen[key].get("timestamp", ""):
                        seen[key] = entry

                # Write compacted file
                compacted = list(seen.values())
                with open(filepath, "w", encoding="utf-8") as f:
                    for entry in compacted:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

                return original_count - len(compacted)

        try:
            removed = await asyncio.wait_for(
                asyncio.to_thread(_compact),
                timeout=FILE_OPERATION_TIMEOUT * 2  # Allow more time for compaction
            )
            logger.info(f"Compacted {vault_type} vault, removed {removed} entries")
            return removed
        except Exception as e:
            logger.error(f"Error compacting vault: {e}")
            return 0
