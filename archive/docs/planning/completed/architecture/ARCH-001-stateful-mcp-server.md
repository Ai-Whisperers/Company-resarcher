# ARCH-001: Stateful MCP Server Architecture

## Status: RESOLVED

**Resolved Date:** 2025-12-01
**Implementation:** [src/mcp/](../../../../src/mcp/)

## Problem Statement

Our agents currently pass massive context strings back and forth. This is inefficient and error-prone. We need a shared state model.

## Implemented Solution

Implemented a Stateful MCP Server where the server maintains a `project_state` object. Tools read from and write to this shared state instead of requiring all context as input arguments.

### Files Created

1. **[src/mcp/__init__.py](../../../../src/mcp/__init__.py)** - Module exports and documentation
2. **[src/mcp/state.py](../../../../src/mcp/state.py)** - Thread-safe state management
3. **[src/mcp/server.py](../../../../src/mcp/server.py)** - MCP server with research tools

### Key Components

#### 1. ProjectState Class (`state.py`)
Thread-safe dataclass holding all research session data:
- Company information (name, website, industry, description)
- Research phase tracking
- Raw data and search queries
- Analysis results (market, competitive, financial, etc.)
- Report drafts and final reports
- Sources and errors
- Evaluation metrics

#### 2. StateManager (`state.py`)
Thread-safe singleton manager providing:
- Atomic state updates with `threading.RLock`
- Deep copy on read to prevent external mutation
- Checkpoint/rollback support for error recovery
- Convenience methods: `add_source()`, `add_error()`, `set_phase()`

#### 3. MCP Server (`server.py`)
FastMCP server with 10 research tools:

| Tool | Description |
|------|-------------|
| `init_research` | Initialize a new research session |
| `gather_data` | Gather research data from sources |
| `analyze_company` | Analyze gathered company data |
| `generate_report` | Generate research report |
| `finalize_report` | Finalize and complete research |
| `get_status` | Get current research status |
| `get_analysis` | Get analysis results from state |
| `reset_session` | Reset research session |
| `rollback` | Rollback to checkpoint |
| `health_check` | Server health check |

### Usage Example

```python
from src.mcp.state import get_project_state, update_project_state

# Tool reads company name from shared state (no argument needed)
state = get_project_state()
company = state.company_name

# Tool writes results to shared state
update_project_state(
    market_analysis={"market_size": "$10B", "growth_rate": "5%"}
)

# Next tool reads previous tool's output automatically
state = get_project_state()
market_size = state.market_analysis.get("market_size")
```

### Running the Server

```bash
# Install MCP dependency
pip install mcp>=1.0.0

# Run the server
python -m src.mcp.server
```

## Acceptance Criteria - COMPLETED

- [x] Tools can share data without explicit argument passing
- [x] State is preserved across tool calls within a session
- [x] Reduced token usage for context passing
- [x] Thread-safe for concurrent requests
- [x] Checkpoint/rollback support for error recovery

## Technical Details

### Thread Safety
All state operations are protected by `threading.RLock`:
- Allows reentrant locking (same thread can acquire multiple times)
- Deep copies returned to prevent external mutation
- Atomic updates via `update_state(**kwargs)`

### State Persistence
State is session-based (in-memory). For persistence, the state can be:
- Serialized via `state.to_dict()`
- Restored via `ProjectState.from_dict(data)`

### Dependencies
- `mcp>=1.0.0` - Model Context Protocol server library

## Source References

- Original Design: [AI-Software-Engineering-Team-MCP-Multi-Agent-System/server.py](../../../../docs/reference/external-repos/AI-Software-Engineering-Team-MCP-Multi-Agent-System/server.py)
