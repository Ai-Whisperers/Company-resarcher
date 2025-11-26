# Inter-Agent Communication (A2A) Pattern

## 📖 Overview

The Inter-Agent Communication (A2A) pattern defines how multiple autonomous agents exchange messages, share state, and coordinate actions to solve complex problems.

**Category**: Production Pattern  
**Difficulty**: High  
**Impact**: Very High

## 🎯 Core Concept

```
Agent A  ◄─── [Protocol / Message Bus] ───►  Agent B
   │                                            │
   └──────────►  Shared State / Memory  ◄───────┘
```

Communication styles:

1. **Direct Messaging**: Request/Response (RPC)
2. **Broadcasting**: Pub/Sub events
3. **Blackboard**: Shared state/memory
4. **Orchestration**: Central coordinator

## 💡 Why This Pattern?

### Problems It Solves

- **Silos**: Agents unaware of each other's work
- **Coordination**: Managing dependencies between tasks
- **Scalability**: Adding new agents without breaking existing ones
- **Complexity**: Decomposing monolithic tasks

### Benefits

- ✅ **Decoupling**: Agents evolve independently
- ✅ **Scalability**: Easy to add more agents
- ✅ **Specialization**: Agents focus on specific domains
- ✅ **Robustness**: Failure in one agent doesn't kill system

## 🏗️ Architecture

### Communication Protocols

**1. Structured Messages (JSON)**

```json
{
  "sender": "research_agent",
  "recipient": "ideation_agent",
  "type": "research_complete",
  "payload": {
    "market_trends": [...]
  },
  "timestamp": "2024-11-26T10:00:00Z"
}
```

**2. LangGraph State (Blackboard)**
Current implementation in Marketing Agent uses a shared state object passed between nodes.

```python
class CampaignState(TypedDict):
    project_id: str
    research: dict
    concepts: list
    # All agents read/write to this shared state
```

### Interaction Patterns

**A. Handoff (Relay)**
Agent A finishes, passes context to Agent B.
`Research -> Synthesis -> Ideation`

**B. Chat (Dialogue)**
Agents converse to solve a problem.
`Writer <-> Editor` (Iterative refinement)

**C. Swarm (Collective)**
Many agents work in parallel on subtasks.
`Search Agents (x5) -> Aggregator`

## 📊 Implementation in Marketing Agent

### Current Status

**Status**: ✅ Implemented (Shared State)  
**Priority**: High  
**Potential**: High

### Current Implementation (LangGraph)

```python
# Shared State (Blackboard Pattern)
class CampaignState(TypedDict):
    messages: Annotated[list, add_messages]
    research: dict
    concepts: list

# Agent Node
async def research_node(state: CampaignState):
    # Read from state
    query = state["messages"][-1].content

    # Do work
    result = await research(query)

    # Write to state
    return {"research": result}

# Graph definition (Orchestration)
graph.add_edge("research", "ideation")
```

## 🔧 Implementation Guide

### Step 1: Define Protocol

Standardize how agents talk.

```python
class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    ERROR = "error"
    STATUS_UPDATE = "status_update"

@dataclass
class AgentMessage:
    id: str
    sender: str
    recipient: str
    type: MessageType
    content: Any
    metadata: dict = field(default_factory=dict)
```

### Step 2: Choose Transport

- **In-Memory**: Direct function calls / Shared object (LangGraph)
- **Message Queue**: RabbitMQ, Kafka, Redis (Distributed)
- **HTTP/RPC**: REST, gRPC (Microservices)

### Step 3: Implement Handlers

```python
class Agent:
    async def receive(self, message: AgentMessage):
        handler = self.handlers.get(message.type)
        if handler:
            return await handler(message)

    async def send(self, recipient: str, content: Any):
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            content=content
        )
        await bus.publish(msg)
```

## 🎓 Best Practices

### Do's ✅

- **Standardize Schema**: Strict message formats
- **Idempotency**: Handle duplicate messages safely
- **Timeouts**: Don't wait forever for replies
- **Tracing**: Correlation IDs to track flows
- **Version Protocol**: Allow evolution

