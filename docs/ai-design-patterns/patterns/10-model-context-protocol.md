# Model Context Protocol (MCP) Pattern

## 📖 Overview

MCP is a standardized protocol for connecting AI agents with external data sources and tools, enabling seamless context sharing and tool discovery.

**Category**: Advanced Pattern  
**Difficulty**: Medium-High  
**Impact**: High

## 🎯 Core Concept

```
Agent → MCP Server → Resources/Tools
         ↓
    Standardized Protocol
         ↓
    - Resource Discovery
    - Tool Invocation
    - Context Sharing
```

MCP provides a universal interface for:

- **Resources**: Data sources (files, databases, APIs)
- **Tools**: Executable functions
- **Prompts**: Reusable prompt templates
- **Sampling**: LLM interaction patterns

## 💡 Why This Pattern?

### Problems It Solves

- **Tool Fragmentation**: Each tool has different API
- **Context Loss**: Hard to share context between agents
- **Discovery**: Agents can't find available tools
- **Standardization**: No common protocol

### Benefits

- ✅ **Standardized Interface**: One protocol for all tools
- ✅ **Dynamic Discovery**: Agents find tools at runtime
- ✅ **Context Sharing**: Seamless data exchange
- ✅ **Extensibility**: Easy to add new tools

## 🏗️ Architecture

### MCP Components

```python
# MCP Server
class MCPServer:
    def list_resources(self) -> List[Resource]:
        """Discover available resources"""
        pass

    def read_resource(self, uri: str) -> ResourceContent:
        """Read resource content"""
        pass

    def list_tools(self) -> List[Tool]:
        """Discover available tools"""
        pass

    def call_tool(self, name: str, args: dict) -> ToolResult:
        """Execute tool"""
        pass
```

### Resource Types

- **File System**: Local files, directories
- **Databases**: SQL, NoSQL queries
- **APIs**: REST, GraphQL endpoints
- **Cloud Storage**: S3, Azure Blob
- **Knowledge Bases**: Vector stores, graphs

### Tool Types

- **Search**: Web search, document search
- **Computation**: Math, data processing
- **Communication**: Email, messaging
- **Integration**: Third-party services

## 📊 Implementation in Marketing Agent

### Current Status

**Status**: ❌ Not Implemented  
**Priority**: 🟡 Medium  
**Potential**: High

### Potential Implementation

```python
# MCP Server for Marketing Tools
class MarketingMCPServer:
    def __init__(self):
        self.resources = {
            "campaigns": CampaignResource(),
            "research": ResearchResource(),
            "brand_guidelines": BrandResource()
        }

        self.tools = {
            "web_search": TavilySearchTool(),
            "video_gen": VeoTool(),
            "content_fetch": WebFetcherTool()
        }

    async def list_resources(self):
        return [
            {
                "uri": "campaign://nestle-paraguay",
                "name": "Nestlé Paraguay Campaign",
                "type": "campaign",
                "mimeType": "application/json"
            },
            {
                "uri": "research://market-analysis",
                "name": "Market Research",
                "type": "research",
                "mimeType": "text/markdown"
            }
        ]

    async def read_resource(self, uri: str):
        resource_type, resource_id = uri.split("://")
        resource = self.resources.get(resource_type)
        return await resource.read(resource_id)

    async def list_tools(self):
        return [
            {
                "name": "web_search",
                "description": "Search the web for information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            },
            {
                "name": "video_gen",
                "description": "Generate branded video",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "duration": {"type": "number"}
                    }
                }
            }
        ]

    async def call_tool(self, name: str, arguments: dict):
        tool = self.tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool {name} not found")

        return await tool.execute(**arguments)
```

## 🔧 Implementation Guide

### Step 1: Define MCP Server

```python
from mcp import Server, Resource, Tool

server = Server("marketing-agent")

# Register resources
@server.resource("campaign://{id}")
async def get_campaign(id: str):
    campaign = await load_campaign(id)
    return {
        "uri": f"campaign://{id}",
        "mimeType": "application/json",
        "text": json.dumps(campaign)
    }

# Register tools
@server.tool("web_search")
async def web_search(query: str):
    results = await tavily.search(query)
    return {"results": results}
```

### Step 2: Connect Agent to MCP

```python
from mcp import Client

# Agent connects to MCP server
client = Client("marketing-agent-server")

# Discover resources
resources = await client.list_resources()

# Read resource
campaign = await client.read_resource("campaign://nestle-paraguay")

# Discover tools
tools = await client.list_tools()

# Use tool
results = await client.call_tool("web_search", {"query": "Paraguay market trends"})
```

### Step 3: Implement Context Sharing

```python
# Share context between agents
async def share_context(source_agent, target_agent, context_uri):
    # Source agent publishes context
    await mcp_server.publish_resource(context_uri, context_data)

    # Target agent subscribes
    context = await mcp_server.read_resource(context_uri)

    # Target agent uses context
    result = await target_agent.process(context)
```

## 🎓 Best Practices

### Do's ✅

