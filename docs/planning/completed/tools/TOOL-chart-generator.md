# [RESOLVED] TOOL: Chart Generator Tool

**Status**: RESOLVED
**Original File**: backlog/08-agents-tools.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Low
**Description:** Generate visualization for financial data.

**Acceptance Criteria:**
- [x] Use `matplotlib` or `plotly`
- [x] Input: JSON data series
- [x] Output: Image file path (PNG/SVG)

## Resolution

### Implementation

**File:** `src/tools/chart_tool.py`

```python
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
        ...
```

### Supported Chart Types

1. **Line Charts** - Single and multi-series time series data
   - `generate_line_chart(data, title, ...)`
   - `generate_multi_line_chart(data, title, ...)`

2. **Bar Charts** - Comparisons and distributions
   - `generate_bar_chart(data, title, horizontal=False, ...)`

3. **Pie Charts** - Market share and proportions
   - `generate_pie_chart(data, title, show_percentages=True, ...)`

4. **Area Charts** - Cumulative data visualization
   - `generate_area_chart(data, title, stacked=False, ...)`

5. **Scatter Plots** - Correlation analysis
   - `generate_scatter_chart(data, title, show_trendline=False, ...)`

### Usage Example

```python
from src.tools.chart_tool import ChartGeneratorTool

tool = ChartGeneratorTool(output_dir="./outputs/charts")

# Line chart
chart_path = tool.generate_line_chart(
    data={"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [100, 120, 115, 140]},
    title="Quarterly Revenue",
    filename="revenue_chart"
)

# Multi-series comparison
chart_path = tool.generate_multi_line_chart(
    data={
        "labels": ["2020", "2021", "2022", "2023"],
        "series": {
            "Company A": [100, 110, 125, 140],
            "Company B": [90, 95, 105, 120],
        }
    },
    title="Revenue Comparison"
)

# From JSON string
chart_path = tool.generate_from_json(
    json_data='{"labels": ["A", "B", "C"], "values": [30, 50, 20]}',
    chart_type="pie",
    title="Market Share"
)
```

### Output Formats

- **PNG** (default) - Raster format, configurable DPI
- **SVG** - Vector format for scalability
- **PDF** - Print-ready format

### Files

- **Tool:** `src/tools/chart_tool.py` - `ChartGeneratorTool` class
- **Export:** Added to `src/tools/__init__.py`

### Dependencies

- `matplotlib` (required)
- `numpy` (optional, for trendlines)
