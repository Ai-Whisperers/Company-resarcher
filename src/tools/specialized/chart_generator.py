"""
Chart Generator Tool (TOOL-001).

Generates visualizations for financial and research data using matplotlib/plotly.

Usage:
    from src.tools.chart_generator import ChartGenerator

    generator = ChartGenerator()

    # Line chart
    chart_path = generator.line_chart(
        data={"2021": 100, "2022": 150, "2023": 200},
        title="Revenue Growth",
        output_path="charts/revenue.png"
    )

    # Bar chart
    chart_path = generator.bar_chart(
        data={"Product A": 40, "Product B": 35, "Product C": 25},
        title="Market Share",
        output_path="charts/market_share.png"
    )
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ...core.logging import get_logger

logger = get_logger(__name__)

# Chart output directory (configurable via env)
CHART_OUTPUT_DIR = os.getenv("CHART_OUTPUT_DIR", "outputs/charts")

# Chart styling defaults
CHART_STYLE = os.getenv("CHART_STYLE", "seaborn-v0_8-whitegrid")
CHART_DPI = int(os.getenv("CHART_DPI", "150"))
CHART_FIGSIZE = (10, 6)

# Try to import matplotlib, fallback gracefully if not installed
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for server use
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not installed. Chart generation disabled.")

# Try to import plotly for interactive charts
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.debug("plotly not installed. Interactive charts disabled.")


class ChartGenerator:
    """
    Generate charts and visualizations for research data.

    Supports:
    - Line charts (time series, trends)
    - Bar charts (comparisons, distributions)
    - Pie charts (proportions, market share)
    - Combined charts (multi-series)

    Outputs:
    - PNG/SVG images (matplotlib)
    - Interactive HTML (plotly, if available)
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        style: Optional[str] = None,
        dpi: int = CHART_DPI,
        figsize: tuple = CHART_FIGSIZE,
    ):
        """
        Initialize chart generator.

        Args:
            output_dir: Directory for chart output files
            style: Matplotlib style (e.g., 'seaborn-v0_8-whitegrid')
            dpi: Resolution for PNG output
            figsize: Default figure size (width, height) in inches
        """
        self.output_dir = Path(output_dir or CHART_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.style = style or CHART_STYLE
        self.dpi = dpi
        self.figsize = figsize

        if MATPLOTLIB_AVAILABLE:
            try:
                plt.style.use(self.style)
            except OSError:
                plt.style.use('default')

    def _generate_filename(self, prefix: str, ext: str = "png") -> Path:
        """Generate unique filename for chart."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{prefix}_{timestamp}.{ext}"

    def line_chart(
        self,
        data: Dict[str, Union[float, int]],
        title: str = "Line Chart",
        xlabel: str = "",
        ylabel: str = "",
        output_path: Optional[str] = None,
        color: str = "#2196F3",
        marker: str = "o",
    ) -> Optional[str]:
        """
        Generate a line chart.

        Args:
            data: Dictionary of {x_label: y_value}
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            output_path: Custom output path (optional)
            color: Line color
            marker: Data point marker style

        Returns:
            Path to generated chart file, or None on error
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib not available for chart generation")
            return None

        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            x_values = list(data.keys())
            y_values = list(data.values())

            ax.plot(x_values, y_values, color=color, marker=marker, linewidth=2)

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)

            # Rotate x labels if many values
            if len(x_values) > 6:
                plt.xticks(rotation=45, ha='right')

            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save chart
            output = Path(output_path) if output_path else self._generate_filename("line")
            output.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output, dpi=self.dpi, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Line chart saved to {output}")
            return str(output)

        except Exception as e:
            logger.error(f"Failed to generate line chart: {e}")
            return None

    def bar_chart(
        self,
        data: Dict[str, Union[float, int]],
        title: str = "Bar Chart",
        xlabel: str = "",
        ylabel: str = "",
        output_path: Optional[str] = None,
        color: str = "#4CAF50",
        horizontal: bool = False,
    ) -> Optional[str]:
        """
        Generate a bar chart.

        Args:
            data: Dictionary of {category: value}
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            output_path: Custom output path
            color: Bar color
            horizontal: Use horizontal bars

        Returns:
            Path to generated chart file
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib not available for chart generation")
            return None

        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            categories = list(data.keys())
            values = list(data.values())

            if horizontal:
                ax.barh(categories, values, color=color)
                ax.set_xlabel(ylabel or "Value")
                ax.set_ylabel(xlabel or "Category")
            else:
                ax.bar(categories, values, color=color)
                ax.set_xlabel(xlabel or "Category")
                ax.set_ylabel(ylabel or "Value")

            ax.set_title(title, fontsize=14, fontweight='bold')

            # Rotate x labels if many categories
            if not horizontal and len(categories) > 6:
                plt.xticks(rotation=45, ha='right')

            plt.tight_layout()

            output = Path(output_path) if output_path else self._generate_filename("bar")
            output.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output, dpi=self.dpi, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Bar chart saved to {output}")
            return str(output)

        except Exception as e:
            logger.error(f"Failed to generate bar chart: {e}")
            return None

    def pie_chart(
        self,
        data: Dict[str, Union[float, int]],
        title: str = "Pie Chart",
        output_path: Optional[str] = None,
        colors: Optional[List[str]] = None,
        explode_largest: bool = True,
    ) -> Optional[str]:
        """
        Generate a pie chart.

        Args:
            data: Dictionary of {category: value}
            title: Chart title
            output_path: Custom output path
            colors: Custom color palette
            explode_largest: Explode the largest slice

        Returns:
            Path to generated chart file
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib not available for chart generation")
            return None

        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            labels = list(data.keys())
            values = list(data.values())

            # Default color palette
            if colors is None:
                colors = ['#2196F3', '#4CAF50', '#FFC107', '#E91E63', '#9C27B0',
                         '#00BCD4', '#FF5722', '#795548', '#607D8B', '#3F51B5']

            # Explode largest slice
            explode = None
            if explode_largest and values:
                max_idx = values.index(max(values))
                explode = [0.05 if i == max_idx else 0 for i in range(len(values))]

            ax.pie(
                values,
                labels=labels,
                colors=colors[:len(labels)],
                explode=explode,
                autopct='%1.1f%%',
                startangle=90,
                shadow=True,
            )
            ax.set_title(title, fontsize=14, fontweight='bold')

            plt.tight_layout()

            output = Path(output_path) if output_path else self._generate_filename("pie")
            output.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output, dpi=self.dpi, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Pie chart saved to {output}")
            return str(output)

        except Exception as e:
            logger.error(f"Failed to generate pie chart: {e}")
            return None

    def multi_line_chart(
        self,
        data: Dict[str, Dict[str, Union[float, int]]],
        title: str = "Multi-Line Chart",
        xlabel: str = "",
        ylabel: str = "",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a multi-line chart with multiple series.

        Args:
            data: Dictionary of {series_name: {x_label: y_value}}
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            output_path: Custom output path

        Returns:
            Path to generated chart file
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib not available for chart generation")
            return None

        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            colors = ['#2196F3', '#4CAF50', '#FFC107', '#E91E63', '#9C27B0']

            for i, (series_name, series_data) in enumerate(data.items()):
                x_values = list(series_data.keys())
                y_values = list(series_data.values())
                color = colors[i % len(colors)]
                ax.plot(x_values, y_values, marker='o', label=series_name, color=color)

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            output = Path(output_path) if output_path else self._generate_filename("multi_line")
            output.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output, dpi=self.dpi, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Multi-line chart saved to {output}")
            return str(output)

        except Exception as e:
            logger.error(f"Failed to generate multi-line chart: {e}")
            return None

    def financial_chart(
        self,
        revenue: Dict[str, float],
        profit: Optional[Dict[str, float]] = None,
        title: str = "Financial Performance",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a financial chart with revenue and optional profit.

        Args:
            revenue: Dictionary of {period: revenue_value}
            profit: Optional dictionary of {period: profit_value}
            title: Chart title
            output_path: Custom output path

        Returns:
            Path to generated chart file
        """
        data = {"Revenue": revenue}
        if profit:
            data["Profit"] = profit

        return self.multi_line_chart(
            data=data,
            title=title,
            xlabel="Period",
            ylabel="Amount ($)",
            output_path=output_path,
        )

    def create_interactive_chart(
        self,
        data: Dict[str, Union[float, int]],
        chart_type: str = "bar",
        title: str = "Interactive Chart",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create an interactive HTML chart using Plotly.

        Args:
            data: Dictionary of {category: value}
            chart_type: "bar", "line", or "pie"
            title: Chart title
            output_path: Custom output path (.html)

        Returns:
            Path to generated HTML file
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("plotly not available, falling back to static chart")
            if chart_type == "bar":
                return self.bar_chart(data, title, output_path=output_path)
            elif chart_type == "pie":
                return self.pie_chart(data, title, output_path=output_path)
            else:
                return self.line_chart(data, title, output_path=output_path)

        try:
            x_values = list(data.keys())
            y_values = list(data.values())

            if chart_type == "bar":
                fig = go.Figure(data=[go.Bar(x=x_values, y=y_values)])
            elif chart_type == "pie":
                fig = go.Figure(data=[go.Pie(labels=x_values, values=y_values)])
            else:  # line
                fig = go.Figure(data=[go.Scatter(x=x_values, y=y_values, mode='lines+markers')])

            fig.update_layout(title=title)

            output = Path(output_path) if output_path else self._generate_filename("interactive", "html")
            output.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(output))

            logger.info(f"Interactive chart saved to {output}")
            return str(output)

        except Exception as e:
            logger.error(f"Failed to generate interactive chart: {e}")
            return None


# Singleton instance for convenience
_chart_generator: Optional[ChartGenerator] = None


def get_chart_generator() -> ChartGenerator:
    """Get or create singleton chart generator instance."""
    global _chart_generator
    if _chart_generator is None:
        _chart_generator = ChartGenerator()
    return _chart_generator


__all__ = [
    "ChartGenerator",
    "get_chart_generator",
    "MATPLOTLIB_AVAILABLE",
    "PLOTLY_AVAILABLE",
]
