import asyncio
import os
import sys
import argparse
import json
import shutil
import re
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to sys.path to allow imports from src
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from src.infrastructure.ai.ai_client import get_ai_manager
from src.core.logging import setup_logger
from src.infrastructure.security.sandbox import DockerSandbox

logger = setup_logger("code_reviewer")


class CodeReviewer:
    def __init__(self):
        self.ai_manager = get_ai_manager()
        self.prompt_path = project_root / "src" / "prompts" / "code_review_prompt.md"
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"System prompt not found at {self.prompt_path}")
            return "You are a code reviewer."

    def should_ignore(self, path: Path, ignore_patterns: List[str]) -> bool:
        """Checks if a path matches any ignore patterns."""
        for pattern in ignore_patterns:
            if path.match(pattern) or any(p.match(pattern) for p in path.parents):
                return True
        return False

    def _extract_code_block(self, response: str, extension: str) -> str | None:
        """Extracts the last code block from the response."""
        # Regex to find code blocks with or without language identifier
        # Matches ```(optional_lang)\n(content)```
        pattern = r"```\w*\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[-1].strip()

        return None

    def verify_fix(self, file_path: Path, code_content: str) -> bool:
        """
        Verifies the fixed code by running it in a Docker sandbox.
        Only supports Python files for now.
        """
        if file_path.suffix != ".py":
            logger.info(f"Skipping verification for non-python file: {file_path}")
            return True  # Assume valid if not python

        try:
            logger.info(f"Verifying fix for {file_path} in sandbox...")
            with DockerSandbox() as sandbox:
                # Copy file to sandbox
                container_path = f"/workspace/{file_path.name}"
                sandbox.copy_to_container(code_content, container_path)

                # Run syntax check first
                exit_code, stdout, stderr = sandbox.execute(
                    f"python -m py_compile {container_path}"
                )
                if exit_code != 0:
                    logger.warning(f"Verification failed (Syntax Error): {stderr}")
                    return False

                # Optionally run the script if safe?
                # For now, just syntax check is safer than running arbitrary code.
                # If we had a test suite, we would run that.
                logger.info(f"Verification passed for {file_path}")
                return True
        except Exception as e:
            logger.error(f"Sandbox verification error: {e}")
            return False  # Fail safe

    async def review_file(
        self, file_path: Path, auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        Reviews a specific file using the AI client.
        Returns a dictionary with the review result.
        """
        if not file_path.exists():
            return {"file": str(file_path), "error": "File not found"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            return {"file": str(file_path), "error": f"Error reading file: {e}"}

        user_prompt = f"Please review the following code file: {file_path.name}\n\n```\n{code_content}\n```"
        if auto_fix:
            user_prompt += "\n\nIMPORTANT: Please FIX the code issues found and provide the complete, corrected code at the end of your response."

        logger.info(f"Starting review for {file_path} (Fix: {auto_fix})...")
        try:
            response = await self.ai_manager.generate(
                prompt=user_prompt, system=self.system_prompt, task_type="smart"
            )

            result = {"file": str(file_path), "review": response}

            if auto_fix:
                fixed_code = self._extract_code_block(response, file_path.suffix)
                if fixed_code:
                    # Verify fix in sandbox
                    if self.verify_fix(file_path, fixed_code):
                        # Create backup
                        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                        shutil.copy2(file_path, backup_path)

                        # Write fixed code
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(fixed_code)

                        result["fixed"] = True
                        result["backup"] = str(backup_path)
                        logger.info(
                            f"Applied fix to {file_path}. Backup saved to {backup_path}"
                        )
                    else:
                        result["fixed"] = False
                        result["error"] = "Verification failed in sandbox."
                        logger.warning(f"Verification failed for {file_path}")
                else:
                    result["fixed"] = False
                    result["error"] = "Could not extract fixed code from response."
                    logger.warning(f"Could not extract fixed code for {file_path}")

            return result
        except Exception as e:
            logger.error(f"Error during AI generation for {file_path}: {e}")
            return {"file": str(file_path), "error": f"Failed to generate review: {e}"}

    async def scan_directory(
        self,
        dir_path: Path,
        ignore_patterns: List[str],
        auto_fix: bool = False,
        extensions: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recursively scans a directory and reviews matching files."""
        results = []
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".html", ".css", ".md"]

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [
                d
                for d in dirs
                if not self.should_ignore(Path(root) / d, ignore_patterns)
            ]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix not in extensions:
                    continue

                if self.should_ignore(file_path, ignore_patterns):
                    continue

                result = await self.review_file(file_path, auto_fix=auto_fix)
                results.append(result)

        return results


async def main():
    parser = argparse.ArgumentParser(description="Automated Code Review Tool")
    parser.add_argument("path", help="Path to file or directory to review")
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--ignore",
        nargs="+",
        default=[],
        help="List of patterns to ignore (e.g., *.pyc __pycache__)",
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to automatically fix issues"
    )

    args = parser.parse_args()

    target_path = Path(args.path)
    reviewer = CodeReviewer()

    # Default ignore patterns
    ignore_patterns = args.ignore + [
        "__pycache__",
        ".git",
        ".venv",
        "node_modules",
        "*.pyc",
    ]

    results = []

    if target_path.is_file():
        print(f"Reviewing file: {target_path}")
        results.append(await reviewer.review_file(target_path, auto_fix=args.fix))
    elif target_path.is_dir():
        print(f"Scanning directory: {target_path}")
        results = await reviewer.scan_directory(
            target_path, ignore_patterns, auto_fix=args.fix
        )
    else:
        print(f"Error: Path {target_path} does not exist.")
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for res in results:
            print(f"\n{'='*80}")
            print(f"FILE: {res['file']}")
            print(f"{'='*80}")
            if "error" in res:
                print(f"ERROR: {res['error']}")
            else:
                print(res["review"])
                if res.get("fixed"):
                    print(f"\n[SUCCESS] Fixed code applied. Backup: {res['backup']}")
                elif args.fix and not res.get("fixed"):
                    print(f"\n[WARNING] Failed to apply fix.")


if __name__ == "__main__":
    asyncio.run(main())
