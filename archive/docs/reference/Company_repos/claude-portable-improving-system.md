# claude-portable-improving-system

**Description:** Token optimization, export chats, agents and more!
**URL:** https://github.com/Ai-Whisperers/claude-portable-improving-system
**Visibility:** PRIVATE

---

# Portable Claude Insights System

A comprehensive, cross-platform tool for analyzing and optimizing your Claude Code workflow.

## What This Does

1. **Analyzes** your Claude conversations to identify patterns
2. **Suggests** configuration optimizations based on actual usage
3. **Auto-applies** recommended settings (optional)
4. **Tracks** improvements over time
5. **Dashboards** cross-project insights
6. **Integrates** as native Claude tool via MCP

## Features

- 🚀 **One-Command Installation**: Works on Windows, Mac, Linux
- 📊 **Usage Analytics**: Detailed breakdown of tool usage, commands, patterns
- ⚙️ **Smart Configuration**: Auto-generates optimized settings
- 📈 **Progress Tracking**: Compare month-over-month improvements
- 🎨 **Visual Dashboard**: Interactive HTML dashboard for multiple projects
- 🔧 **Claude Integration**: Available as slash command and MCP tool
- 🔄 **Scheduled Analysis**: Set it and forget it - monthly reports

## Quick Start

### Installation

**Option 1: Automatic (Recommended)**
```bash
# Unix/Mac/Git Bash
curl -sSL https://raw.githubusercontent.com/Ai-Whisperers/claude-portable-improving-system/main/install/install.sh | bash

# Windows PowerShell
iwr -useb https://raw.githubusercontent.com/Ai-Whisperers/claude-portable-improving-system/main/install/install.ps1 | iex
```

**Option 2: Manual**
```bash
# Clone or download this folder
cd portable-claude-insights

# Run installer
./install/install.sh       # Unix/Mac/Git Bash
# or
install\install.bat        # Windows CMD
# or
.\install\install.ps1      # Windows PowerShell
```

**Option 3: Python Package**
```bash
pip install -e .
```

### Usage

**Command Line:**
```bash
# Analyze current project
claude-insights

# Analyze and auto-apply suggestions
claude-insights --auto-apply

# Analyze all projects
claude-insights --all-projects

# Generate dashboard
claude-insights --dashboard

# Compare with previous month
claude-insights --compare
```

**As Claude Slash Command:**
```
/insights
```

**As MCP Tool:**
Available automatically in Claude conversations as `analyze_workflow` tool

## What Gets Analyzed

### Tool Usage (6,431 calls analyzed)
- Which tools you use most
- Efficiency patterns (specialized vs bash)
- Parallel vs sequential operations

### Request Patterns (519 requests analyzed)
- Testing, documentation, debugging frequency
- Workflow categories
- Common task types

### Command Usage (2,941 bash commands analyzed)
- Most-used commands
- Permission optimization opportunities
- Platform-specific patterns

### Error Patterns (5,103 errors analyzed)
- Common error types
- Resolution patterns
- Prevention opportunities

### Configuration Gaps
- Missing permissions
- Useful slash commands to create
- Hook opportunities

## Generated Outputs

### 1. Analysis Report (`insights_YYYYMMDD_HHMMSS.json`)
Comprehensive statistics and metrics

### 2. Suggestions (`suggestions_YYYYMMDD_HHMMSS.md`)
Human-readable recommendations

### 3. Optimized Config (`settings.local.json.suggested`)
Ready-to-use configuration file

### 4. Dashboard (`dashboard.html`)
Interactive visualization of patterns

### 5. Comparison Report (`comparison_YYYYMMDD.md`)
Month-over-month progress

## Configuration Options

### Auto-Apply Settings

Edit `~/.claude-insights/config.json`:

```json
{
  "auto_apply": {
    "permissions": true,
    "slash_commands": true,
    "hooks": false
  },
  "analysis": {
    "min_tool_uses_for_permission": 10,
    "min_request_category_for_slash_cmd": 5
  },
  "dashboard": {
    "theme": "dark",
    "refresh_interval_days": 30
  }
}
```

### Scheduled Analysis

**Unix/Mac (cron):**
```bash
# Edit crontab
crontab -e

# Add line for 1st of each month at midnight
0 0 1 * * /usr/local/bin/claude-insights --all-projects --email-report
```

