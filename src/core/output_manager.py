"""
Output Manager - Handles the organization and saving of research outputs.
"""

from pathlib import Path
from typing import Dict
from .logger import setup_logger

logger = setup_logger("output_manager")


class PathTraversalError(ValueError):
    """Raised when a path traversal attack is detected."""
    pass


class OutputManager:
    """
    Manages the file system operations for saving research outputs
    in a structured format.

    Security: Validates all paths to prevent directory traversal attacks.
    """

    def __init__(self, base_output_dir: str = "outputs"):
        self.base_output_dir = Path(base_output_dir).resolve()

    def _validate_path(self, base_dir: Path, target_path: Path) -> Path:
        """
        Validate that target_path is within base_dir to prevent path traversal.

        Args:
            base_dir: The allowed base directory (resolved to absolute)
            target_path: The target path to validate

        Returns:
            The validated absolute path

        Raises:
            PathTraversalError: If path would escape the base directory
        """
        # Resolve to absolute path
        resolved_path = target_path.resolve()

        # Check if the resolved path starts with the base directory
        try:
            resolved_path.relative_to(base_dir)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal detected: '{target_path}' escapes base directory"
            )

        return resolved_path

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a filename/dirname to remove dangerous characters.

        Args:
            name: The name to sanitize

        Returns:
            Sanitized name safe for filesystem use
        """
        # Remove or replace dangerous characters
        dangerous_chars = ['..', '\x00', ':', '*', '?', '"', '<', '>', '|']
        sanitized = name
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized.strip()

    def save_research_output(self, company_name: str, drafts: Dict[str, str]):
        """
        Save the research drafts to the file system using the keys as relative paths.

        Args:
            company_name: Name of the company (used for root folder)
            drafts: Dictionary where key is relative path (e.g. '01-Context/01-Overview.md')
                    and value is the file content.

        Raises:
            PathTraversalError: If any path would escape the output directory
        """
        # Sanitize company name to prevent traversal via company_name
        safe_company_name = self._sanitize_filename(company_name)
        company_dir = (self.base_output_dir / safe_company_name).resolve()

        # Validate company_dir is within base_output_dir
        self._validate_path(self.base_output_dir, company_dir)

        # Create company root directory
        company_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving research output to: {company_dir}")

        for relative_path, content in drafts.items():
            # Construct and validate full path
            target_path = company_dir / relative_path

            try:
                # Validate path doesn't escape company_dir
                validated_path = self._validate_path(company_dir, target_path)

                # Create subdirectories if needed
                validated_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                validated_path.write_text(content, encoding="utf-8")
                logger.debug(f"Saved: {relative_path}")

            except PathTraversalError as e:
                logger.error(f"Security error for {relative_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to save {relative_path}: {e}")

        logger.info("All research outputs saved successfully.")
