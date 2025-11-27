"""
MCP Pattern Example
-------------------
This script demonstrates the Model Context Protocol (MCP) pattern:
Client <-> Protocol <-> Server

It simulates an agent discovering and using tools via a standardized protocol.
"""

import asyncio
from typing import Dict, Any, List, Callable

# --- Mock MCP Protocol ---


class MCPServer:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, str] = {}

    def register_tool(self, name: str, func: Callable):
        self.tools[name] = func

    def register_resource(self, uri: str, content: str):
        self.resources[uri] = content

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")

        if method == "list_tools":
            return {"tools": list(self.tools.keys())}

        elif method == "call_tool":
            name = request.get("params", {}).get("name")
            args = request.get("params", {}).get("args", {})
            if name in self.tools:
                result = self.tools[name](**args)
                return {"result": result}
            return {"error": "Tool not found"}

        elif method == "read_resource":
            uri = request.get("params", {}).get("uri")
            if uri in self.resources:
                return {"content": self.resources[uri]}
            return {"error": "Resource not found"}

        return {"error": "Unknown method"}


# --- Mock Client ---


class MCPClient:
    def __init__(self, server: MCPServer):
        self.server = server

    async def list_tools(self) -> List[str]:
        response = await self.server.handle_request({"method": "list_tools"})
        return response.get("tools", [])

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        response = await self.server.handle_request(
            {"method": "call_tool", "params": {"name": name, "args": args}}
        )
        return response.get("result", response.get("error"))


# --- Implementation ---


def add(a: int, b: int) -> int:
    return a + b


def greet(name: str) -> str:
    return f"Hello, {name}!"


async def main():
    # 1. Setup Server
    server = MCPServer()
    server.register_tool("add", add)
    server.register_tool("greet", greet)
    server.register_resource("note://1", "Buy milk")

    # 2. Setup Client
    client = MCPClient(server)

    # 3. Discovery
    print("🔎 Discovering tools...")
    tools = await client.list_tools()
    print(f"Available tools: {tools}")

    # 4. Execution
    print("\n🛠️ Calling 'add' tool...")
    result = await client.call_tool("add", {"a": 5, "b": 10})
    print(f"Result: {result}")

    print("\n🛠️ Calling 'greet' tool...")
    result = await client.call_tool("greet", {"name": "MCP User"})
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
