#!/usr/bin/env python3
"""
Script to fix all relative imports (from ..) in Python files to use absolute imports.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

def get_absolute_import(file_path: str, relative_import: str) -> str:
    """
    Convert a relative import to an absolute import based on the file's location.

    Args:
        file_path: Full path to the Python file
        relative_import: The relative import statement (e.g., "from ..core.logging import setup_logger")

    Returns:
        The absolute import statement
    """
    # Get the directory of the file
    file_dir = Path(file_path).parent

    # Extract the dots and the module path from the import
    match = re.match(r'^from (\.+)(.*)$', relative_import)
    if not match:
        return relative_import

    dots, module_suffix = match.groups()
    num_dots = len(dots)

    # Go up the directory tree based on number of dots
    # One dot means current directory, two dots means parent, etc.
    current_path = file_dir
    for _ in range(num_dots - 1):  # -1 because one dot is the current package
        current_path = current_path.parent

    # Find the src directory in the path
    parts = list(current_path.parts)
    try:
        src_idx = parts.index('src')
        # Build absolute import from src
        absolute_parts = parts[src_idx + 1:]  # Everything after 'src'

        if module_suffix.strip():
            absolute_import_path = '.'.join(absolute_parts + [module_suffix.strip()])
        else:
            absolute_import_path = '.'.join(absolute_parts)

        # Clean up any leading dots
        absolute_import_path = absolute_import_path.lstrip('.')

        return f"from src.{absolute_import_path}" if absolute_import_path else relative_import
    except (ValueError, IndexError):
        return relative_import

def fix_file_imports(file_path: str) -> Tuple[int, List[str]]:
    """
    Fix all relative imports in a single file.

    Returns:
        Tuple of (number of replacements, list of changes made)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, []

    lines = content.split('\n')
    changes = []
    replacements = 0

    new_lines = []
    for line in lines:
        # Match lines that start with "from .." (relative imports)
        if re.match(r'^\s*from \.\.', line):
            # Extract the import statement
            stripped = line.lstrip()
            indent = line[:len(line) - len(stripped)]

            # Get the absolute import
            absolute_import = get_absolute_import(file_path, stripped)

            if absolute_import != stripped and absolute_import.startswith('from src.'):
                new_line = indent + absolute_import
                new_lines.append(new_line)
                changes.append(f"  {stripped} -> {absolute_import}")
                replacements += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Write back if changes were made
    if replacements > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return 0, []

    return replacements, changes

def main():
    """Main function to process all Python files."""
    src_dir = Path('src')

    if not src_dir.exists():
        print("Error: 'src' directory not found")
        return

    print("Scanning for Python files with relative imports...")
    print("=" * 80)

    total_files = 0
    total_replacements = 0

    # Find all Python files in src directory
    for py_file in src_dir.rglob('*.py'):
        replacements, changes = fix_file_imports(str(py_file))

        if replacements > 0:
            total_files += 1
            total_replacements += replacements
            print(f"\n{py_file} ({replacements} replacements):")
            for change in changes[:5]:  # Show first 5 changes
                print(change)
            if len(changes) > 5:
                print(f"  ... and {len(changes) - 5} more")

    print("\n" + "=" * 80)
    print(f"\nSummary:")
    print(f"  Files modified: {total_files}")
    print(f"  Total replacements: {total_replacements}")
    print("\nDone!")

if __name__ == "__main__":
    main()
