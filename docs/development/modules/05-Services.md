# Services Module Documentation

This module contains helper services and utilities for data processing.

## 1. JSON Parser Helper (`src/services/json_parser_helper.py`)

A utility to robustly parse JSON output from LLMs, which often includes markdown formatting or minor syntax errors.

### Function: `robust_json_parse(json_str: str) -> Dict`

- **Input**: A string potentially containing JSON (e.g., "`json\n{...}\n`").
- **Logic**:
  1.  Strips markdown code block markers (`json, `).
  2.  Attempts `json.loads`.
  3.  If that fails, attempts to fix common errors (e.g., trailing commas, single quotes).
  4.  Returns a dictionary or raises an error.
