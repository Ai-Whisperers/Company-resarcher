"""
CLI commands for managing research checkpoints.

Provides commands to:
- Resume interrupted research from checkpoints
- List available checkpoints
- Clean up old checkpoints
- View checkpoint statistics
"""

import asyncio
from pathlib import Path
from typing import Optional

from src.core.logging import setup_logger
from src.graph.checkpointer import (
    get_checkpointer,
    list_checkpoints,
    cleanup_old_checkpoints,
    get_checkpoint_stats,
    delete_checkpoint_thread,
)
from src.graph.research_graph import resume_research, get_research_status

logger = setup_logger("cli.checkpoint")


async def resume_research_command(
    thread_id: str,
    human_feedback: Optional[str] = None,
) -> None:
    """
    Resume an interrupted research workflow from checkpoint.

    Args:
        thread_id: Thread ID of the interrupted workflow
        human_feedback: Optional human feedback to inject
    """
    logger.info(f"Resuming research from checkpoint: {thread_id}")

    try:
        # Check if checkpointing is enabled
        checkpointer = get_checkpointer()
        if checkpointer is None:
            logger.error("Checkpointing is disabled. Cannot resume research.")
            logger.info("Enable checkpointing in .env: GRAPH__ENABLE_CHECKPOINTING=true")
            return

        # Get current status
        status = await get_research_status(thread_id)
        if status is None:
            logger.error(f"No checkpoint found for thread ID: {thread_id}")
            logger.info("Use --list-checkpoints to see available threads")
            return

        logger.info(f"Found checkpoint - Phase: {status.get('phase')}")
        logger.info(f"Quality Score: {status.get('quality_score', 'N/A')}")
        logger.info(f"Has Report: {status.get('has_report', False)}")

        # Resume execution
        result = await resume_research(
            thread_id=thread_id,
            human_feedback=human_feedback,
        )

        logger.info("Research resumed successfully!")

        # Print summary
        if result:
            final_phase = result.get("phase", "unknown")
            final_score = result.get("quality_score", 0)
            has_report = result.get("report") is not None

            logger.info(f"Final Phase: {final_phase}")
            logger.info(f"Final Quality Score: {final_score}")
            logger.info(f"Report Generated: {has_report}")

    except Exception as e:
        logger.error(f"Failed to resume research: {e}")
        raise


def list_checkpoints_command(limit: int = 20) -> None:
    """
    List available research checkpoints.

    Args:
        limit: Maximum number of checkpoints to display
    """
    logger.info("Listing available checkpoints...")

    try:
        checkpoints = list_checkpoints(limit=limit)

        if not checkpoints:
            logger.info("No checkpoints found")
            logger.info("Checkpoints are created when research is interrupted or paused")
            return

        logger.info(f"\nFound {len(checkpoints)} checkpoints:\n")

        # Group by thread_id
        threads = {}
        for cp in checkpoints:
            thread_id = cp["thread_id"]
            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(cp)

        # Print grouped by thread
        for thread_id, thread_checkpoints in threads.items():
            logger.info(f"Thread: {thread_id}")
            logger.info(f"  Checkpoints: {len(thread_checkpoints)}")

            latest = thread_checkpoints[0]  # Already sorted by created_at DESC
            logger.info(f"  Latest: {latest['created_at']}")
            logger.info(f"  Checkpoint ID: {latest['checkpoint_id']}")
            logger.info("")

        logger.info(f"Use --resume <thread_id> to continue research")

    except Exception as e:
        logger.error(f"Failed to list checkpoints: {e}")
        raise


def cleanup_checkpoints_command(max_age_days: int = 30) -> None:
    """
    Clean up old checkpoints from database.

    Args:
        max_age_days: Maximum age of checkpoints to keep
    """
    logger.info(f"Cleaning up checkpoints older than {max_age_days} days...")

    try:
        deleted = cleanup_old_checkpoints(max_age_days=max_age_days)

        if deleted > 0:
            logger.info(f"Successfully deleted {deleted} old checkpoints")
        else:
            logger.info("No old checkpoints to clean")

    except Exception as e:
        logger.error(f"Failed to clean up checkpoints: {e}")
        raise


def checkpoint_stats_command() -> None:
    """
    Display checkpoint database statistics.
    """
    logger.info("Fetching checkpoint statistics...")

    try:
        stats = get_checkpoint_stats()

        if stats["total_checkpoints"] == 0:
            logger.info("No checkpoints in database")
            return

        logger.info("\nCheckpoint Database Statistics:")
        logger.info(f"  Total Checkpoints: {stats['total_checkpoints']}")
        logger.info(f"  Unique Threads: {stats['unique_threads']}")
        logger.info(f"  Database Size: {stats['db_size_mb']} MB")

        if stats["oldest"]:
            logger.info(f"  Oldest Checkpoint: {stats['oldest']}")
        if stats["newest"]:
            logger.info(f"  Newest Checkpoint: {stats['newest']}")

    except Exception as e:
        logger.error(f"Failed to get checkpoint stats: {e}")
        raise


def delete_thread_command(thread_id: str) -> None:
    """
    Delete all checkpoints for a specific thread.

    Args:
        thread_id: Thread ID to delete
    """
    logger.info(f"Deleting checkpoints for thread: {thread_id}")

    try:
        deleted = delete_checkpoint_thread(thread_id)

        if deleted > 0:
            logger.info(f"Successfully deleted {deleted} checkpoints")
        else:
            logger.info("No checkpoints found for this thread")

    except Exception as e:
        logger.error(f"Failed to delete thread checkpoints: {e}")
        raise
