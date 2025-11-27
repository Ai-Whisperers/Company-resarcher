# Goal Setting & Monitoring Pattern

## 📖 Overview

Agents break down high-level objectives into measurable goals, track progress, detect drift, and course-correct to ensure successful task completion.

**Category**: Intelligence Pattern  
**Difficulty**: Medium  
**Impact**: Medium-High

## 🎯 Core Concept

```
Objective → [Goal Decomposition] → Goals (KPIs)
                                      ↓
                                   Execution
                                      ↓
                                   [Monitor] → On Track?
                                      ↓           ↓
                                   Continue    Re-plan
```

Unlike simple planning, this involves **active state monitoring** against success criteria.

## 💡 Why This Pattern?

### Problems It Solves

- **Getting Lost**: Agent forgetting the original goal in long conversations
- **Looping**: Getting stuck in repetitive actions
- **Inefficiency**: Taking the long route
- **Drift**: Slowly deviating from requirements

### Benefits

- ✅ **Focus**: Keeps agent aligned with objective
- ✅ **Efficiency**: Detects stalls early
- ✅ **Autonomy**: Self-correction without human help
- ✅ **Transparency**: Clear status reporting

## 🏗️ Architecture

### Components

1. **Goal Manager**: Stores and tracks goals
2. **Monitor**: Checks state against goals
3. **Planner**: Updates plan if goals missed

```python
class Goal:
    description: str
    status: str # pending, active, completed, failed
    criteria: List[str]
    deadline: datetime
```

## 📊 Implementation in Marketing Agent

### Current Status

**Status**: ❌ Not Implemented  
**Priority**: 🟡 Medium  
**Potential**: Medium

### Potential Implementation

**Campaign Goals**:

1. **Completeness**: All 13 fields filled?
2. **Quality**: Score > 7.0?
3. **Constraints**: Budget within limits?
4. **Brand**: Nestlé guidelines met?

```python
# Goal Monitoring in Graph
async def monitor_node(state):
    goals = state["goals"]
    current_idea = state["current_idea"]

    # Check completeness
    if missing_fields(current_idea):
        return Command(goto="ideation", update={"feedback": "Missing fields"})

    # Check quality
    if current_idea.score < 7.0:
        return Command(goto="refinement", update={"feedback": "Score too low"})

    return Command(goto="end")
```

## 🔧 Implementation Guide

### Step 1: Define Goals Explicitly

```python
goals = [
    Goal(id="g1", desc="Research market trends", status="pending"),
    Goal(id="g2", desc="Generate 3 concepts", status="pending"),
    Goal(id="g3", desc="Select best concept", status="pending")
]
```

### Step 2: Implement Monitor Loop

```python
async def execute_with_monitoring(agent, task):
    while not goals_met():
        action = agent.act()
        state = execute(action)

        # Monitor
        progress = check_progress(state, goals)
        if progress.stalled:
            agent.replan()

        update_goals(goals, state)
```

### Step 3: Drift Detection

```python
def check_drift(original_goal, current_path):
    similarity = semantic_similarity(original_goal, current_path)
    if similarity < 0.7:
        raise GoalDriftError("Agent is deviating from goal")
```

## 🎓 Best Practices

### Do's ✅

- **SMART Goals**: Specific, Measurable, Achievable, Relevant, Time-bound
- **Check Often**: Monitor after every major step
- **Allow Retries**: Don't fail immediately
- **Visualize**: Show user which goals are done

### Don'ts ❌

- **Don't Be Rigid**: Allow alternative paths to same goal
- **Don't Infinite Loop**: Set max attempts per goal
- **Don't Hide Failures**: Report _why_ a goal failed

## 📈 Performance & Metrics

### Metrics to Track

- **Goal Completion Rate**: % of goals achieved
- **Steps per Goal**: Efficiency
- **Re-plan Rate**: How often plan changed
- **Drift Incidents**: Frequency of deviation

