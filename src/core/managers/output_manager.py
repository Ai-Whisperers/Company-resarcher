"""
Output Manager - Handles the organization and saving of research outputs.

Security Features:
- Strict path validation to prevent directory traversal attacks
- Company name sanitization (alphanumeric + limited safe characters)
- Relative path validation in drafts dictionary
- Symlink detection and prevention
- Null byte injection prevention
"""

import re
from pathlib import Path
from typing import Dict
from ..logging import setup_logger

logger = setup_logger("output_manager")

# Maximum allowed path component length
MAX_PATH_COMPONENT_LENGTH = 255

# Allowed characters in company names and path components
# Alphanumeric, spaces, hyphens, underscores, and periods
SAFE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\s\-_.]*$')

# Dangerous path patterns to detect
DANGEROUS_PATH_PATTERNS = [
    r'\.\.[\\/]',  # Parent directory traversal
    r'^\.\.',  # Starts with parent directory
    r'[\\/]\.\.',  # Contains parent directory
    r'\x00',  # Null byte injection
    r'[\\/]\.[\\/]',  # Current directory in path
]


class PathTraversalError(ValueError):
    """Raised when a path traversal attack is detected."""

    def __init__(self, message: str, attempted_path: str = ""):
        self.attempted_path = attempted_path
        super().__init__(message)


class InvalidPathError(ValueError):
    """Raised when a path contains invalid or dangerous characters."""

    def __init__(self, message: str, invalid_value: str = ""):
        self.invalid_value = invalid_value
        super().__init__(message)


