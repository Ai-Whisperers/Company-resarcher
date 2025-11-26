# Reasoning Techniques Pattern

## 📖 Overview

Reasoning techniques enhance an agent's ability to solve complex problems by structuring its thought process, rather than just generating an immediate answer.

**Category**: Production Pattern  
**Difficulty**: Medium-High  
**Impact**: High

## 🎯 Core Concept

```
Input → [Structured Reasoning Process] → Output
```

Instead of `Input -> Output` (Zero-shot), we force the model to "think" before answering.

Key Techniques:

1. **Chain of Thought (CoT)**: Step-by-step reasoning
2. **Tree of Thoughts (ToT)**: Exploring multiple branches
3. **Self-Consistency**: Majority vote from multiple paths
4. **ReAct**: Interleaving reasoning and acting
5. **Debate**: Multiple agents arguing to find truth

## 💡 Why This Pattern?

### Problems It Solves

- **Hallucinations**: Jumping to conclusions
- **Math/Logic Errors**: Failing at multi-step problems
- **Inconsistency**: Random outputs
- **Opacity**: "Black box" decisions

### Benefits

- ✅ **Accuracy**: Significantly higher on complex tasks
- ✅ **Explainability**: We see the "why"
- ✅ **Debuggability**: Can pinpoint where logic failed
- ✅ **Robustness**: Better handling of edge cases

## 🏗️ Architecture

### 1. Chain of Thought (CoT)

```python
prompt = """
Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?

A: Roger started with 5 balls.
2 cans of 3 tennis balls each is 2 * 3 = 6 tennis balls.
5 + 6 = 11.
The answer is 11.
"""
```

### 2. Tree of Thoughts (ToT)

```python
def tree_of_thoughts(problem):
    # 1. Decompose
    steps = decompose(problem)

    current_states = [initial_state]

    for step in steps:
        # 2. Generate candidates (branches)
        next_states = []
        for state in current_states:
            candidates = generate_candidates(state, step)
            next_states.extend(candidates)

        # 3. Evaluate candidates (pruning)
        current_states = evaluate_and_filter(next_states)

    return best(current_states)
```

## 📊 Implementation in Marketing Agent

### Current Status

**Status**: 🟡 Partial (Implicit)  
**Priority**: Medium  
**Potential**: High

### Current Implementation

- **Implicit CoT**: Some prompts ask for "Rationale" or "Step-by-step"
- **ReAct**: Graph workflow is essentially ReAct (Reason -> Tool -> Reason)

### Potential Implementation

**1. Ideation Rationale**
Explicitly ask for reasoning before concept.

```python
prompt = """
Task: Generate a campaign concept.

Step 1: Analyze the target audience needs.
Step 2: Identify cultural trends in Paraguay.
Step 3: Connect brand values to trends.
Step 4: Generate the concept based on connection.

Output format:
{
  "reasoning": "...",
  "concept": "..."
}
"""
```

**2. Critique Debate**
Have two critic agents debate the score.

```python
critic_a = "I give it 8/10 because..."
critic_b = "I give it 6/10 because..."
moderator = "Considering both, the final score is 7/10."
```

## 🔧 Implementation Guide

### Step 1: Zero-Shot CoT

Simply add "Let's think step by step" to the prompt.

```python
response = await ai.generate(f"{task}\n\nLet's think step by step.")
```

### Step 2: Few-Shot CoT

Provide examples of reasoning.

```python
prompt = f"""
Task: {task}

Example:
Task: [Similar Task]
Thought: First I need to... Then I will... Finally...
Answer: [Result]

Your Turn:
Thought:
"""
```

### Step 3: Programmatic Reasoning (ToT)

Implement search algorithms (BFS/DFS) over thought space.

```python
class ThoughtNode:
    def __init__(self, content, parent=None):
        self.content = content
        self.parent = parent
        self.score = 0
        self.children = []
```

## 🎓 Best Practices

### Do's ✅

- **Use for Logic**: Math, planning, coding
- **Separate Thought from Answer**: Parse them separately
- **Verify Reasoning**: Sometimes reasoning is right but answer wrong (or vice versa)
- **Limit Depth**: ToT can be expensive
- **Use Strong Models**: Reasoning requires capability (GPT-4, Claude 3.5)

### Don'ts ❌

- **Don't Use for Simple Tasks**: Overkill and slow
- **Don't Ignore Cost**: More tokens = more cost
- **Don't Trust Blindly**: Hallucination in reasoning is possible

## 📈 Performance & Metrics

### Metrics to Track

- **Accuracy**: Correctness of final answer
- **Token Usage**: Cost of reasoning
- **Latency**: Time to think
- **Reasoning Quality**: Human eval of logic

### Optimization Tips

```python
# Self-Consistency
# Generate 5 CoT paths and take majority vote
responses = await asyncio.gather(*[generate_cot(task) for _ in range(5)])
final_answer = majority_vote(responses)
```

## 🚀 Advanced Techniques

### 1. Algorithm of Thoughts (AoT)

Using algorithmic examples (DFS, BFS) in context to guide LLM search.

### 2. Skeleton-of-Thought

Generate a skeleton outline first, then fill in details in parallel.

### 3. System 2 Attention

Ask model to re-attend to context and filter irrelevant info before reasoning.

## 🔬 Research & References

### Key Papers

- **Chain-of-Thought** (Wei et al., 2022)
- **Tree of Thoughts** (Yao et al., 2023)
- **Self-Consistency** (Wang et al., 2022)
- **ReAct** (Yao et al., 2022)

### Related Patterns

- **Reflection**: Critiquing the reasoning
- **Planning**: Reasoning about future steps
- **Multi-Agent**: Distributed reasoning

## 💻 Code Examples

### Simple CoT Wrapper

```python
async def generate_with_reasoning(prompt, model):
    enhanced_prompt = f"""
    {prompt}

    Please structure your response as:
    <reasoning>
    Explain your step-by-step logic here.
    </reasoning>

    <answer>
    Your final answer here.
    </answer>
    """

    response = await model.generate(enhanced_prompt)
    return parse_xml(response)
```

## 🎯 When to Use

### Ideal Scenarios

- ✅ Complex planning
- ✅ Math/Logic puzzles
- ✅ Debugging code
- ✅ Strategic decisions
- ✅ Explaining "Why"

### Not Recommended For

- ❌ Creative writing (sometimes hinders flow)
- ❌ Simple lookup
- ❌ Chat chit-chat
- ❌ Latency-critical apps

## 📊 Comparison

### CoT vs ToT

| Aspect         | Chain of Thought | Tree of Thoughts     |
| -------------- | ---------------- | -------------------- |
| **Structure**  | Linear           | Branching            |
| **Cost**       | Low (1x)         | High (Nx)            |
| **Complexity** | Simple           | Complex              |
| **Power**      | Medium           | High                 |
| **Use Case**   | General Logic    | Hard Search/Planning |

## 🚀 Future Enhancements

### Planned for Marketing Agent

1. **Strategic Reasoning**: Use CoT for "Strategic Enrichment" phase
2. **Debate Mode**: Multi-agent critique for high-stakes campaigns
3. **Self-Consistency**: Run ideation 3x and pick best

---

**Status**: 🟡 Partial (Implicit)  
**Priority**: Medium  
**Difficulty**: Medium-High  
**Impact**: High  
**Next Steps**: Add explicit `<reasoning>` tags to ideation prompts
