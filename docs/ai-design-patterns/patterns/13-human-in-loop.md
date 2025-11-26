# Human-in-the-Loop (HITL) Pattern

## 📖 Overview

The Human-in-the-Loop pattern integrates human judgment, approval, and feedback into the AI agent's workflow, ensuring control, safety, and quality for critical decisions.

**Category**: Integration Pattern  
**Difficulty**: Medium  
**Impact**: High

## 🎯 Core Concept

```
Agent Execution → [Pause for Human] → Human Review/Edit → Resume Execution
                       ↑
                  Approval / Feedback
```

Types of HITL:

1. **Approval**: Yes/No gate before critical actions
2. **Review**: Edit/Refine intermediate outputs
3. **Feedback**: Provide guidance to steer direction
4. **Input**: Provide missing information

## 💡 Why This Pattern?

### Problems It Solves

- **Hallucinations**: Catching AI errors before they propagate
- **Safety Risks**: Preventing dangerous actions
- **Ambiguity**: resolving unclear requirements
- **Accountability**: Human sign-off on decisions

### Benefits

- ✅ **Quality Control**: Higher standard of output
- ✅ **Safety**: Critical stop mechanism
- ✅ **Trust**: Users feel in control
- ✅ **Learning**: Feedback data for improvement

## 🏗️ Architecture

### LangGraph Implementation

LangGraph provides native support for HITL via `interrupt_before` and `interrupt_after`.

```python
# Define graph with interrupt
workflow = StateGraph(State)
workflow.add_node("generate", generate_node)
workflow.add_node("review", review_node)
workflow.add_node("publish", publish_node)

workflow.add_edge("generate", "review")
workflow.add_edge("review", "publish")

# Compile with interrupt
app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["publish"]  # Pause before publishing
)
```

### Execution Flow

1. **Run**: `app.invoke(input)` runs until "review" node completes
2. **Pause**: Execution stops at "publish" boundary
3. **Wait**: System waits for user input
4. **Resume**: `app.invoke(Command(resume="approved"))` continues

## 📊 Implementation in Marketing Agent

### Current Status

**Status**: ❌ Not Implemented  
**Priority**: 🟡 Medium  
**Potential**: High

### Potential Implementation Points

1. **Campaign Approval**: Before saving final files
2. **Budget Check**: If estimated cost > threshold
3. **Video Generation**: Review prompt before generating (costly)
4. **Critique Review**: Validate AI critique

```python
# Example: Video Generation HITL
async def video_node(state):
    prompt = generate_prompt(state)

    # Pause for user to review prompt
    # User can edit prompt or cancel
    user_input = interrupt({"prompt": prompt, "cost": 0.20})

    if user_input["action"] == "approve":
        video = await veo.generate(user_input["prompt"])
        return {"video": video}
    else:
        return {"error": "User cancelled"}
```

## 🔧 Implementation Guide

### Step 1: Identify Checkpoints

Determine where human input adds value:

- High cost actions (API calls)
- Irreversible actions (Sending email, deploying)
- Creative direction (Ideation)
- Safety checks (Compliance)

### Step 2: Design Interaction

Define what the human sees and does:

- **Read-only**: View output, Approve/Reject
- **Edit**: Modify output before proceeding
- **Steer**: Give instructions for next step

### Step 3: Implement Persistence

HITL requires state persistence (Checkpointer) to resume later.

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)
```

## 🎓 Best Practices

### Do's ✅

- **Provide Context**: Show user _why_ they are reviewing
- **Make it Easy**: One-click approve/reject
- **Allow Editing**: Don't just reject, let them fix
- **Timeout**: Handle cases where human doesn't respond
- **Batch Reviews**: Group multiple approvals

### Don'ts ❌

- **Don't Overuse**: Too many stops annoy users
- **Don't Lose State**: Ensure seamless resume
- **Don't Be Vague**: Clear call to action
- **Don't Block Forever**: Have timeouts/defaults

## 📈 Performance & Metrics

### Metrics to Track

- **Wait Time**: How long execution pauses
- **Rejection Rate**: % of AI outputs rejected
- **Edit Distance**: How much humans change AI output
- **Intervention Rate**: Frequency of HITL triggers

### Optimization Tips

```python
# Adaptive HITL
if confidence_score < 0.8:
    interrupt_for_review()  # Low confidence -> Human check
else:
    proceed_automatically() # High confidence -> Auto
```

## 🚀 Advanced Techniques

### 1. Steering

Allow user to modify state during pause.

```python
# User updates state
app.update_state(thread_id, {"budget": 5000})
app.invoke(Command(resume=True))
```

### 2. Time Travel

Allow user to rewind and try different path.

```python
# Go back to previous step
history = app.get_state_history(thread_id)
app.update_state(history[2].config, ...) # Revert to 2 steps ago
```

### 3. Multi-User Review

Require consensus from multiple humans.

## 🔬 Research & References

### Key Resources

- [LangGraph Human-in-the-loop](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/)
- [Designing Human-AI Systems](https://design.google/library/ai/)

### Related Patterns

- **Exception Handling**: Human can resolve exceptions
- **Guardrails**: Human as final guardrail
- **Evaluation**: Human feedback as ground truth

## 💻 Code Examples

### Basic Approval Workflow

```python
from typing import TypedDict, Literal

class State(TypedDict):
    content: str
    status: str

def writer(state):
    return {"content": "Generated content...", "status": "pending"}

def human_review(state):
    # This node doesn't do much, just a placeholder for the pause
    pass

def publisher(state):
    return {"status": "published"}

workflow = StateGraph(State)
workflow.add_node("write", writer)
workflow.add_node("publish", publisher)

workflow.add_edge("write", "publish")

# Interrupt before publish
app = workflow.compile(interrupt_before=["publish"])

# Execution
thread = {"configurable": {"thread_id": "1"}}
app.invoke({"content": ""}, thread)

# ... System pauses ...

# User reviews and approves
app.invoke(Command(resume="approved"), thread)
```

## 🎯 When to Use

### Ideal Scenarios

- ✅ Content moderation
- ✅ Code deployment
- ✅ Financial transactions
- ✅ Medical/Legal advice
- ✅ Creative collaboration

### Not Recommended For

- ❌ High-frequency trading
- ❌ Real-time processing (latency)
- ❌ Trivial decisions
- ❌ Fully autonomous background tasks

## 📊 Comparison

### HITL vs Guardrails

| Aspect          | HITL               | Guardrails    |
| --------------- | ------------------ | ------------- |
| **Agent**       | Human              | Code/Model    |
| **Speed**       | Slow               | Fast          |
| **Cost**        | High (Human time)  | Low (Compute) |
| **Flexibility** | High               | Low (Rules)   |
| **Context**     | Full understanding | Limited       |

## 🚀 Future Enhancements

### Planned for Marketing Agent

1. **Prompt Review**: Review video prompts before generation
2. **Budget Approval**: Confirm spend for batch generation
3. **Idea Selection**: Human picks best ideas to proceed
4. **Final Polish**: Human edits markdown before "completion"

---

**Status**: ❌ Not Implemented  
**Priority**: 🟡 Medium  
**Difficulty**: Medium  
**Impact**: High  
**Next Steps**: Add interrupt before video generation in CLI
