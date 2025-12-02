# LEARN-005: Multi-Agent Orchestration Patterns

## Topic Overview

Coordinating multiple AI agents (Researcher, Analyst, Writer) requires robust orchestration patterns to prevent chaos and ensure goal completion.

## Key Concepts

- **Handoffs**: How one agent passes context to another.
- **Supervisor Pattern**: A central agent managing workers.
- **Shared State**: How agents access common data (project context).
- **Structured Communication**: Using defined schemas for inter-agent messages.

## Learning Resources

- **Repo**: `AI-Software-Engineering-Team-MCP-Multi-Agent-System/docs/02-ARCHITECTURE.md`
- **Frameworks**: LangGraph, AutoGen.

## Application

We will improve our `main.py` orchestration logic to be more resilient and scalable (IMP-010, DEBT-004).
