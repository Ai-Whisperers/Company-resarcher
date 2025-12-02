"""
Hierarchical planning system for complex multi-step tasks.

Implements Manager/Planner/Executor pattern for task decomposition and execution.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .ai_client import BaseAIClient, get_ai_manager
from .events import EventType, get_event_stream
from .logger import setup_logger

logger = setup_logger("hierarchical_planner")


class StepStatus(str, Enum):
    """Status of a plan step."""

    PENDING = "pending"
    READY = "ready"  # Dependencies met, ready to execute
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepPriority(str, Enum):
    """Priority levels for steps."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PlanStep:
    """A single step in a plan."""

    step_id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)  # step_ids this depends on
    status: StepStatus = StepStatus.PENDING
    priority: StepPriority = StepPriority.MEDIUM
    executor_type: Optional[str] = None  # Type of executor to use
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "priority": self.priority.value,
            "executor_type": self.executor_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        """Create from dictionary."""
        return cls(
            step_id=data["step_id"],
            name=data["name"],
            description=data["description"],
            dependencies=data.get("dependencies", []),
            status=StepStatus(data.get("status", "pending")),
            priority=StepPriority(data.get("priority", "medium")),
            executor_type=data.get("executor_type"),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            error=data.get("error"),
        )


@dataclass
class Plan:
    """A hierarchical plan with steps forming a DAG."""

    plan_id: str
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "created"  # created, in_progress, completed, failed

    def add_step(self, step: PlanStep):
        """Add a step to the plan."""
        self.steps.append(step)

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute (dependencies met)."""
        completed_ids = {
            s.step_id for s in self.steps if s.status == StepStatus.COMPLETED
        }
        ready = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            # Check if all dependencies are completed
            if all(dep_id in completed_ids for dep_id in step.dependencies):
                ready.append(step)
        return ready

    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return all(
            s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
            for s in self.steps
        )

    def has_failed(self) -> bool:
        """Check if any step has failed."""
        return any(s.status == StepStatus.FAILED for s in self.steps)

    def get_progress(self) -> float:
        """Get completion progress (0.0 to 1.0)."""
        if not self.steps:
            return 0.0
        completed = sum(
            1 for s in self.steps
            if s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
        )
        return completed / len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "progress": self.get_progress(),
        }


# Executor callback type
ExecutorCallback = Callable[[PlanStep, Dict[str, Any]], Awaitable[Dict[str, Any]]]


class Manager:
    """
    High-level task decomposition.

    Breaks down complex goals into sub-goals for planners.
    """

    def __init__(self, ai_client: Optional[BaseAIClient] = None):
        """Initialize the manager."""
        self.ai = ai_client or get_ai_manager()

    async def decompose_goal(
        self,
        goal: str,
        context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Decompose a high-level goal into sub-goals.

        Args:
            goal: The high-level goal to decompose.
            context: Additional context.

        Returns:
            List of sub-goal dictionaries.
        """
        prompt = f"""You are a task decomposition expert. Break down the following goal into 3-7 high-level sub-goals.

Goal: {goal}

{f'Context: {context}' if context else ''}

Return a JSON array of objects with:
- name: Short name for the sub-goal
- description: Detailed description
- priority: low/medium/high/critical
- dependencies: Array of sub-goal names this depends on (empty if none)

Example:
[
  {{"name": "Research", "description": "Gather information", "priority": "high", "dependencies": []}},
  {{"name": "Analysis", "description": "Analyze data", "priority": "high", "dependencies": ["Research"]}}
]

Return ONLY the JSON array:"""

        try:
            import json
            response = await self.ai.generate(prompt, response_format="json")
            sub_goals = json.loads(response)
            if isinstance(sub_goals, list):
                return sub_goals
        except Exception as e:
            logger.error(f"Failed to decompose goal: {e}")

        # Fallback: single sub-goal
        return [{"name": "Execute", "description": goal, "priority": "high", "dependencies": []}]


