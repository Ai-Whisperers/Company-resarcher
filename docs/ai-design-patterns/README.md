# AI Agentic Design Patterns

## 📚 Overview

This documentation provides a comprehensive guide to the **21 Agentic Design Patterns** used in modern AI systems. These patterns are derived from industry best practices (Andrew Ng, LangChain, Anthropic) and are categorized by their role in the agent lifecycle.

## 🎯 Pattern Categories

### Part 1: Core Patterns (Execution)

Foundational patterns for building functional agents.

1. **[Prompt Chaining](patterns/01-prompt-chaining.md)**: Breaking tasks into sequential steps.
2. **[Routing](patterns/02-routing.md)**: Directing tasks to specialized agents.
3. **[Parallelization](patterns/03-parallelization.md)**: Executing independent tasks concurrently.
4. **[Reflection](patterns/04-reflection.md)**: Self-correction and critique.
5. **[Tool Use](patterns/05-tool-use.md)**: Interacting with external environments.
6. **[Planning](patterns/06-planning.md)**: Decomposing complex goals into steps.
7. **[Multi-Agent Collaboration](patterns/07-multi-agent.md)**: Teams of agents working together.

### Part 2: Advanced Patterns (Intelligence)

Patterns that enhance the agent's cognitive capabilities. 8. **[Memory Management](patterns/08-memory.md)**: Short-term, episodic, and long-term memory. 9. **[Learning & Adaptation](patterns/09-learning-adaptation.md)**: Improving performance over time. 10. **[Model Context Protocol (MCP)](patterns/10-model-context-protocol.md)**: Standardized tool/resource access. 11. **[Goal Setting & Monitoring](patterns/11-goal-monitoring.md)**: Tracking objectives and drift.

### Part 3: Integration Patterns (Reliability)

Patterns for robust system integration. 12. **[Exception Handling & Recovery](patterns/12-exception-handling.md)**: Graceful failure management. 13. **[Human-in-the-Loop](patterns/13-human-in-loop.md)**: Approval, review, and steering. 14. **[Knowledge Retrieval (RAG)](patterns/14-knowledge-retrieval.md)**: Accessing external knowledge bases.

### Part 4: Production Patterns (Scale)

Patterns for deploying and scaling agents. 15. **[Inter-Agent Communication (A2A)](patterns/15-inter-agent-comm.md)**: Protocols for agent exchange. 16. **[Resource-Aware Optimization](patterns/16-resource-optimization.md)**: Cost/latency routing. 17. **[Reasoning Techniques](patterns/17-reasoning-techniques.md)**: CoT, ToT, and advanced logic. 18. **[Guardrails & Safety](patterns/18-guardrails-safety.md)**: Security and compliance. 19. **[Evaluation & Monitoring](patterns/19-evaluation-monitoring.md)**: Metrics and LLM-as-a-Judge. 20. **[Prioritization](patterns/20-prioritization.md)**: Dynamic task scheduling. 21. **[Exploration & Discovery](patterns/21-exploration-discovery.md)**: Mapping problem spaces.

## 📊 Implementation Status Matrix

| Pattern                 | Status     | Priority | Implementation in Marketing Agent          |
| ----------------------- | ---------- | -------- | ------------------------------------------ |
| **01. Prompt Chaining** | ✅ Done    | High     | `campaign_graph.py` (Research -> Ideation) |
| **02. Routing**         | 🟡 Partial | Medium   | Implicit in graph edges                    |
| **03. Parallelization** | ✅ Done    | High     | `batch_video_agent.py` (Video Gen)         |
| **04. Reflection**      | ✅ Done    | High     | `campaign_graph.py` (Critique Node)        |
| **05. Tool Use**        | ✅ Done    | High     | Tavily, Veo, File System                   |
| **06. Planning**        | ✅ Done    | High     | `campaign_graph.py` (Strategic Enrichment) |
| **07. Multi-Agent**     | ✅ Done    | High     | Research, Ideation, Critique Agents        |
| **08. Memory**          | ✅ Done    | Medium   | `campaign_memory.py` (FAISS)               |
| **09. Learning**        | ❌ Todo    | Medium   | Planned: Few-shot optimization             |
| **10. MCP**             | ❌ Todo    | Medium   | Planned: Research resource server          |
| **11. Goals**           | ❌ Todo    | Medium   | Planned: Completeness checks               |
| **12. Exceptions**      | 🟡 Partial | High     | Basic try/except blocks                    |
| **13. HITL**            | ❌ Todo    | Medium   | Planned: Video approval                    |
| **14. RAG**             | ✅ Done    | High     | `campaign_memory.py`                       |
| **15. A2A Comm**        | ✅ Done    | High     | Shared State (Blackboard)                  |
| **16. Optimization**    | ✅ Done    | High     | Hybrid (Groq/OpenAI/Veo)                   |
| **17. Reasoning**       | 🟡 Partial | Medium   | Implicit CoT in prompts                    |
| **18. Safety**          | ❌ Todo    | Critical | Planned: PII redaction                     |
| **19. Evaluation**      | 🟡 Partial | High     | Critique scores (0-10)                     |
| **20. Prioritization**  | ❌ Todo    | Low      | Planned: Batch sorting                     |
| **21. Exploration**     | ❌ Todo    | Low      | Planned: Trend discovery                   |

## 🚀 Learning Path

1. **Beginner**: Start with **Prompt Chaining** and **Tool Use**. These are the building blocks.
2. **Intermediate**: Add **Reflection** and **Memory** to make agents smarter.
3. **Advanced**: Implement **Planning** and **Multi-Agent** for complex workflows.
4. **Expert**: Optimize with **Resource-Awareness** and **Evaluation** pipelines.

## 📚 References

- [Andrew Ng's Agentic Design Patterns](https://www.deeplearning.ai/the-batch/issue-242/)
- [LangChain Blog](https://blog.langchain.dev/)
- [Anthropic Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Prompt Advisers](https://github.com/promptadvisers/agentic-design-patterns-docs)
