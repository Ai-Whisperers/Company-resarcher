"""
LangGraph checkpointer for research workflow persistence.

Provides checkpoint storage for resumable research tasks using SQLite.
This enables:
- Resume research after crashes or interruptions
- Human-in-the-loop workflows with state persistence
- Audit trail of research execution
- Rollback to previous states

Usage:
    from src.graph.checkpointer import get_checkpointer, cleanup_old_checkpoints

    # Create checkpointer for graph
    checkpointer = get_checkpointer()
    graph = builder.compile(checkpointer=checkpointer)

    # Run with checkpoint
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "research-123"}}
    )

    # Resume from checkpoint
    result = await graph.ainvoke(
        None,  # None = continue from last checkpoint
        config={"configurable": {"thread_id": "research-123"}}
    )
"""

from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from langgraph.checkpoint.sqlite import SqliteSaver

from src.core.logging import setup_logger
from src.core.config import get_settings

logger = setup_logger("graph.checkpointer")

# Global checkpointer instance (singleton pattern)
_checkpointer: Optional[SqliteSaver] = None
_checkpoint_db_path: Optional[Path] = None


def get_checkpoint_db_path() -> Path:
    """
    Get the path for the checkpoint database.

    Uses configuration from settings or defaults to data/checkpoints/research.db

    Returns:
        Path to checkpoint database file
    """
    global _checkpoint_db_path

    if _checkpoint_db_path is not None:
        return _checkpoint_db_path

    settings = get_settings()

    # Check if custom path is configured
    checkpoint_path = getattr(settings.graph, "checkpoint_db_path", None)

    if checkpoint_path:
        _checkpoint_db_path = Path(checkpoint_path)
    else:
        # Default: data/checkpoints/research.db
        _checkpoint_db_path = Path("data/checkpoints/research.db")

    # Ensure directory exists
    _checkpoint_db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Checkpoint database path: {_checkpoint_db_path}")

    return _checkpoint_db_path


def get_checkpointer(
    db_path: Optional[str | Path] = None,
    force_new: bool = False,
    enabled: Optional[bool] = None,
) -> Optional[SqliteSaver]:
    """
    Get the global checkpointer instance.

    Creates a SqliteSaver on first call, reuses same instance thereafter
    unless force_new=True. Returns None if checkpointing is disabled.

    Args:
        db_path: Optional custom database path
        force_new: Force creation of new checkpointer instance
        enabled: Override settings to enable/disable checkpointing

    Returns:
        SqliteSaver instance for checkpoint storage, or None if disabled

    Example:
        checkpointer = get_checkpointer()
        graph = builder.compile(checkpointer=checkpointer)
    """
    global _checkpointer

    # Check if checkpointing is enabled
    settings = get_settings()
    is_enabled = enabled if enabled is not None else settings.graph.enable_checkpointing

    if not is_enabled:
        logger.debug("Checkpointing is disabled via configuration")
        return None

    if _checkpointer is not None and not force_new:
        return _checkpointer

    # Determine database path
    if db_path is None:
        db_path = get_checkpoint_db_path()
    else:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create SqliteSaver
    try:
        # SqliteSaver.from_conn_string creates the DB and tables automatically
        conn_string = f"sqlite:///{db_path}"
        _checkpointer = SqliteSaver.from_conn_string(conn_string)

        logger.info(f"Initialized checkpointer with database: {db_path}")

        return _checkpointer

    except Exception as e:
        logger.error(f"Failed to initialize checkpointer: {e}")
        raise


def reset_checkpointer() -> None:
    """
    Reset the global checkpointer instance.

    Useful for testing or when switching database paths.
    """
    global _checkpointer
    _checkpointer = None
    logger.info("Checkpointer reset")


def cleanup_old_checkpoints(
    max_age_days: int = 30,
    db_path: Optional[str | Path] = None,
) -> int:
    """
    Clean up old checkpoints from the database.

    Removes checkpoint entries older than max_age_days to prevent
    database bloat.

    Args:
        max_age_days: Maximum age of checkpoints to keep (default: 30 days)
        db_path: Optional database path (uses default if None)

    Returns:
        Number of checkpoints deleted

    Example:
        # Clean up checkpoints older than 7 days
        deleted = cleanup_old_checkpoints(max_age_days=7)
        logger.info(f"Deleted {deleted} old checkpoints")
    """
    if db_path is None:
        db_path = get_checkpoint_db_path()
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        logger.info("No checkpoint database found, nothing to clean")
        return 0

    try:
        import sqlite3
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_date.timestamp()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get count before deletion
        cursor.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE created_at < ?",
            (cutoff_timestamp,)
        )
        count_before = cursor.fetchone()[0]

        if count_before == 0:
            logger.info("No old checkpoints to clean")
            conn.close()
            return 0

        # Delete old checkpoints
        cursor.execute(
            "DELETE FROM checkpoints WHERE created_at < ?",
            (cutoff_timestamp,)
        )

        conn.commit()
        deleted = cursor.rowcount

        # Vacuum to reclaim space
        cursor.execute("VACUUM")

        conn.close()

        logger.info(
            f"Cleaned up {deleted} checkpoints older than {max_age_days} days"
        )

        return deleted

    except Exception as e:
        logger.error(f"Failed to clean up checkpoints: {e}")
        return 0


