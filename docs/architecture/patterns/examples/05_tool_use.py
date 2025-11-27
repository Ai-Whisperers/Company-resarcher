"""
Tool Use Pattern Example
------------------------
This script demonstrates the Tool Use pattern:
Query -> Select Tool -> Execute -> Result

It simulates an agent choosing between a Calculator and a Search tool.
"""

import asyncio
import json
from typing import Dict, Any, Callable

# --- Tools ---


def calculator(expression: str) -> str:
    """Evaluates a mathematical expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"


def search(query: str) -> str:
    """Simulates a web search."""
    return f"Search results for: '{query}'"


# --- Tool Registry ---

TOOLS = {"calculator": calculator, "search": search}

# --- Mock AI Agent ---


async def agent_decide_tool(query: str) -> Dict[str, Any]:
    print(f"🤖 Agent thinking about: '{query}'")

    # Simple keyword-based logic to simulate LLM decision
    if any(char.isdigit() for char in query) and any(
        op in query for op in ["+", "-", "*", "/"]
    ):
        return {"tool": "calculator", "args": {"expression": query}}
    else:
        return {"tool": "search", "args": {"query": query}}


# --- Orchestrator ---


async def run_agent(query: str):
    # 1. Decide
    decision = await agent_decide_tool(query)
    tool_name = decision["tool"]
    args = decision["args"]

    print(f"👉 Selected Tool: {tool_name}")
    print(f"   Arguments: {args}")

    # 2. Execute
    if tool_name in TOOLS:
        tool_func = TOOLS[tool_name]
        result = tool_func(**args)
        print(f"✅ Tool Output: {result}\n")
    else:
        print(f"❌ Unknown tool: {tool_name}\n")


async def main():
    queries = ["What is 25 * 4?", "Who is the CEO of Google?", "100 / 5 + 10"]

    for q in queries:
        await run_agent(q)


if __name__ == "__main__":
    asyncio.run(main())
