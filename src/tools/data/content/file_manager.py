import aiofiles
from pathlib import Path
from typing import List, Dict, Any
from src.core.config import get_settings
from src.core.logging import setup_logger
from src.core.types import ResearchPhaseResult

logger = setup_logger("file_manager")
settings = get_settings()


class FileManager:
    """
    Handles file system operations: creating folders, saving reports, and logging sources.
    """

    def __init__(self, base_output_dir: Path = None):
        self.output_dir = base_output_dir or settings.OUTPUT_DIR

    def setup_company_folder(self, company_name: str) -> Path:
        """
        Creates the standard folder structure for a company.
        """
        safe_name = "".join(
            x for x in company_name if x.isalnum() or x in (" ", "-", "_")
        ).strip()
        company_dir = self.output_dir / safe_name

        # Base folders
        folders = [
            "00-Strategic-Context",
            "01-Market-Intelligence",
            "02-Target-Audience",
            "03-Competitive-Landscape",
            "04-Brand-Strategy",
            "05-Marketing-Execution",
            "06-Data-Room",
            "07-Creative-Inspiration",
            "99-Sources",
            "99-Sources/raw",
        ]

        for folder in folders:
            (company_dir / folder).mkdir(parents=True, exist_ok=True)

        logger.info(f"Created folder structure for {company_name} at {company_dir}")
        return company_dir

    async def save_report(self, company_name: str, result: ResearchPhaseResult):
        """
        Saves a research phase result to the appropriate file.
        """
        company_dir = self.setup_company_folder(company_name)

        # phase_id is now like "00-Strategic-Context/01-Company-Overview"
        # We want to save to "00-Strategic-Context/01-Company-Overview.md"

        if "/" in result.phase_name:
            # It's a sub-phase, so it already contains the folder structure
            relative_path = f"{result.phase_name}.md"
        else:
            # Fallback for old style or top-level phases
            relative_path = f"{result.phase_name}/{result.phase_name}.md"

        await self.save_markdown_report(
            company_dir, relative_path, result.markdown_content
        )

        # Save raw sources
        await self.save_source_data(company_dir, result.sources)

    async def save_markdown_report(
        self, company_dir: Path, relative_path: str, content: str
    ):
        """
        Saves a markdown report to the specified path.
        """
        file_path = company_dir / relative_path
        # Ensure parent dir exists (in case of deep nesting)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        logger.info(f"Saved report: {relative_path}")

    async def save_source_data(self, company_dir: Path, sources: List[Any]):
        """
        Saves raw source data to the 99-Sources/raw folder.
        """
        raw_dir = company_dir / "99-Sources" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        for i, source in enumerate(sources):
            # Create a safe filename from the title
            safe_title = "".join(
                x for x in source.title if x.isalnum() or x in (" ", "-", "_")
            ).strip()[
                :50
            ]  # Limit length

            filename = f"Source-{i:03d}-{safe_title}.md"
            file_path = raw_dir / filename

            # Add the raw file path to the source object for logging
            source.raw_file_path = str(file_path)

            content = f"""# Source: {source.title}
URL: {source.url}
Accessed: {source.accessed_at}
Type: {source.source_type}

## Content
{source.content}
"""
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

        logger.info(f"Saved {len(sources)} raw sources")

        # Save source log
        # Convert Source objects to dicts for logging
        source_dicts = []
        for i, s in enumerate(sources):
            source_dicts.append(
                {
                    "id": f"{i:03d}",
                    "title": s.title,
                    "url": s.url,
                    "date": s.accessed_at,
                    "type": s.source_type,
                    "raw_file_path": getattr(s, "raw_file_path", ""),
                }
            )

        await self.save_source_log(company_dir, source_dicts)

    async def save_source_log(self, company_dir: Path, sources: List[Dict[str, Any]]):
        """Saves a log of all sources used in the research as a Markdown file."""
        log_path = company_dir / "99-Sources" / "Source-Log.md"

        # Create header if file doesn't exist
        if not log_path.exists():
            async with aiofiles.open(log_path, "w", encoding="utf-8") as f:
                await f.write(f"# Source Log\n\n")
                await f.write("| ID | Title | URL | Date | Type | Raw File |\n")
                await f.write("|----|-------|-----|------|------|----------|\n")

        # Append new sources
        async with aiofiles.open(log_path, "a", encoding="utf-8") as f:
            for source in sources:
                # Create a relative link to the raw file if it exists
                raw_file_link = "N/A"
                if source.get("raw_file_path"):
                    # Source-Log.md is in 99-Sources/
                    # Raw files are in 99-Sources/raw/
                    # So relative path is raw/<filename>
                    raw_path = Path(source["raw_file_path"])
                    raw_file_link = f"[View](raw/{raw_path.name})"

                title = source.get("title", "Unknown").replace("|", "-")
                url = source.get("url", "N/A")
                date = source.get("date", "N/A")
                type_ = source.get("type", "N/A")

                await f.write(
                    f"| {source.get('id', 'N/A')} | {title} | {url} | {date} | {type_} | {raw_file_link} |\n"
                )

        logger.info(f"Updated source log with {len(sources)} entries")
