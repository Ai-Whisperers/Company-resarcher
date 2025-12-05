"""
Chart Generator Tool for creating visualizations from financial/research data.

Supports multiple chart types:
- Line charts (time series, trends)
- Bar charts (comparisons)
- Pie charts (market share, distributions)
- Area charts (cumulative data)
- Scatter plots (correlations)

Usage:
    from src.tools.specialized.chart import ChartGeneratorTool

    tool = ChartGeneratorTool(output_dir="./outputs/charts")

    # From JSON data
    chart_path = tool.generate_line_chart(
        data={"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [100, 120, 115, 140]},
        title="Quarterly Revenue",
        filename="revenue_chart"
    )

    # From dict with multiple series
    chart_path = tool.generate_multi_line_chart(
        data={
            "labels": ["2020", "2021", "2022", "2023"],
            "series": {
                "Company A": [100, 110, 125, 140],
                "Company B": [90, 95, 105, 120],
            }
        },
        title="Revenue Comparison",
        filename="comparison_chart"
    )
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from src.core.logging import setup_logger

logger = setup_logger("chart_tool")

# Type aliases
ChartFormat = Literal["png", "svg", "pdf"]
ChartType = Literal["line", "bar", "pie", "area", "scatter", "horizontal_bar"]


class ChartGeneratorTool:
    """
    Tool for generating charts and visualizations from research data.

    Uses matplotlib as the primary backend with optional plotly support
    for interactive charts.
    """

    def __init__(
        self,
        output_dir: str = "./outputs/charts",
        default_format: ChartFormat = "png",
        dpi: int = 150,
        style: str = "seaborn-v0_8-whitegrid",
    ):
        """
        Initialize the chart generator.

        Args:
            output_dir: Directory to save generated charts
            default_format: Default output format (png, svg, pdf)
            dpi: Resolution for raster formats
            style: Matplotlib style to use
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.default_format = default_format
        self.dpi = dpi
        self.style = style

        # Color palette for consistent styling
        self.colors = [
            "#2E86AB",  # Blue
            "#A23B72",  # Magenta
            "#F18F01",  # Orange
            "#C73E1D",  # Red
            "#3B1F2B",  # Dark
            "#95C623",  # Green
            "#7B68EE",  # Medium Slate Blue
            "#20B2AA",  # Light Sea Green
        ]

    def _get_matplotlib(self):
        """Lazy import matplotlib to avoid import errors if not installed."""
        try:
            import matplotlib

            matplotlib.use("Agg")  # Non-interactive backend
            import matplotlib.pyplot as plt

            return plt
        except ImportError:
            raise ImportError(
                "matplotlib is required for chart generation. "
                "Install with: pip install matplotlib"
            )

    def _apply_style(self, plt):
        """Apply consistent styling to charts."""
        try:
            plt.style.use(self.style)
        except OSError:
            # Fallback if style not available
            plt.style.use("ggplot")

    def _generate_filename(
        self,
        base_name: str,
        chart_type: str,
        fmt: ChartFormat,
    ) -> Path:
        """Generate a unique filename for the chart."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{chart_type}_{timestamp}.{fmt}"
        return self.output_dir / filename

    def generate_line_chart(
        self,
        data: Dict[str, Any],
        title: str = "Line Chart",
        filename: str = "line_chart",
        x_label: str = "",
        y_label: str = "",
        fmt: Optional[ChartFormat] = None,
        figsize: tuple = (10, 6),
    ) -> str:
        """
        Generate a line chart from data.

        Args:
            data: Dict with "labels" (x-axis) and "values" (y-axis) keys
            title: Chart title
            filename: Base filename (without extension)
            x_label: X-axis label
            y_label: Y-axis label
            fmt: Output format (overrides default)
            figsize: Figure size in inches

        Returns:
            Path to the generated chart file
        """
        plt = self._get_matplotlib()
        self._apply_style(plt)

        labels = data.get("labels", [])
        values = data.get("values", [])

        if not labels or not values:
            raise ValueError("Data must contain 'labels' and 'values' keys")

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(labels, values, color=self.colors[0], linewidth=2, marker="o")

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.3)

        # Rotate x labels if too many
        if len(labels) > 8:
            plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        output_format = fmt or self.default_format
        output_path = self._generate_filename(filename, "line", output_format)
        plt.savefig(output_path, dpi=self.dpi, format=output_format)
        plt.close(fig)

        logger.info(f"Generated line chart: {output_path}")
        return str(output_path)

    def generate_multi_line_chart(
        self,
        data: Dict[str, Any],
        title: str = "Multi-Line Chart",
        filename: str = "multi_line_chart",
        x_label: str = "",
        y_label: str = "",
        fmt: Optional[ChartFormat] = None,
        figsize: tuple = (10, 6),
        show_legend: bool = True,
    ) -> str:
        """
        Generate a multi-line chart comparing multiple data series.

        Args:
            data: Dict with "labels" and "series" (dict of name -> values)
            title: Chart title
            filename: Base filename
            x_label: X-axis label
            y_label: Y-axis label
            fmt: Output format
            figsize: Figure size
            show_legend: Whether to show legend

        Returns:
            Path to the generated chart file
        """
        plt = self._get_matplotlib()
        self._apply_style(plt)

        labels = data.get("labels", [])
        series = data.get("series", {})

        if not labels or not series:
            raise ValueError("Data must contain 'labels' and 'series' keys")

        fig, ax = plt.subplots(figsize=figsize)

        for idx, (name, values) in enumerate(series.items()):
            color = self.colors[idx % len(self.colors)]
            ax.plot(labels, values, color=color, linewidth=2, marker="o", label=name)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.3)

        if show_legend:
            ax.legend(loc="best")

        if len(labels) > 8:
            plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        output_format = fmt or self.default_format
        output_path = self._generate_filename(filename, "multi_line", output_format)
        plt.savefig(output_path, dpi=self.dpi, format=output_format)
        plt.close(fig)

        logger.info(f"Generated multi-line chart: {output_path}")
        return str(output_path)

    def generate_bar_chart(
        self,
        data: Dict[str, Any],
        title: str = "Bar Chart",
        filename: str = "bar_chart",
        x_label: str = "",
        y_label: str = "",
        fmt: Optional[ChartFormat] = None,
        figsize: tuple = (10, 6),
        horizontal: bool = False,
    ) -> str:
        """
        Generate a bar chart.

        Args:
            data: Dict with "labels" and "values" keys
            title: Chart title
            filename: Base filename
            x_label: X-axis label
            y_label: Y-axis label
            fmt: Output format
            figsize: Figure size
            horizontal: If True, generate horizontal bar chart

        Returns:
            Path to the generated chart file
        """
        plt = self._get_matplotlib()
        self._apply_style(plt)

        labels = data.get("labels", [])
        values = data.get("values", [])

        if not labels or not values:
            raise ValueError("Data must contain 'labels' and 'values' keys")

        fig, ax = plt.subplots(figsize=figsize)

        # Use different colors for each bar
        colors = [self.colors[i % len(self.colors)] for i in range(len(labels))]

        if horizontal:
            ax.barh(labels, values, color=colors)
            ax.set_xlabel(y_label)
            ax.set_ylabel(x_label)
        else:
            ax.bar(labels, values, color=colors)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            if len(labels) > 8:
                plt.xticks(rotation=45, ha="right")

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y" if not horizontal else "x")

        plt.tight_layout()

        chart_type = "horizontal_bar" if horizontal else "bar"
        output_format = fmt or self.default_format
        output_path = self._generate_filename(filename, chart_type, output_format)
        plt.savefig(output_path, dpi=self.dpi, format=output_format)
        plt.close(fig)

        logger.info(f"Generated bar chart: {output_path}")
        return str(output_path)

    def generate_pie_chart(
        self,
        data: Dict[str, Any],
        title: str = "Pie Chart",
        filename: str = "pie_chart",
        fmt: Optional[ChartFormat] = None,
        figsize: tuple = (8, 8),
        show_percentages: bool = True,
        explode_largest: bool = False,
    ) -> str:
        """
        Generate a pie chart for market share or distribution data.

        Args:
            data: Dict with "labels" and "values" keys
            title: Chart title
            filename: Base filename
            fmt: Output format
            figsize: Figure size
            show_percentages: Show percentage labels
            explode_largest: Slightly separate the largest slice

        Returns:
            Path to the generated chart file
        """
        plt = self._get_matplotlib()
        self._apply_style(plt)

        labels = data.get("labels", [])
        values = data.get("values", [])

        if not labels or not values:
            raise ValueError("Data must contain 'labels' and 'values' keys")

        fig, ax = plt.subplots(figsize=figsize)

        colors = [self.colors[i % len(self.colors)] for i in range(len(labels))]

        explode = None
        if explode_largest:
            max_idx = values.index(max(values))
            explode = [0.05 if i == max_idx else 0 for i in range(len(values))]

        autopct = "%1.1f%%" if show_percentages else None

        ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct=autopct,
            explode=explode,
            startangle=90,
            shadow=False,
        )

        ax.set_title(title, fontsize=14, fontweight="bold")

        plt.tight_layout()

        output_format = fmt or self.default_format
        output_path = self._generate_filename(filename, "pie", output_format)
        plt.savefig(output_path, dpi=self.dpi, format=output_format)
        plt.close(fig)

        logger.info(f"Generated pie chart: {output_path}")
        return str(output_path)

    def generate_area_chart(
        self,
        data: Dict[str, Any],
        title: str = "Area Chart",
        filename: str = "area_chart",
        x_label: str = "",
        y_label: str = "",
        fmt: Optional[ChartFormat] = None,
        figsize: tuple = (10, 6),
        stacked: bool = False,
    ) -> str:
        """
        Generate an area chart for cumulative data.

        Args:
            data: Dict with "labels" and "series" for stacked, or "values" for single
            title: Chart title
            filename: Base filename
            x_label: X-axis label
            y_label: Y-axis label
            fmt: Output format
            figsize: Figure size
            stacked: If True, stack multiple series

        Returns:
            Path to the generated chart file
        """
        plt = self._get_matplotlib()
        self._apply_style(plt)

        labels = data.get("labels", [])

        fig, ax = plt.subplots(figsize=figsize)

        if stacked and "series" in data:
            series = data["series"]
            series_names = list(series.keys())
            series_values = list(series.values())
            colors = [self.colors[i % len(self.colors)] for i in range(len(series_names))]
            ax.stackplot(labels, series_values, labels=series_names, colors=colors, alpha=0.8)
            ax.legend(loc="upper left")
        else:
            values = data.get("values", [])
            if not values:
                raise ValueError("Data must contain 'values' or 'series' key")
            ax.fill_between(labels, values, color=self.colors[0], alpha=0.6)
            ax.plot(labels, values, color=self.colors[0], linewidth=2)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.3)

        if len(labels) > 8:
            plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        output_format = fmt or self.default_format
        output_path = self._generate_filename(filename, "area", output_format)
        plt.savefig(output_path, dpi=self.dpi, format=output_format)
        plt.close(fig)

        logger.info(f"Generated area chart: {output_path}")
        return str(output_path)

    def generate_scatter_chart(
        self,
        data: Dict[str, Any],
        title: str = "Scatter Plot",
        filename: str = "scatter_chart",
        x_label: str = "X",
        y_label: str = "Y",
        fmt: Optional[ChartFormat] = None,
        figsize: tuple = (10, 6),
        show_trendline: bool = False,
    ) -> str:
        """
        Generate a scatter plot for correlation analysis.

        Args:
            data: Dict with "x" and "y" lists, optionally "labels" for point labels
            title: Chart title
            filename: Base filename
            x_label: X-axis label
            y_label: Y-axis label
            fmt: Output format
            figsize: Figure size
            show_trendline: Add a linear trendline

        Returns:
            Path to the generated chart file
        """
        plt = self._get_matplotlib()
        self._apply_style(plt)

        x_values = data.get("x", [])
        y_values = data.get("y", [])
        point_labels = data.get("labels", [])

        if not x_values or not y_values:
            raise ValueError("Data must contain 'x' and 'y' keys")

        fig, ax = plt.subplots(figsize=figsize)

        ax.scatter(x_values, y_values, c=self.colors[0], s=100, alpha=0.7)

        # Add point labels if provided
        if point_labels:
            for i, label in enumerate(point_labels):
                ax.annotate(
                    label,
                    (x_values[i], y_values[i]),
                    textcoords="offset points",
                    xytext=(5, 5),
                    fontsize=8,
                )

        # Add trendline
        if show_trendline:
            try:
                import numpy as np

                z = np.polyfit(x_values, y_values, 1)
                p = np.poly1d(z)
                ax.plot(
                    x_values,
                    p(x_values),
                    color=self.colors[1],
                    linestyle="--",
                    linewidth=2,
                    alpha=0.8,
                )
            except ImportError:
                logger.warning("numpy required for trendline, skipping")

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        output_format = fmt or self.default_format
        output_path = self._generate_filename(filename, "scatter", output_format)
        plt.savefig(output_path, dpi=self.dpi, format=output_format)
        plt.close(fig)

        logger.info(f"Generated scatter chart: {output_path}")
        return str(output_path)

    def generate_from_json(
        self,
        json_data: Union[str, Dict[str, Any]],
        chart_type: ChartType = "bar",
        **kwargs,
    ) -> str:
        """
        Generate a chart from JSON data (string or dict).

        Args:
            json_data: JSON string or dict containing chart data
            chart_type: Type of chart to generate
            **kwargs: Additional arguments passed to the chart method

        Returns:
            Path to the generated chart file
        """
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        chart_methods = {
            "line": self.generate_line_chart,
            "bar": self.generate_bar_chart,
            "pie": self.generate_pie_chart,
            "area": self.generate_area_chart,
            "scatter": self.generate_scatter_chart,
            "horizontal_bar": lambda d, **kw: self.generate_bar_chart(d, horizontal=True, **kw),
        }

        if chart_type not in chart_methods:
            raise ValueError(f"Unsupported chart type: {chart_type}. Use one of: {list(chart_methods.keys())}")

        return chart_methods[chart_type](data, **kwargs)


# Export
__all__ = ["ChartGeneratorTool", "ChartFormat", "ChartType"]