class OutputManager:
    """
    Manages the file system operations for saving research outputs
    in a structured format.

    Security Features:
    - Validates all paths to prevent directory traversal attacks
    - Sanitizes company names to alphanumeric + limited safe characters
    - Detects and prevents symlink attacks
    - Blocks null byte injection and other path manipulation attacks
    """

    def __init__(self, base_output_dir: str = "outputs"):
        self.base_output_dir = Path(base_output_dir).resolve()
        # Compile dangerous patterns for efficiency
        self._dangerous_patterns = [
            re.compile(p) for p in DANGEROUS_PATH_PATTERNS
        ]

    def _validate_path(self, base_dir: Path, target_path: Path) -> Path:
        """
        Validate that target_path is within base_dir to prevent path traversal.

        Security checks performed:
        1. Resolve to absolute path (follows symlinks)
        2. Verify resolved path is under base_dir
        3. Check for symlinks pointing outside base_dir
        4. Detect dangerous path patterns

        Args:
            base_dir: The allowed base directory (resolved to absolute)
            target_path: The target path to validate

        Returns:
            The validated absolute path

        Raises:
            PathTraversalError: If path would escape the base directory
        """
        # Convert to string for pattern checking
        path_str = str(target_path)

        # Check for dangerous patterns in the original path
        for pattern in self._dangerous_patterns:
            if pattern.search(path_str):
                raise PathTraversalError(
                    f"Dangerous path pattern detected in: '{target_path}'",
                    attempted_path=path_str
                )

        # Resolve to absolute path (this follows symlinks)
        try:
            resolved_path = target_path.resolve()
        except (OSError, ValueError) as e:
            raise PathTraversalError(
                f"Cannot resolve path '{target_path}': {e}",
                attempted_path=path_str
            )

        # Check if the resolved path starts with the base directory
        try:
            resolved_path.relative_to(base_dir)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal detected: '{target_path}' escapes base directory '{base_dir}'",
                attempted_path=path_str
            )

        # Additional check: if target_path exists, ensure it's not a symlink to outside
        if target_path.exists() and target_path.is_symlink():
            link_target = target_path.resolve()
            try:
                link_target.relative_to(base_dir)
            except ValueError:
                raise PathTraversalError(
                    f"Symlink escape detected: '{target_path}' points outside base directory",
                    attempted_path=path_str
                )

        return resolved_path

    def _sanitize_company_name(self, name: str) -> str:
        """
        Strictly sanitize a company name for use as a directory name.

        Security measures:
        - Only allows alphanumeric, spaces, hyphens, underscores, periods
        - Replaces any other characters with underscores
        - Strips leading/trailing whitespace
        - Enforces maximum length
        - Prevents reserved names (Windows)

        Args:
            name: The company name to sanitize

        Returns:
            Sanitized name safe for filesystem use

        Raises:
            InvalidPathError: If name is empty or cannot be sanitized
        """
        if not name or not name.strip():
            raise InvalidPathError("Company name cannot be empty", name)

        # Remove null bytes and control characters
        sanitized = name.replace('\x00', '').strip()
        sanitized = ''.join(c for c in sanitized if ord(c) >= 32)

        # Replace any character that's not alphanumeric, space, hyphen, underscore, or period
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_.]', '_', sanitized)

        # Replace multiple consecutive underscores/spaces with single underscore
        sanitized = re.sub(r'[\s_]+', '_', sanitized)

        # Remove leading/trailing underscores and periods
        sanitized = sanitized.strip('_.')

        # Enforce maximum length
        if len(sanitized) > MAX_PATH_COMPONENT_LENGTH:
            sanitized = sanitized[:MAX_PATH_COMPONENT_LENGTH].rstrip('_.')

        # Check for Windows reserved names
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
        }
        if sanitized.upper() in reserved_names:
            sanitized = f"_{sanitized}_"

        if not sanitized:
            raise InvalidPathError(
                f"Company name '{name}' cannot be sanitized to a valid name",
                name
            )

        return sanitized

    def _sanitize_relative_path(self, rel_path: str) -> str:
        """
        Sanitize a relative file path within the output directory.

        Args:
            rel_path: The relative path to sanitize (e.g., '01-Context/01-Overview.md')

        Returns:
            Sanitized relative path

        Raises:
            InvalidPathError: If path is invalid or dangerous
        """
        if not rel_path or not rel_path.strip():
            raise InvalidPathError("Relative path cannot be empty", rel_path)

        # Check for null bytes
        if '\x00' in rel_path:
            raise InvalidPathError("Null byte detected in path", rel_path)

        # Check for dangerous patterns
        for pattern in self._dangerous_patterns:
            if pattern.search(rel_path):
                raise InvalidPathError(
                    f"Dangerous pattern detected in relative path",
                    rel_path
                )

        # Split into components and sanitize each
        # Use os.path to handle both / and \ separators
        parts = Path(rel_path).parts

        sanitized_parts = []
        for part in parts:
            # Remove dangerous characters
            sanitized = re.sub(r'[<>:"|?*\x00]', '_', part)
            # Don't allow parts that are just dots
            if sanitized in ('.', '..'):
                raise InvalidPathError(
                    f"Invalid path component '{part}'",
                    rel_path
                )
            sanitized_parts.append(sanitized)

        return str(Path(*sanitized_parts)) if sanitized_parts else ""

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a filename/dirname to remove dangerous characters.

        Args:
            name: The name to sanitize

        Returns:
            Sanitized name safe for filesystem use
        """
        # Use the more robust company name sanitization
        return self._sanitize_company_name(name)

    def save_research_output(self, company_name: str, drafts: Dict[str, str]):
        """
        Save the research drafts to the file system using the keys as relative paths.

        Args:
            company_name: Name of the company (used for root folder)
            drafts: Dictionary where key is relative path (e.g. '01-Context/01-Overview.md')
                    and value is the file content.

        Raises:
            PathTraversalError: If any path would escape the output directory
            InvalidPathError: If company name or path contains invalid characters
        """
        # Sanitize company name using strict sanitization
        try:
            safe_company_name = self._sanitize_company_name(company_name)
        except InvalidPathError as e:
            logger.error(f"Invalid company name: {e}")
            raise

        company_dir = (self.base_output_dir / safe_company_name).resolve()

        # Validate company_dir is within base_output_dir
        self._validate_path(self.base_output_dir, company_dir)

        # Create company root directory
        company_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving research output to: {company_dir}")

        saved_count = 0
        error_count = 0

        for relative_path, content in drafts.items():
            try:
                # Sanitize the relative path first
                safe_relative_path = self._sanitize_relative_path(relative_path)

                # Construct and validate full path
                target_path = company_dir / safe_relative_path

                # Validate path doesn't escape company_dir
                validated_path = self._validate_path(company_dir, target_path)

                # Create subdirectories if needed
                validated_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                validated_path.write_text(content, encoding="utf-8")
                logger.debug(f"Saved: {safe_relative_path}")
                saved_count += 1

            except (PathTraversalError, InvalidPathError) as e:
                logger.error(f"Security error for {relative_path}: {e}")
                error_count += 1
                raise
            except OSError as e:
                logger.error(f"OS error saving {relative_path}: {e}")
                error_count += 1
            except Exception as e:
                logger.error(f"Unexpected error saving {relative_path}: {e}")
                error_count += 1

        if error_count > 0:
            logger.warning(f"Completed with {error_count} errors. Saved {saved_count} files.")
        else:
            logger.info(f"All {saved_count} research outputs saved successfully.")