### Don'ts ❌

- **Don't Share Mutable State**: Unless using strict locking
- **Don't Create Cycles**: Infinite message loops
- **Don't Tight Couple**: Agents shouldn't know internal details of others
- **Don't Ignore Failures**: Handle delivery failures

## 📈 Performance & Metrics

### Metrics to Track

- **Message Latency**: Time from send to receive
- **Throughput**: Messages per second
- **Error Rate**: Failed deliveries
- **Queue Depth**: Backlog of messages

### Optimization Tips

```python
# Batching
async def send_batch(messages):
    # Send multiple messages in one network call
    await bus.publish_batch(messages)

# Compression
if len(payload) > 1024:
    payload = compress(payload)
```

## 🚀 Advanced Techniques

### 1. Semantic Routing

Route messages based on content meaning, not just address.

```python
# Router Agent
if "budget" in message.content:
    route_to("finance_agent")
elif "creative" in message.content:
    route_to("design_agent")
```

### 2. Negotiation Protocol

Agents negotiate to accept tasks.

```python
# Contract Net Protocol
1. Manager -> Broadcast: "Task Available: Video Gen"
2. Agent A -> Manager: "I can do it for $0.20"
3. Agent B -> Manager: "I can do it for $0.15"
4. Manager -> Agent B: "Awarded"
```

### 3. Shared Knowledge Graph

Agents communicate by updating a shared graph knowledge base.

## 🔬 Research & References

### Key Papers

- **Communicative Agents** (Park et al., 2023): Generative Agents
- **MetaGPT** (Hong et al., 2023): SOP-based communication
- **CAMEL** (Li et al., 2023): Role-playing agents

### Related Patterns

- **Multi-Agent**: The structural pattern
- **MCP**: The protocol for tools/resources
- **Routing**: Directing the messages

## 💻 Code Examples

### LangGraph State Passing (Current)

```python
# Simple linear handoff
def agent_a(state):
    return {"data_a": "result"}

def agent_b(state):
    # Agent B uses Agent A's output
    prev_result = state["data_a"]
    return {"data_b": process(prev_result)}

workflow.add_edge("agent_a", "agent_b")
```

### Event Bus (Distributed)

```python
# Redis Pub/Sub
class EventBus:
    async def publish(self, channel, message):
        await redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel, callback):
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        async for msg in pubsub.listen():
            if msg['type'] == 'message':
                await callback(json.loads(msg['data']))
```

## 🎯 When to Use

### Ideal Scenarios

- ✅ Complex workflows with multiple steps
- ✅ Distributed systems
- ✅ Team of specialized agents
- ✅ Asynchronous processing

### Not Recommended For

- ❌ Single agent scripts
- ❌ Tightly coupled logic (use functions)
- ❌ Latency-sensitive loops

## 📊 Comparison

### Shared State vs Message Passing

| Aspect          | Shared State (Blackboard) | Message Passing     |
| --------------- | ------------------------- | ------------------- |
| **Coupling**    | High (Schema dependency)  | Low (Protocol only) |
| **Simplicity**  | High                      | Medium              |
| **Concurrency** | Hard (Race conditions)    | Easy (Actor model)  |
| **Visibility**  | Global                    | Local               |
| **Use Case**    | Monolithic / Graph        | Distributed / Swarm |

## 🚀 Future Enhancements

### Planned for Marketing Agent

1. **Standardized Message Schema**: Formalize state structure
2. **Tracing**: Add OpenTelemetry for agent flows
3. **Error Propagation**: Better error messages between nodes

### Research Directions

- **Language-based Communication**: Agents talking in natural language (English) vs JSON
- **Dynamic Team Formation**: Agents finding each other to form squads

---

**Status**: ✅ Implemented (Shared State)  
**Priority**: High  
**Difficulty**: High  
**Impact**: Very High  
**Next Steps**: Formalize state schema with Pydantic
