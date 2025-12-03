# 🔧 Developer Experience (DX) Improvements

This document outlines improvements designed to make the development process smoother, faster, and less error-prone. A better developer experience translates directly to higher productivity and code quality.

## DX-1: CLI Tool Improvements (4h)

### Concept & Rationale

A robust Command Line Interface (CLI) is essential for testing, debugging, and running ad-hoc tasks without needing to spin up the full web server or UI.

**The Improvement:**
Enhance the existing CLI using `typer` and `rich` to provide a modern, interactive experience.

- **Rich Output:** Use the `rich` library to display formatted tables, progress bars, and syntax-highlighted JSON/Markdown output. This makes logs and results much easier to parse visually.
- **Progress Tracking:** Implement real-time progress bars for long-running research tasks, giving immediate feedback on the internal state of the process.
- **System Introspection:** Add commands like `validate` (to check config and connections) and `providers` (to list active providers, health status, and remaining rate limits).

### Key Implementation Details

- Use `typer` for argument parsing and command structure.
- Integrate `asyncio` support for running async research tasks from the CLI.
- Reference: `src/cli/commands.py` (Proposed)

## DX-2: Hot Reload for Development (4h)

### Concept & Rationale

Restarting the entire application to see changes in logic (especially deep in the research pipeline) is slow and disrupts flow.

**The Improvement:**
Implement a `HotReloader` that watches for file changes in specific directories (`src/agents`, `src/services`) and reloads the corresponding Python modules in memory without restarting the main process.

- **State Preservation:** Attempt to preserve the state of running services where possible, or at least minimize the "blast radius" of the reload.
- **Fast Feedback:** This allows developers to tweak prompt templates, parsing logic, or heuristic algorithms and immediately test the effect on the next request.

### Key Implementation Details

- Use `watchdog` or similar libraries to monitor file system events.
- Use `importlib.reload` to reload modules.
- _Note:_ This is primarily for development mode (`settings.debug = True`).
- Reference: `src/dev/hot_reload.py` (Proposed)

## DX-3: Debug Mode Enhancements (4h)

### Concept & Rationale

Debugging complex AI agent interactions can be difficult. Standard logs often miss the context of _why_ a decision was made.

**The Improvement:**
Create a `DebugInspector` tool that provides deep visibility into the execution flow.

- **Tracing Decorator:** A `@trace_call` decorator that captures inputs, outputs, execution time, and exceptions for any decorated function.
- **Snapshots:** A mechanism to capture the full state of an object or data structure at a specific point in time (`debug_inspector.snapshot("name", data)`).
- **Exportable Traces:** Ability to export the execution trace as a JSON file or a flamegraph for post-mortem analysis.

### Key Implementation Details

- Store traces in memory (ring buffer) or write to a separate debug log.
- Ensure minimal overhead when debug mode is disabled.
- Reference: `src/core/debug/inspector.py` (Proposed)

## DX-4: Type Stubs and IDE Support (4h)

### Concept & Rationale

Python's dynamic nature can lead to runtime errors that could have been caught statically. Good type hinting improves IDE autocompletion and reduces bugs.

**The Improvement:**
Enhance type safety by adding comprehensive type stubs (`.pyi` files) and configuring strict type checking.

- **Protocols:** Define `Protocol` classes for core interfaces (like `AIClientProtocol`) to enforce structural subtyping.
- **Overloads:** Use `@overload` to specify precise return types based on input arguments (e.g., `generate` returning `str` vs structured data).
- **Strict Mode:** Configure `pyright` or `mypy` to run in strict mode for the `src` directory, ensuring no "Any" types leak through critical paths.

### Key Implementation Details

- Create a `src/types` directory for custom type definitions.
- Add `py.typed` marker files to packages.
- Reference: `src/types/stubs/ai_client.pyi` (Proposed)

## DX-5: Local Development Environment (4h)

### Concept & Rationale

Setting up a dev environment should be a one-step process. Inconsistent environments between developers lead to "works on my machine" issues.

**The Improvement:**
Standardize the local development setup using Docker Compose and automation scripts.

- **Docker Compose:** Define a `docker-compose.dev.yml` that spins up all dependencies (Postgres, Redis, MinIO, MailHog) with development-friendly configurations (exposed ports, persistence).
- **Setup Script:** A `scripts/dev_setup.py` script that handles the entire bootstrap process: creating a venv, installing dependencies, copying `.env` templates, starting containers, running migrations, and seeding initial data.

### Key Implementation Details

- Ensure the Docker setup mounts the local source code for live editing.
- Include a "debug" service definition that exposes a port for attaching a remote debugger (e.g., `debugpy`).
- Reference: `docker-compose.dev.yml` and `scripts/dev_setup.py` (Proposed)
