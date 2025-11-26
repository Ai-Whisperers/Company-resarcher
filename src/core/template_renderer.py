"""
Template Rendering Service

Renders Jinja2 templates for generating markdown files.
Ported from AI-powered-marketing-campaign-generator.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, TemplateError, TemplateNotFound
from ..core.logger import setup_logger

logger = setup_logger("template_renderer")


class TemplateRenderer:
    """
    Renders Jinja2 templates for campaign documents.
    """

    def __init__(self, templates_dir: Path | None = None):
        if templates_dir is None:
            # Default to src/templates
            templates_dir = Path(__file__).parent.parent.parent / "src" / "templates"

        self.templates_dir = templates_dir
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,  # Markdown output
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self._env.filters["format_date"] = self._format_date
        self._env.filters["format_number"] = self._format_number

        logger.info(f"Initialized template renderer from: {templates_dir}")

    @staticmethod
    def _format_date(value: datetime | str, format: str = "%d/%m/%Y") -> str:
        """Format a date value."""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime(format)

    @staticmethod
    def _format_number(value: float, decimals: int = 1) -> str:
        """Format a number with specified decimal places."""
        return f"{value:.{decimals}f}"

    def render(self, template_name: str, **context: Any) -> str:
        """
        Render a template with context.
        """
        try:
            template = self._env.get_template(template_name)

            # Add common context
            context["generated_at"] = datetime.utcnow()
            context["generator_version"] = "1.0.0"

            rendered = template.render(**context)
            return rendered

        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            # Fallback for now if template missing
            return f"# Error: Template {template_name} not found\n\nContext: {context}"

        except TemplateError as e:
            logger.error(f"Template error in '{template_name}': {e}")
            return f"# Error rendering {template_name}\n\n{e}"


_renderer = None


def get_template_renderer() -> TemplateRenderer:
    global _renderer
    if _renderer is None:
        _renderer = TemplateRenderer()
    return _renderer
