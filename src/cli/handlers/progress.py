from src.core.logging.progress import ResearchProgress, ResearchStage
from src.lib.tracking.cost_tracker import get_cost_tracker


def create_cli_progress_callback(run_id: str, registry):
    """
    Create a callback that syncs progress updates to the CLI registry.

    Args:
        run_id: The CLI run ID to update
        registry: The CLI run registry instance
    """

    def progress_callback(progress: ResearchProgress):
        # Map ResearchStage to dashboard stages
        stage_map = {
            ResearchStage.INITIALIZING: "init",
            ResearchStage.GENERATING_QUERIES: "gathering",
            ResearchStage.SEARCHING: "gathering",
            ResearchStage.FETCHING_CONTENT: "gathering",
            ResearchStage.ANALYZING: "thinking",
            ResearchStage.SYNTHESIZING: "thinking",
            ResearchStage.WRITING: "writing",
            ResearchStage.REVIEWING: "review",
            ResearchStage.COMPLETE: "complete",
            ResearchStage.ERROR: "init",
        }

        dashboard_stage = stage_map.get(progress.current_stage, "init")

        registry.update_progress(
            run_id=run_id,
            stage=dashboard_stage,
            overall=progress.overall_progress,
            activity=progress.current_activity
            or f"Processing: {progress.current_stage.value}",
            elapsed_seconds=progress.elapsed_time,
            queries_completed=progress.completed_queries,
            queries_total=progress.total_queries,
            sources_processed=progress.processed_sources,
            sources_total=progress.total_sources,
            errors=progress.errors if progress.errors else None,
        )

        # Also sync cost data from the cost tracker
        try:
            cost_tracker = get_cost_tracker()
            summary = cost_tracker.get_summary()
            registry.update_cost(
                run_id=run_id,
                total=summary.total_cost,
                budget_limit=cost_tracker.budget_limit,
                input_tokens=summary.total_input_tokens,
                output_tokens=summary.total_output_tokens,
                api_calls=summary.calls_count,
            )
        except Exception:
            pass  # Non-fatal if cost sync fails

    return progress_callback