class Planner:
    """
    Creates detailed execution plans.

    Converts sub-goals into executable step DAGs.
    """

    def __init__(self, ai_client: Optional[BaseAIClient] = None):
        """Initialize the planner."""
        self.ai = ai_client or get_ai_manager()

    async def create_plan(
        self,
        goal: str,
        sub_goals: Optional[List[Dict[str, Any]]] = None,
    ) -> Plan:
        """
        Create an execution plan for a goal.

        Args:
            goal: The goal to plan for.
            sub_goals: Optional pre-decomposed sub-goals.

        Returns:
            A Plan with steps.
        """
        plan = Plan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
        )

        if sub_goals:
            # Convert sub-goals to steps
            name_to_id = {}
            for i, sg in enumerate(sub_goals):
                step_id = f"step_{i+1}"
                name_to_id[sg["name"]] = step_id

                # Resolve dependency names to IDs
                dep_ids = [
                    name_to_id[dep]
                    for dep in sg.get("dependencies", [])
                    if dep in name_to_id
                ]

                step = PlanStep(
                    step_id=step_id,
                    name=sg["name"],
                    description=sg.get("description", sg["name"]),
                    dependencies=dep_ids,
                    priority=StepPriority(sg.get("priority", "medium")),
                    executor_type=sg.get("executor_type"),
                )
                plan.add_step(step)
        else:
            # Generate steps with AI
            await self._generate_steps(plan, goal)

        logger.info(f"Created plan with {len(plan.steps)} steps for: {goal[:50]}...")
        return plan

    async def _generate_steps(self, plan: Plan, goal: str):
        """Generate steps using AI."""
        prompt = f"""Create a detailed step-by-step plan to achieve this goal:

Goal: {goal}

Return a JSON array of steps with:
- name: Short step name
- description: What this step does
- dependencies: Array of step names this depends on
- executor_type: Type of agent/tool to use (optional)

Example:
[
  {{"name": "Gather Data", "description": "Collect information from sources", "dependencies": [], "executor_type": "researcher"}},
  {{"name": "Process Data", "description": "Clean and organize data", "dependencies": ["Gather Data"], "executor_type": "processor"}}
]

Return ONLY the JSON array:"""

        try:
            import json
            response = await self.ai.generate(prompt, response_format="json")
            steps_data = json.loads(response)

            name_to_id = {}
            for i, sd in enumerate(steps_data):
                step_id = f"step_{i+1}"
                name_to_id[sd["name"]] = step_id

            for i, sd in enumerate(steps_data):
                step_id = f"step_{i+1}"
                dep_ids = [
                    name_to_id[dep]
                    for dep in sd.get("dependencies", [])
                    if dep in name_to_id
                ]

                step = PlanStep(
                    step_id=step_id,
                    name=sd["name"],
                    description=sd.get("description", ""),
                    dependencies=dep_ids,
                    executor_type=sd.get("executor_type"),
                )
                plan.add_step(step)

        except Exception as e:
            logger.error(f"Failed to generate steps: {e}")
            # Add a single fallback step
            plan.add_step(PlanStep(
                step_id="step_1",
                name="Execute Goal",
                description=goal,
            ))


