"""
Checkpoint Manager - Resume capability for batch research.

This module provides checkpoint/resume functionality for long-running batch
research operations. It saves progress to a JSON file so research can be
resumed after interruption (Ctrl+C, crash, etc.).

Usage:
    python main.py --batch research_targets/paraguay_telecom --full --resume

Features:
- Tracks company-level progress (completed, in_progress, pending)
- Atomic writes to prevent checkpoint corruption
- Auto-detection of completed companies via output files
- Configurable minimum file threshold for "complete" status
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import setup_logger

logger = setup_logger("checkpoint_manager")

# Minimum number of .md files to consider a company research "complete"
MIN_FILES_FOR_COMPLETE = 40  # Out of expected ~52


@dataclass
class CompanyCheckpoint:
    """Checkpoint state for a single company."""
    name: str
    status: str = "pending"  # "pending", "in_progress", "completed", "error"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    sources_count: int = 0
    files_generated: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompanyCheckpoint":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            status=data.get("status", "pending"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            sources_count=data.get("sources_count", 0),
            files_generated=data.get("files_generated", 0),
            error_message=data.get("error_message"),
        )


@dataclass
class BatchCheckpoint:
    """Checkpoint state for a batch research operation."""
    version: str = "1.0"
    batch_path: str = ""
    started_at: str = ""
    last_updated: str = ""
    status: str = "pending"  # "pending", "in_progress", "completed"
    companies: Dict[str, CompanyCheckpoint] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "batch_path": self.batch_path,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "status": self.status,
            "companies": {
                name: cp.to_dict() for name, cp in self.companies.items()
            },
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchCheckpoint":
        """Create from dictionary."""
        companies = {}
        for name, cp_data in data.get("companies", {}).items():
            cp_data["name"] = name
            companies[name] = CompanyCheckpoint.from_dict(cp_data)

        return cls(
            version=data.get("version", "1.0"),
            batch_path=data.get("batch_path", ""),
            started_at=data.get("started_at", ""),
            last_updated=data.get("last_updated", ""),
            status=data.get("status", "pending"),
            companies=companies,
            config=data.get("config", {}),
        )


class CheckpointManager:
    """
    Manages batch research checkpoints for resume capability.

    Checkpoints are stored in: outputs/.checkpoints/{batch_name}.json

    Example:
        checkpoint = CheckpointManager("research_targets/paraguay_telecom")

        # On resume
        if checkpoint.exists():
            pending = checkpoint.get_pending_companies(all_profiles)
            print(f"Resuming: {len(pending)} companies remaining")

        # During research
        checkpoint.mark_company_started("Tigo_Paraguay")
        # ... research ...
        checkpoint.mark_company_completed("Tigo_Paraguay", sources=156, files=52)
    """

    def __init__(
        self,
        batch_path: str,
        output_dir: str = None,
    ):
        """
        Initialize checkpoint manager.

        Args:
            batch_path: Path to the batch research folder
            output_dir: Output directory (default from OUTPUT_DIR env var or "outputs")
        """
        self.batch_path = batch_path
        self.output_dir = output_dir or os.getenv("OUTPUT_DIR", "outputs")

        # Derive batch name from path
        self.batch_name = Path(batch_path).name

        # Checkpoint file location
        self.checkpoint_dir = Path(self.output_dir) / ".checkpoints"
        self.checkpoint_file = self.checkpoint_dir / f"{self.batch_name}.json"

        # In-memory state
        self._checkpoint: Optional[BatchCheckpoint] = None

    def exists(self) -> bool:
        """Check if a checkpoint file exists."""
        return self.checkpoint_file.exists()

    def load(self) -> Optional[BatchCheckpoint]:
        """
        Load existing checkpoint if exists.

        Returns:
            BatchCheckpoint if exists, None otherwise
        """
        if not self.exists():
            return None

        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._checkpoint = BatchCheckpoint.from_dict(data)
            logger.info(f"Loaded checkpoint: {self.checkpoint_file}")
            return self._checkpoint
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def save(self) -> bool:
        """
        Save current checkpoint state (atomic write).

        Uses write-to-temp-then-rename pattern for atomicity.

        Returns:
            True if save succeeded, False otherwise
        """
        if self._checkpoint is None:
            return False

        try:
            # Ensure checkpoint directory exists
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

            # Update timestamp
            self._checkpoint.last_updated = datetime.now().isoformat()

            # Atomic write: write to temp file, then rename
            fd, temp_path = tempfile.mkstemp(
                suffix=".json",
                prefix="checkpoint_",
                dir=self.checkpoint_dir,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self._checkpoint.to_dict(), f, indent=2)

                # Atomic rename (works on same filesystem)
                shutil.move(temp_path, self.checkpoint_file)
                logger.debug(f"Checkpoint saved: {self.checkpoint_file}")
                return True
            except Exception:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    def initialize(
        self,
        profiles: List[Dict[str, Any]],
        config: Dict[str, Any] = None,
    ) -> BatchCheckpoint:
        """
        Initialize a new checkpoint for batch research.

        Args:
            profiles: List of company profiles from batch
            config: Optional configuration to store

        Returns:
            New BatchCheckpoint
        """
        now = datetime.now().isoformat()

        # Create company checkpoints
        companies = {}
        for profile in profiles:
            name = profile.get("name", "Unknown")
            companies[name] = CompanyCheckpoint(name=name)

        self._checkpoint = BatchCheckpoint(
            batch_path=self.batch_path,
            started_at=now,
            last_updated=now,
            status="in_progress",
            companies=companies,
            config=config or {},
        )

        self.save()
        logger.info(f"Initialized checkpoint for {len(profiles)} companies")
        return self._checkpoint

    def clear(self) -> bool:
        """
        Clear/delete existing checkpoint.

        Returns:
            True if cleared, False otherwise
        """
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                logger.info(f"Cleared checkpoint: {self.checkpoint_file}")
            self._checkpoint = None
            return True
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")
            return False

    def mark_company_started(self, company_name: str) -> None:
        """Mark a company as started (in_progress)."""
        if self._checkpoint is None:
            return

        if company_name not in self._checkpoint.companies:
            self._checkpoint.companies[company_name] = CompanyCheckpoint(name=company_name)

        cp = self._checkpoint.companies[company_name]
        cp.status = "in_progress"
        cp.started_at = datetime.now().isoformat()
        cp.error_message = None

        self.save()
        logger.debug(f"Company started: {company_name}")

    def mark_company_completed(
        self,
        company_name: str,
        sources_count: int = 0,
        files_generated: int = 0,
    ) -> None:
        """Mark a company as completed with statistics."""
        if self._checkpoint is None:
            return

        if company_name not in self._checkpoint.companies:
            self._checkpoint.companies[company_name] = CompanyCheckpoint(name=company_name)

        cp = self._checkpoint.companies[company_name]
        cp.status = "completed"
        cp.completed_at = datetime.now().isoformat()
        cp.sources_count = sources_count
        cp.files_generated = files_generated

        # Check if all companies are complete
        all_complete = all(
            c.status == "completed" for c in self._checkpoint.companies.values()
        )
        if all_complete:
            self._checkpoint.status = "completed"

        self.save()
        logger.info(f"Company completed: {company_name} ({sources_count} sources, {files_generated} files)")

    def mark_company_error(self, company_name: str, error: str) -> None:
        """Mark a company as failed with error message."""
        if self._checkpoint is None:
            return

        if company_name not in self._checkpoint.companies:
            self._checkpoint.companies[company_name] = CompanyCheckpoint(name=company_name)

        cp = self._checkpoint.companies[company_name]
        cp.status = "error"
        cp.error_message = error

        self.save()
        logger.warning(f"Company error: {company_name} - {error}")

    def get_pending_companies(
        self,
        all_profiles: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Get list of companies that still need to be researched.

        Filters out companies that are already "completed" in the checkpoint.

        Args:
            all_profiles: All company profiles from batch

        Returns:
            List of profiles for pending companies
        """
        if self._checkpoint is None:
            # No checkpoint, all companies are pending
            return all_profiles

        pending = []
        for profile in all_profiles:
            name = profile.get("name", "")
            cp = self._checkpoint.companies.get(name)

            # Include if: no checkpoint entry, or not completed
            if cp is None or cp.status != "completed":
                pending.append(profile)

        return pending

    def is_company_completed(self, company_name: str) -> bool:
        """Check if a company is marked as completed in checkpoint."""
        if self._checkpoint is None:
            return False

        cp = self._checkpoint.companies.get(company_name)
        return cp is not None and cp.status == "completed"

    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics."""
        if self._checkpoint is None:
            return {"status": "no_checkpoint"}

        companies = self._checkpoint.companies.values()
        return {
            "status": self._checkpoint.status,
            "total_companies": len(companies),
            "completed": sum(1 for c in companies if c.status == "completed"),
            "in_progress": sum(1 for c in companies if c.status == "in_progress"),
            "pending": sum(1 for c in companies if c.status == "pending"),
            "errors": sum(1 for c in companies if c.status == "error"),
            "total_sources": sum(c.sources_count for c in companies),
            "total_files": sum(c.files_generated for c in companies),
        }

    def detect_completed_from_outputs(self) -> Dict[str, bool]:
        """
        Detect which companies appear complete based on output files.

        This is a backup detection method when checkpoint is missing.
        Checks if company output directory has minimum number of .md files.

        Returns:
            Dict mapping company name to completion status
        """
        results = {}
        output_path = Path(self.output_dir)

        if not output_path.exists():
            return results

        # Check each subdirectory in outputs
        for company_dir in output_path.iterdir():
            if not company_dir.is_dir():
                continue
            if company_dir.name.startswith("."):
                continue

            # Count .md files
            md_files = list(company_dir.rglob("*.md"))
            is_complete = len(md_files) >= MIN_FILES_FOR_COMPLETE
            results[company_dir.name] = is_complete

            if is_complete:
                logger.debug(f"Detected complete: {company_dir.name} ({len(md_files)} files)")

        return results

    def sync_from_outputs(self, profiles: List[Dict[str, Any]]) -> BatchCheckpoint:
        """
        Sync checkpoint state from existing output files.

        Useful when resuming without a checkpoint file - detects what's
        already been completed based on output directory contents.

        Args:
            profiles: All company profiles from batch

        Returns:
            Updated BatchCheckpoint
        """
        # Initialize if needed
        if self._checkpoint is None:
            self.initialize(profiles)

        # Detect completed companies from outputs
        detected = self.detect_completed_from_outputs()

        for name, is_complete in detected.items():
            if is_complete and name in self._checkpoint.companies:
                cp = self._checkpoint.companies[name]
                if cp.status != "completed":
                    # Count files for stats
                    company_dir = Path(self.output_dir) / name
                    file_count = len(list(company_dir.rglob("*.md")))

                    cp.status = "completed"
                    cp.files_generated = file_count
                    logger.info(f"Synced from outputs: {name} marked as completed ({file_count} files)")

        self.save()
        return self._checkpoint


def get_checkpoint_manager(batch_path: str, output_dir: str = None) -> CheckpointManager:
    """
    Factory function to create a checkpoint manager.

    Args:
        batch_path: Path to the batch research folder
        output_dir: Output directory (optional)

    Returns:
        CheckpointManager instance
    """
    return CheckpointManager(batch_path, output_dir)


__all__ = [
    "CheckpointManager",
    "BatchCheckpoint",
    "CompanyCheckpoint",
    "get_checkpoint_manager",
]