**Windows (Task Scheduler):**
```powershell
# Automated setup
.\scripts\schedule-monthly.ps1
```

## Integration with Claude

### Slash Command

After installation, available in any Claude conversation:

```
/insights
```

Runs analysis and displays summary in conversation.

### MCP Server

Add to your Claude configuration:

```json
{
  "mcpServers": {
    "claude-insights": {
      "command": "claude-insights-mcp",
      "args": ["--project", "."]
    }
  }
}
```

Then Claude can automatically:
- Analyze workflow when you ask
- Suggest optimizations mid-conversation
- Track your progress over time

### Hooks

Post-conversation hook to auto-analyze:

```bash
# .claude/hooks/post-conversation.sh
#!/bin/bash
claude-insights --quick --silent
```

## Project Structure

```
portable-claude-insights/
├── claude_insights/          # Core Python package
│   ├── cli.py               # Command-line interface
│   ├── analyzer.py          # Enhanced analysis engine
│   ├── config_manager.py    # Auto-apply configurations
│   ├── dashboard.py         # Dashboard generation
│   └── mcp_server.py        # MCP server implementation
├── install/                  # Platform-specific installers
├── templates/                # Claude integration templates
├── scripts/                  # Utility scripts
└── examples/                 # Example configurations
```

## Advanced Features

### Cross-Project Dashboard

```bash
# Analyze all projects in a directory
claude-insights --workspace ~/projects --dashboard
```

Generates interactive dashboard showing:
- Comparative tool usage across projects
- Best practices by project type
- Efficiency trends
- Recommended configurations per project

### Historical Tracking

```bash
# Compare current month with previous
claude-insights --compare

# Show 6-month trend
claude-insights --trend 6
```

### Custom Analysis

```python
from claude_insights import ClaudeAnalyzer

analyzer = ClaudeAnalyzer()
conversations = analyzer.load_conversations()

# Custom analysis
my_pattern = analyzer.find_pattern(
    tool="Task",
    subagent_type="Explore",
    min_uses=5
)
```

## Requirements

- Python 3.8+
- Claude Code installed
- ~/.claude/projects/ directory with conversation history

## Troubleshooting

### "No conversations found"

Check that:
1. Claude Code is installed
2. You've had conversations in this project
3. Path is correct: `~/.claude/projects/`

### "Permission denied"

Run with appropriate permissions:
```bash
chmod +x install/install.sh
./install/install.sh
```

### Windows encoding issues

Set encoding in PowerShell:
```powershell
$env:PYTHONIOENCODING = "utf-8"
claude-insights
```

## Contributing

Contributions welcome! This tool is designed to evolve with Claude Code.

### Adding Custom Analyzers

```python
# claude_insights/custom_analyzers/my_analyzer.py
class MyCustomAnalyzer:
    def analyze(self, conversations):
        # Your analysis logic
        return insights
```

### Adding Dashboard Widgets

See `claude_insights/dashboard.py` for widget templates.

## FAQ

**Q: Does this send my conversations anywhere?**
A: No. All analysis is local. Nothing leaves your machine.

**Q: How much disk space does it use?**
A: ~1-2MB per 100 conversations analyzed

**Q: Can I use this with Claude.ai (not Claude Code)?**
A: Currently only works with Claude Code's local conversation storage.

**Q: Does auto-apply overwrite my custom settings?**
A: No. It merges with existing settings and backs up originals.

**Q: How often should I run this?**
A: Monthly is recommended. Set up scheduled analysis for automation.

## License

MIT - Free to use and modify

## Credits

Created by [@IvanWeissVanDerPol](https://github.com/IvanWeissVanDerPol) through collaborative conversations with Claude.

Based on analysis of 90 real conversations showing effective Claude usage patterns, this project emerged from iterative discussions about optimizing Claude Code workflows and making insights portable across projects.

## Links

- Repository: [GitHub](https://github.com/Ai-Whisperers/claude-portable-improving-system)
- Documentation: [Full Docs](./docs/)
- Examples: [Example Configurations](./examples/)
- Issues: [Report a Bug](https://github.com/Ai-Whisperers/claude-portable-improving-system/issues)