def list_checkpoints(
    db_path: Optional[str | Path] = None,
    limit: int = 100,
) -> list[dict]:
    """
    List recent checkpoints in the database.

    Args:
        db_path: Optional database path (uses default if None)
        limit: Maximum number of checkpoints to return

    Returns:
        List of checkpoint metadata dicts

    Example:
        checkpoints = list_checkpoints(limit=10)
        for cp in checkpoints:
            print(f"Thread: {cp['thread_id']}, Created: {cp['created_at']}")
    """
    if db_path is None:
        db_path = get_checkpoint_db_path()
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        logger.info("No checkpoint database found")
        return []

    try:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                thread_id,
                checkpoint_id,
                created_at,
                parent_checkpoint_id
            FROM checkpoints
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        checkpoints = []
        for row in cursor.fetchall():
            checkpoints.append({
                "thread_id": row["thread_id"],
                "checkpoint_id": row["checkpoint_id"],
                "created_at": datetime.fromtimestamp(row["created_at"]).isoformat(),
                "parent_checkpoint_id": row["parent_checkpoint_id"],
            })

        conn.close()

        logger.debug(f"Found {len(checkpoints)} checkpoints")

        return checkpoints

    except Exception as e:
        logger.error(f"Failed to list checkpoints: {e}")
        return []


def get_checkpoint_stats(db_path: Optional[str | Path] = None) -> dict:
    """
    Get statistics about the checkpoint database.

    Args:
        db_path: Optional database path (uses default if None)

    Returns:
        Dict with stats: total_checkpoints, unique_threads, db_size_mb, oldest, newest

    Example:
        stats = get_checkpoint_stats()
        print(f"Total checkpoints: {stats['total_checkpoints']}")
        print(f"Database size: {stats['db_size_mb']:.2f} MB")
    """
    if db_path is None:
        db_path = get_checkpoint_db_path()
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        return {
            "total_checkpoints": 0,
            "unique_threads": 0,
            "db_size_mb": 0.0,
            "oldest": None,
            "newest": None,
        }

    try:
        import sqlite3

        # Get database file size
        db_size_mb = db_path.stat().st_size / (1024 * 1024)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Total checkpoints
        cursor.execute("SELECT COUNT(*) FROM checkpoints")
        total_checkpoints = cursor.fetchone()[0]

        # Unique threads
        cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
        unique_threads = cursor.fetchone()[0]

        # Oldest and newest
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM checkpoints")
        oldest_ts, newest_ts = cursor.fetchone()

        oldest = datetime.fromtimestamp(oldest_ts).isoformat() if oldest_ts else None
        newest = datetime.fromtimestamp(newest_ts).isoformat() if newest_ts else None

        conn.close()

        stats = {
            "total_checkpoints": total_checkpoints,
            "unique_threads": unique_threads,
            "db_size_mb": round(db_size_mb, 2),
            "oldest": oldest,
            "newest": newest,
        }

        logger.debug(f"Checkpoint stats: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Failed to get checkpoint stats: {e}")
        return {
            "total_checkpoints": 0,
            "unique_threads": 0,
            "db_size_mb": 0.0,
            "oldest": None,
            "newest": None,
        }


def delete_checkpoint_thread(
    thread_id: str,
    db_path: Optional[str | Path] = None,
) -> int:
    """
    Delete all checkpoints for a specific thread.

    Args:
        thread_id: Thread ID to delete
        db_path: Optional database path (uses default if None)

    Returns:
        Number of checkpoints deleted

    Example:
        deleted = delete_checkpoint_thread("research-failed-123")
        logger.info(f"Deleted {deleted} checkpoints for thread")
    """
    if db_path is None:
        db_path = get_checkpoint_db_path()
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        logger.info("No checkpoint database found")
        return 0

    try:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM checkpoints WHERE thread_id = ?",
            (thread_id,)
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Deleted {deleted} checkpoints for thread {thread_id}")

        return deleted

    except Exception as e:
        logger.error(f"Failed to delete checkpoint thread: {e}")
        return 0
