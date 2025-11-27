"""
Output Manager - Handles the organization and saving of research outputs.
"""

import os
from typing import Dict
from .logger import setup_logger

logger = setup_logger("output_manager")


class OutputManager:
    """
    Manages the file system operations for saving research outputs
    in a structured format.
    """

    def __init__(self, base_output_dir: str = "outputs"):
        self.base_output_dir = base_output_dir

    def save_research_output(self, company_name: str, drafts: Dict[str, str]):
        """
        Save the research drafts to the file system using the keys as relative paths.

        Args:
            company_name: Name of the company (used for root folder)
            drafts: Dictionary where key is relative path (e.g. '01-Context/01-Overview.md')
                    and value is the file content.
        """
        company_dir = os.path.join(self.base_output_dir, company_name)

        # Create company root directory
        os.makedirs(company_dir, exist_ok=True)
        logger.info(f"Saving research output to: {company_dir}")

        for relative_path, content in drafts.items():
            # Construct full path
            full_path = os.path.join(company_dir, relative_path)

            # Create subdirectories if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write file
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.debug(f"Saved: {relative_path}")
            except Exception as e:
                logger.error(f"Failed to save {relative_path}: {e}")

        logger.info("All research outputs saved successfully.")
