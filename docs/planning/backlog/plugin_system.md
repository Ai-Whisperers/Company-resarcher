# Feature: Plugin System

## Source

- **Repository:** `langgenius/dify`
- **File:** `api/core/tools`

## Description

Allow easy extension of the agent's capabilities. Developers should be able to drop in a python file (or an OpenAPI spec) to add a new tool.

## Implementation Details

1.  **Standard Interface:** All plugins must inherit from `BaseTool` and define `name`, `description`, `args_schema`.
2.  **Discovery:** Auto-load plugins from a `plugins/` directory.
3.  **Manifest:** A `manifest.json` file to describe the plugin's metadata.

## Code Reference

```python
class MyPlugin(BaseTool):
    name = "my_plugin"
    def run(self, args):
        ...
```