## 🚀 Advanced Techniques

### 1. Hierarchical Goals

Goals -> Sub-goals -> Tasks -> Actions.
Monitor at each level.

### 2. Dynamic Goal Adjustment

If a goal proves impossible, the agent negotiates a relaxed goal.
"I can't find 10 competitors, but I found 5. Is that okay?"

### 3. Multi-Objective Optimization

Balancing conflicting goals (e.g., "High Quality" vs "Low Cost").

## 🔬 Research & References

### Key Papers

- **Voyager** (Wang et al., 2023): Curriculum learning with goals
- **AutoGPT**: Goal-oriented autonomous agent

### Related Patterns

- **Planning**: Creating the path to goals
- **Reflection**: Checking if goals met
- **Evaluation**: Measuring success

## 💻 Code Examples

### Simple Goal Tracker

```python
class GoalTracker:
    def __init__(self, objectives):
        self.objectives = {obj: False for obj in objectives}

    def update(self, state):
        for obj, done in self.objectives.items():
            if not done and self.check_condition(obj, state):
                self.objectives[obj] = True
                print(f"Goal Achieved: {obj}")

    def check_condition(self, objective, state):
        # Logic to check if objective is met
        if objective == "research_done":
            return len(state.get("research", [])) > 0
        return False

    def is_complete(self):
        return all(self.objectives.values())
```

## 🎯 When to Use

### Ideal Scenarios

- ✅ Long-running tasks
- ✅ Multi-step workflows
- ✅ Autonomous agents
- ✅ Complex requirements

### Not Recommended For

- ❌ Simple Q&A
- ❌ Single-step tools
- ❌ Stateless interactions

## 📊 Comparison

### Planning vs Goal Setting

| Aspect      | Planning         | Goal Setting      |
| ----------- | ---------------- | ----------------- |
| **Focus**   | How (Steps)      | What (Outcomes)   |
| **State**   | Static (Initial) | Dynamic (Runtime) |
| **Action**  | Decomposition    | Monitoring        |
| **Failure** | Execution Error  | Criteria Missed   |

## 🚀 Future Enhancements

### Planned for Marketing Agent

1. **Progress Bar**: Show goal completion in CLI
2. **Completeness Check**: Auto-verify all fields present
3. **Constraint Monitor**: Ensure branding rules respected

## ⚠️ Edge Cases & Pitfalls

### Common Pitfalls

1.  **Zeno's Paradox**: The agent gets infinitely closer to the goal but never finishes (e.g., "Polish the text" forever).
    - _Fix_: Define a "Good Enough" threshold or max iterations.
2.  **Goal Conflict**: Goal A (Speed) contradicts Goal B (Quality).
    - _Fix_: Assign weights or priorities to goals.
3.  **False Positives**: The agent thinks it's done because it misunderstood the criteria.
    - _Fix_: Use an independent "Verifier" agent to confirm completion.

### Edge Cases

- **Moving Goalposts**: The user changes the goal mid-task.
- **Impossible Goal**: "Find a unicorn." (Need early exit/failure detection).

## 🧪 Testing Strategy

### 1. Drift Simulation

Intentionally steer the agent off-course and see if it corrects itself.

```python
async def test_correction():
    agent.state = "off_topic"
    action = await monitor.check(agent.state)
    assert action == "realign"
```

### 2. Completion Check

Verify that the monitor correctly identifies a finished state.

### 3. Eval Metrics

- **Time to Completion**: How fast did it reach the goal?
- **Correction Rate**: How many times did it have to self-correct?

## 💻 Runnable Example

View a working example of Goal Monitoring:
[11_goal_monitoring.py](../examples/11_goal_monitoring.py)

---

**Status**: ❌ Not Implemented  
**Priority**: 🟡 Medium  
**Difficulty**: Medium  
**Impact**: Medium  
**Next Steps**: Add completeness check in `ideation_node`
