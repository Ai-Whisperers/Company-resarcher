# LEARN-003: MCP Protocol Standard

## Topic Overview

The Model Context Protocol (MCP) is an emerging standard for connecting AI models to external tools and data. We need to understand its specification to make our tools interoperable.

## Key Concepts

- **MCP Server**: Exposes tools and resources.
- **MCP Client**: Consumes tools (e.g., Claude Desktop).
- **Transports**: Stdio (standard input/output) vs SSE (Server-Sent Events).
- **JSON-RPC**: The underlying message format.

## Learning Resources

- **Repo**: `AI-Software-Engineering-Team-MCP-Multi-Agent-System/docs/05-MCP-PROTOCOL.md`
- **Official Docs**: modelcontextprotocol.io

## Application

We will implement an MCP server (FEAT-012) to expose our research tools to the wider ecosystem.