- **Standardize URIs**: Use consistent URI schemes
- **Version APIs**: Support multiple MCP versions
- **Document Tools**: Clear descriptions and schemas
- **Handle Errors**: Graceful error responses
- **Cache Resources**: Avoid redundant reads

### Don'ts ❌

- **Don't Hardcode**: Use discovery, not hardcoded tools
- **Don't Skip Validation**: Validate all inputs
- **Don't Ignore Security**: Authenticate and authorize
- **Don't Block**: Use async operations

## 📈 Performance & Metrics

### Metrics to Track

- **Discovery Time**: Time to list resources/tools
- **Tool Latency**: Time to execute tools
- **Cache Hit Rate**: Resource caching effectiveness
- **Error Rate**: Failed tool calls
- **Resource Usage**: Memory, CPU for MCP server

### Optimization Tips

```python
# Cache resource listings
@lru_cache(maxsize=100)
async def list_resources_cached():
    return await mcp_server.list_resources()

# Batch tool calls
async def batch_tool_calls(calls: List[ToolCall]):
    return await asyncio.gather(*[
        mcp_server.call_tool(call.name, call.args)
        for call in calls
    ])
```

## 🚀 Advanced Techniques

### 1. Dynamic Tool Registration

```python
# Register tools at runtime
async def register_new_tool(tool_def: ToolDefinition):
    mcp_server.register_tool(
        name=tool_def.name,
        description=tool_def.description,
        handler=tool_def.handler,
        schema=tool_def.input_schema
    )
```

### 2. Resource Subscriptions

```python
# Subscribe to resource changes
async def subscribe_to_campaign(campaign_id: str):
    async for update in mcp_server.subscribe(f"campaign://{campaign_id}"):
        await handle_campaign_update(update)
```

### 3. Federated MCP

```python
# Connect multiple MCP servers
class FederatedMCP:
    def __init__(self, servers: List[MCPServer]):
        self.servers = servers

    async def list_all_tools(self):
        all_tools = []
        for server in self.servers:
            tools = await server.list_tools()
            all_tools.extend(tools)
        return all_tools
```

## 🔬 Research & References

### Key Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [Anthropic MCP](https://www.anthropic.com/news/model-context-protocol)
- [OpenAI Integration](https://platform.openai.com/docs/guides/mcp)

### Related Patterns

- **Tool Use**: MCP standardizes tool access
- **A2A Communication**: MCP enables agent communication
- **RAG**: MCP can serve knowledge bases

## 💻 Code Examples

### Basic MCP Server

```python
from mcp.server import Server
from mcp.types import Resource, Tool

app = Server("marketing-mcp")

@app.list_resources()
async def list_resources():
    return [
        Resource(
            uri="campaign://active",
            name="Active Campaigns",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: str):
    if uri == "campaign://active":
        campaigns = await get_active_campaigns()
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(campaigns)
            }]
        }

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="analyze_market",
            description="Analyze market trends",
            inputSchema={
                "type": "object",
                "properties": {
                    "market": {"type": "string"},
                    "timeframe": {"type": "string"}
                },
                "required": ["market"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "analyze_market":
        return await analyze_market(**arguments)
```

## 🎯 When to Use

### Ideal Scenarios

- ✅ Multiple agents need same tools
- ✅ Dynamic tool discovery required
- ✅ Standardization across team
- ✅ Context sharing between agents
- ✅ Extensible tool ecosystem

### Not Recommended For

- ❌ Single agent, fixed tools
- ❌ Simple, static workflows
- ❌ Performance-critical paths (overhead)
- ❌ No tool reuse needed

## 📊 Comparison

### MCP vs Direct Tool Integration

| Aspect              | MCP            | Direct Integration |
| ------------------- | -------------- | ------------------ |
| **Setup**           | More complex   | Simple             |
| **Flexibility**     | High (dynamic) | Low (static)       |
| **Reusability**     | Excellent      | Poor               |
| **Discovery**       | Automatic      | Manual             |
| **Overhead**        | Some           | Minimal            |
| **Standardization** | Yes            | No                 |

### When to Choose MCP

- Multiple agents
- Growing tool ecosystem
- Need standardization
- Long-term maintainability

### When to Choose Direct

- Single agent
- Few, stable tools
- Performance critical
- Quick prototype

## 🚀 Future Enhancements

### Planned for Marketing Agent

1. **MCP Server**: Expose research, campaigns, brand guidelines
2. **Tool Registry**: Centralize all tools (Tavily, Veo, etc.)
3. **Context Sharing**: Share research between ideation phases
4. **Dynamic Discovery**: Agents find tools at runtime

### Research Directions

- **Semantic Tool Discovery**: AI-powered tool matching
- **Automatic Tool Composition**: Chain tools intelligently
- **Cross-Platform MCP**: Connect different agent frameworks
- **MCP Marketplace**: Share and discover community tools

---

**Status**: ❌ Not Implemented  
**Priority**: 🟡 Medium  
**Difficulty**: Medium-High  
**Impact**: High  
**Next Steps**: Implement basic MCP server for research and brand resources