class Executor:
    """
    Executes individual plan steps.

    Supports registering specialized executors for different step types.
    """

    def __init__(self):
        """Initialize the executor."""
        self._executors: Dict[str, ExecutorCallback] = {}
        self._default_executor: Optional[ExecutorCallback] = None

    def register(self, executor_type: str, callback: ExecutorCallback):
        """Register an executor for a step type."""
        self._executors[executor_type] = callback

    def set_default_executor(self, callback: ExecutorCallback):
        """Set the default executor for unregistered types."""
        self._default_executor = callback

    async def execute(
        self,
        step: PlanStep,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a plan step.

        Args:
            step: The step to execute.
            context: Execution context (outputs from dependencies).

        Returns:
            Step outputs.
        """
        context = context or {}
        step.status = StepStatus.IN_PROGRESS
        step.started_at = datetime.now()

        # Emit event
        event_stream = get_event_stream()
        event_stream.emit(
            EventType.AGENT_START,
            f"executor:{step.executor_type or 'default'}",
            {"step_id": step.step_id, "name": step.name},
        )

        try:
            # Find appropriate executor
            executor = None
            if step.executor_type and step.executor_type in self._executors:
                executor = self._executors[step.executor_type]
            elif self._default_executor:
                executor = self._default_executor

            if executor:
                outputs = await executor(step, context)
            else:
                # No executor registered - mark as completed
                logger.warning(f"No executor for step {step.step_id}, marking as completed")
                outputs = {"status": "no_executor"}

            step.outputs = outputs
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()

            event_stream.emit(
                EventType.AGENT_END,
                f"executor:{step.executor_type or 'default'}",
                {"step_id": step.step_id, "success": True},
            )

            return outputs

        except Exception as e:
            step.error = str(e)
            step.retry_count += 1

            if step.retry_count < step.max_retries:
                step.status = StepStatus.PENDING
                logger.warning(f"Step {step.step_id} failed, will retry: {e}")
            else:
                step.status = StepStatus.FAILED
                logger.error(f"Step {step.step_id} failed permanently: {e}")

            event_stream.emit(
                EventType.SYSTEM_ERROR,
                f"executor:{step.executor_type or 'default'}",
                {"step_id": step.step_id, "error": str(e)},
            )

            return {}


class HierarchicalPlanner:
    """
    Coordinates Manager, Planner, and Executor for complex tasks.

    Provides a high-level interface for hierarchical planning and execution.
    """

    def __init__(
        self,
        ai_client: Optional[BaseAIClient] = None,
        parallel_execution: bool = True,
        max_parallel: int = 3,
    ):
        """
        Initialize the hierarchical planner.

        Args:
            ai_client: AI client for planning.
            parallel_execution: Execute independent steps in parallel.
            max_parallel: Maximum parallel executions.
        """
        self.manager = Manager(ai_client)
        self.planner = Planner(ai_client)
        self.executor = Executor()
        self.parallel_execution = parallel_execution
        self.max_parallel = max_parallel
        self._current_plan: Optional[Plan] = None

    def register_executor(self, executor_type: str, callback: ExecutorCallback):
        """Register a step executor."""
        self.executor.register(executor_type, callback)

    def set_default_executor(self, callback: ExecutorCallback):
        """Set the default step executor."""
        self.executor.set_default_executor(callback)

    async def plan(
        self,
        goal: str,
        context: Optional[str] = None,
        decompose: bool = True,
    ) -> Plan:
        """
        Create a plan for a goal.

        Args:
            goal: The goal to achieve.
            context: Additional context.
            decompose: Whether to decompose into sub-goals first.

        Returns:
            The created Plan.
        """
        sub_goals = None
        if decompose:
            sub_goals = await self.manager.decompose_goal(goal, context)

        plan = await self.planner.create_plan(goal, sub_goals)
        self._current_plan = plan

        logger.info(f"Created plan {plan.plan_id} with {len(plan.steps)} steps")
        return plan

    async def execute_plan(
        self,
        plan: Optional[Plan] = None,
    ) -> Plan:
        """
        Execute a plan.

        Args:
            plan: Plan to execute (uses current if not provided).

        Returns:
            The executed Plan with results.
        """
        plan = plan or self._current_plan
        if not plan:
            raise ValueError("No plan to execute")

        plan.started_at = datetime.now()
        plan.status = "in_progress"

        # Build outputs context from completed steps
        outputs_context: Dict[str, Any] = {}

        while not plan.is_complete() and not plan.has_failed():
            ready_steps = plan.get_ready_steps()

            if not ready_steps:
                # No steps ready but plan not complete - check for failures
                if any(s.status == StepStatus.FAILED for s in plan.steps):
                    break
                # Circular dependency or other issue
                logger.error("No steps ready but plan not complete")
                break

            # Execute steps
            if self.parallel_execution and len(ready_steps) > 1:
                # Execute in parallel
                tasks = []
                for step in ready_steps[:self.max_parallel]:
                    step_context = self._build_step_context(step, plan, outputs_context)
                    tasks.append(self.executor.execute(step, step_context))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for step, result in zip(ready_steps[:self.max_parallel], results):
                    if isinstance(result, dict):
                        outputs_context[step.step_id] = result
            else:
                # Execute sequentially
                for step in ready_steps:
                    step_context = self._build_step_context(step, plan, outputs_context)
                    result = await self.executor.execute(step, step_context)
                    outputs_context[step.step_id] = result

        plan.completed_at = datetime.now()
        plan.status = "completed" if plan.is_complete() else "failed"

        logger.info(f"Plan {plan.plan_id} {plan.status} - progress: {plan.get_progress():.0%}")
        return plan

    def _build_step_context(
        self,
        step: PlanStep,
        plan: Plan,
        outputs_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build context for a step from its dependencies."""
        context = {"plan_goal": plan.goal}

        for dep_id in step.dependencies:
            if dep_id in outputs_context:
                dep_step = plan.get_step(dep_id)
                if dep_step:
                    context[dep_step.name] = outputs_context[dep_id]

        context.update(step.inputs)
        return context

    async def plan_and_execute(
        self,
        goal: str,
        context: Optional[str] = None,
    ) -> Plan:
        """
        Create and execute a plan in one call.

        Args:
            goal: The goal to achieve.
            context: Additional context.

        Returns:
            The executed Plan.
        """
        plan = await self.plan(goal, context)
        return await self.execute_plan(plan)

    def get_current_plan(self) -> Optional[Plan]:
        """Get the current plan."""
        return self._current_plan


# Global hierarchical planner
_hierarchical_planner: Optional[HierarchicalPlanner] = None


def get_hierarchical_planner(
    ai_client: Optional[BaseAIClient] = None,
) -> HierarchicalPlanner:
    """Get or create the global hierarchical planner."""
    global _hierarchical_planner
    if _hierarchical_planner is None:
        _hierarchical_planner = HierarchicalPlanner(ai_client)
    return _hierarchical_planner


def reset_hierarchical_planner():
    """Reset the global hierarchical planner."""
    global _hierarchical_planner
    _hierarchical_planner = None
