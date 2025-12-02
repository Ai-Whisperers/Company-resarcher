#!/usr/bin/env python3
"""
Config Validator Script - SCRIPT-004

Validates the .env configuration file:
- Checks for required variables
- Validates API key formats
- Verifies URL formats
- Checks for common misconfigurations

Usage:
    python scripts/validate_config.py           # Validate .env
    python scripts/validate_config.py --fix     # Suggest fixes
    python scripts/validate_config.py --example # Generate example .env
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class ConfigVar:
    """Configuration variable specification."""
    name: str
    required: bool = False
    description: str = ""
    pattern: Optional[str] = None  # Regex pattern for validation
    example: str = ""
    category: str = "general"


# Define expected configuration variables
CONFIG_VARS = [
    # AI Providers
    ConfigVar("OPENAI_API_KEY", required=False, category="ai",
              description="OpenAI API key for GPT models",
              pattern=r"^sk-[a-zA-Z0-9]{32,}$",
              example="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
    ConfigVar("ANTHROPIC_API_KEY", required=False, category="ai",
              description="Anthropic API key for Claude models",
              pattern=r"^sk-ant-[a-zA-Z0-9-]{32,}$",
              example="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
    ConfigVar("GEMINI_API_KEY", required=False, category="ai",
              description="Google Gemini API key",
              pattern=r"^[a-zA-Z0-9_-]{20,}$",
              example="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"),
    ConfigVar("GROQ_API_KEY", required=False, category="ai",
              description="Groq API key for fast inference",
              pattern=r"^gsk_[a-zA-Z0-9]{32,}$",
              example="gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),

    # Search Providers
    ConfigVar("TAVILY_API_KEY", required=False, category="search",
              description="Tavily search API key",
              pattern=r"^tvly-[a-zA-Z0-9]{20,}$",
              example="tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
    ConfigVar("SERPER_API_KEY", required=False, category="search",
              description="Serper search API key",
              pattern=r"^[a-zA-Z0-9]{30,}$",
              example="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),

    # Data Sources
    ConfigVar("NEWS_API_KEY", required=False, category="data",
              description="NewsAPI key for news aggregation",
              pattern=r"^[a-f0-9]{32}$",
              example="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),

    # Observability
    ConfigVar("LANGFUSE_PUBLIC_KEY", required=False, category="observability",
              description="LangFuse public key for LLM observability",
              example="pk-lf-xxxxxxxx"),
    ConfigVar("LANGFUSE_SECRET_KEY", required=False, category="observability",
              description="LangFuse secret key",
              example="sk-lf-xxxxxxxx"),
    ConfigVar("LANGSMITH_API_KEY", required=False, category="observability",
              description="LangSmith API key",
              example="ls__xxxxxxxx"),

    # Database
    ConfigVar("DATABASE_URL", required=False, category="database",
              description="PostgreSQL connection string",
              pattern=r"^postgresql://.*",
              example="postgresql://user:pass@localhost:5432/dbname"),
    ConfigVar("REDIS_URL", required=False, category="database",
              description="Redis connection URL",
              pattern=r"^redis://.*",
              example="redis://localhost:6379/0"),

    # Configuration
    ConfigVar("PRIMARY_AI_PROVIDER", required=False, category="config",
              description="Primary AI provider (openai, anthropic, gemini, groq)",
              pattern=r"^(openai|anthropic|gemini|groq|ollama)$",
              example="anthropic"),
    ConfigVar("FALLBACK_AI_PROVIDER", required=False, category="config",
              description="Fallback AI provider",
              pattern=r"^(openai|anthropic|gemini|groq|ollama)$",
              example="openai"),
    ConfigVar("LOG_LEVEL", required=False, category="config",
              description="Logging level (DEBUG, INFO, WARNING, ERROR)",
              pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
              example="INFO"),
    ConfigVar("LOG_FORMAT", required=False, category="config",
              description="Log format (text, json)",
              pattern=r"^(text|json)$",
              example="text"),
]


@dataclass
class ValidationResult:
    """Result of validating a configuration variable."""
    var: ConfigVar
    present: bool = False
    value: Optional[str] = None
    valid: bool = True
    message: str = ""


def load_env_file(path: Path) -> dict[str, str]:
    """Load and parse .env file."""
    env_vars = {}

    if not path.exists():
        return env_vars

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE
            if "=" in line:
                key, _, value = line.partition("=")
                # Remove quotes from value
                value = value.strip().strip('"').strip("'")
                env_vars[key.strip()] = value

    return env_vars


def validate_config(env_path: Path) -> list[ValidationResult]:
    """Validate configuration file."""
    results = []
    env_vars = load_env_file(env_path)

    # Also check os.environ for variables set externally
    all_vars = {**os.environ, **env_vars}

    for config_var in CONFIG_VARS:
        result = ValidationResult(var=config_var)

        if config_var.name in all_vars:
            result.present = True
            result.value = all_vars[config_var.name]

            # Validate format if pattern specified
            if config_var.pattern and result.value:
                if not re.match(config_var.pattern, result.value):
                    result.valid = False
                    result.message = f"Invalid format (expected: {config_var.pattern})"
                else:
                    result.message = "Valid"
            else:
                result.message = "Set (no format validation)"
        else:
            result.present = False
            if config_var.required:
                result.valid = False
                result.message = "REQUIRED but missing"
            else:
                result.message = "Not set (optional)"

        results.append(result)

    return results


def generate_example_env() -> str:
    """Generate example .env content."""
    lines = [
        "# Company Researcher Configuration",
        "# Generated by scripts/validate_config.py",
        "",
    ]

    current_category = ""
    for var in CONFIG_VARS:
        if var.category != current_category:
            current_category = var.category
            lines.append("")
            lines.append(f"# === {current_category.upper()} ===")

        required = "(REQUIRED)" if var.required else "(optional)"
        lines.append(f"# {var.description} {required}")
        lines.append(f"# {var.name}={var.example}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Company Researcher configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--env-file", "-e",
        type=Path,
        default=PROJECT_ROOT / ".env",
        help="Path to .env file (default: .env)"
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Generate example .env file content"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show suggestions for fixing issues"
    )
    parser.add_argument(
        "--category", "-c",
        choices=["ai", "search", "data", "observability", "database", "config"],
        help="Show only specific category"
    )

    args = parser.parse_args()

    # Generate example mode
    if args.example:
        console.print(Panel(generate_example_env(), title="Example .env"))
        return

    # Validation mode
    console.print(f"\n[bold]Validating:[/bold] {args.env_file}\n")

    if not args.env_file.exists():
        console.print(f"[red]Error: {args.env_file} not found[/red]")
        console.print(f"[dim]Tip: Run with --example to generate a template[/dim]")
        sys.exit(1)

    results = validate_config(args.env_file)

    # Filter by category if specified
    if args.category:
        results = [r for r in results if r.var.category == args.category]

    # Build results table
    table = Table(title="Configuration Validation Results")
    table.add_column("Variable", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Message")

    issues = 0
    warnings = 0
    valid_count = 0

    for result in results:
        if not result.valid:
            status = "[red]ERROR[/red]"
            issues += 1
        elif not result.present:
            status = "[yellow]MISSING[/yellow]"
            warnings += 1
        else:
            status = "[green]OK[/green]"
            valid_count += 1

        table.add_row(
            result.var.name,
            result.var.category,
            status,
            result.message
        )

    console.print(table)
    console.print()

    # Summary
    total = len(results)
    console.print(f"[bold]Summary:[/bold] {valid_count}/{total} valid, {warnings} missing (optional), {issues} errors")

    # Show fixes if requested
    if args.fix and (issues > 0 or warnings > 0):
        console.print("\n[bold]Suggested Fixes:[/bold]")
        for result in results:
            if not result.valid or not result.present:
                console.print(f"  [cyan]{result.var.name}[/cyan]={result.var.example}")
                console.print(f"  [dim]  # {result.var.description}[/dim]")

    if issues > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
