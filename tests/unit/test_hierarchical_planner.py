"""Tests for the hierarchical planning system."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.core.hierarchical_planner import (
    Executor,
    HierarchicalPlanner,
    Manager,
    Plan,
    Planner,
    PlanStep,
    StepPriority,
    StepStatus,
    get_hierarchical_planner,
    reset_hierarchical_planner,
)


class TestPlanStep:
    """Tests for PlanStep class."""

    def test_create_step(self):
        """Test creating a plan step."""
        step = PlanStep(
            step_id="step_1",
            name="Research",
            description="Research the topic",
        )
        assert step.step_id == "step_1"
        assert step.status == StepStatus.PENDING
        assert step.priority == StepPriority.MEDIUM

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = PlanStep(
            step_id="step_2",
            name="Analyze",
            description="Analyze data",
            dependencies=["step_1"],
        )
        assert "step_1" in step.dependencies

    def test_to_dict(self):
        """Test serialization."""
        step = PlanStep(
            step_id="step_1",
            name="Test",
            description="Test step",
            status=StepStatus.COMPLETED,
            outputs={"result": "success"},
        )
        data = step.to_dict()
        assert data["step_id"] == "step_1"
        assert data["status"] == "completed"
        assert data["outputs"]["result"] == "success"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "step_id": "step_1",
            "name": "Loaded",
            "description": "Loaded step",
            "status": "in_progress",
            "priority": "high",
        }
        step = PlanStep.from_dict(data)
        assert step.status == StepStatus.IN_PROGRESS
        assert step.priority == StepPriority.HIGH


class TestPlan:
    """Tests for Plan class."""

    def test_create_plan(self):
        """Test creating a plan."""
        plan = Plan(plan_id="plan_1", goal="Research a company")
        assert plan.plan_id == "plan_1"
        assert len(plan.steps) == 0
        assert plan.status == "created"

    def test_add_steps(self):
        """Test adding steps."""
        plan = Plan(plan_id="plan_1", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="First"))
        plan.add_step(PlanStep(step_id="s2", name="Step 2", description="Second"))
        assert len(plan.steps) == 2

    def test_get_step(self):
        """Test getting a step by ID."""
        plan = Plan(plan_id="plan_1", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="First"))

        step = plan.get_step("s1")
        assert step is not None
        assert step.name == "Step 1"

        assert plan.get_step("nonexistent") is None

    def test_get_ready_steps(self):
        """Test getting ready steps."""
        plan = Plan(plan_id="plan_1", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="No deps"))
        plan.add_step(PlanStep(
            step_id="s2",
            name="Step 2",
            description="Depends on s1",
            dependencies=["s1"],
        ))

        # Initially only s1 is ready
        ready = plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == "s1"

        # Mark s1 as completed
        plan.steps[0].status = StepStatus.COMPLETED

        # Now s2 should be ready
        ready = plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == "s2"

    def test_is_complete(self):
        """Test completion check."""
        plan = Plan(plan_id="plan_1", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="First"))

        assert plan.is_complete() is False

        plan.steps[0].status = StepStatus.COMPLETED
        assert plan.is_complete() is True

    def test_has_failed(self):
        """Test failure check."""
        plan = Plan(plan_id="plan_1", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="First"))

        assert plan.has_failed() is False

        plan.steps[0].status = StepStatus.FAILED
        assert plan.has_failed() is True

    def test_get_progress(self):
        """Test progress calculation."""
        plan = Plan(plan_id="plan_1", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="First"))
        plan.add_step(PlanStep(step_id="s2", name="Step 2", description="Second"))

        assert plan.get_progress() == 0.0

        plan.steps[0].status = StepStatus.COMPLETED
        assert plan.get_progress() == 0.5

        plan.steps[1].status = StepStatus.COMPLETED
        assert plan.get_progress() == 1.0

    def test_to_dict(self):
        """Test serialization."""
        plan = Plan(plan_id="plan_1", goal="Test goal")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="First"))

        data = plan.to_dict()
        assert data["plan_id"] == "plan_1"
        assert data["goal"] == "Test goal"
        assert len(data["steps"]) == 1
        assert "progress" in data


class TestManager:
    """Tests for Manager class."""

    @pytest.mark.asyncio
    async def test_decompose_goal(self):
        """Test goal decomposition."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='''[
            {"name": "Research", "description": "Gather info", "priority": "high", "dependencies": []},
            {"name": "Analyze", "description": "Analyze data", "priority": "medium", "dependencies": ["Research"]}
        ]''')

        manager = Manager(ai_client=mock_ai)
        sub_goals = await manager.decompose_goal("Research Apple Inc")

        assert len(sub_goals) == 2
        assert sub_goals[0]["name"] == "Research"
        assert sub_goals[1]["dependencies"] == ["Research"]

    @pytest.mark.asyncio
    async def test_decompose_goal_failure_fallback(self):
        """Test fallback on decomposition failure."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(side_effect=Exception("API error"))

        manager = Manager(ai_client=mock_ai)
        sub_goals = await manager.decompose_goal("Test goal")

        assert len(sub_goals) == 1
        assert sub_goals[0]["name"] == "Execute"


class TestPlanner:
    """Tests for Planner class."""

    @pytest.mark.asyncio
    async def test_create_plan_from_subgoals(self):
        """Test creating plan from sub-goals."""
        planner = Planner()

        sub_goals = [
            {"name": "Step A", "description": "First step", "priority": "high", "dependencies": []},
            {"name": "Step B", "description": "Second step", "priority": "medium", "dependencies": ["Step A"]},
        ]

        plan = await planner.create_plan("Test goal", sub_goals)

        assert len(plan.steps) == 2
        assert plan.steps[1].dependencies == ["step_1"]

    @pytest.mark.asyncio
    async def test_create_plan_with_ai(self):
        """Test creating plan using AI."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='''[
            {"name": "Research", "description": "Research phase", "dependencies": []},
            {"name": "Write", "description": "Write report", "dependencies": ["Research"]}
        ]''')

        planner = Planner(ai_client=mock_ai)
        plan = await planner.create_plan("Create a report")

        assert len(plan.steps) == 2


class TestExecutor:
    """Tests for Executor class."""

    @pytest.mark.asyncio
    async def test_execute_with_callback(self):
        """Test executing a step with callback."""
        executor = Executor()

        async def research_executor(step, context):
            return {"findings": "Important data"}

        executor.register("researcher", research_executor)

        step = PlanStep(
            step_id="s1",
            name="Research",
            description="Research topic",
            executor_type="researcher",
        )

        result = await executor.execute(step, {})

        assert step.status == StepStatus.COMPLETED
        assert result["findings"] == "Important data"

    @pytest.mark.asyncio
    async def test_execute_with_default(self):
        """Test executing with default executor."""
        executor = Executor()

        async def default_exec(step, context):
            return {"default": True}

        executor.set_default_executor(default_exec)

        step = PlanStep(
            step_id="s1",
            name="Generic",
            description="Generic step",
        )

        result = await executor.execute(step, {})
        assert result["default"] is True

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """Test execution failure handling."""
        executor = Executor()

        async def failing_executor(step, context):
            raise Exception("Execution failed")

        executor.register("failing", failing_executor)

        step = PlanStep(
            step_id="s1",
            name="Failing",
            description="Will fail",
            executor_type="failing",
            max_retries=1,
        )

        await executor.execute(step, {})

        assert step.status == StepStatus.FAILED
        assert step.error is not None


class TestHierarchicalPlanner:
    """Tests for HierarchicalPlanner class."""

    def setup_method(self):
        """Reset before each test."""
        reset_hierarchical_planner()

    @pytest.mark.asyncio
    async def test_plan_creation(self):
        """Test creating a plan."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='''[
            {"name": "Research", "description": "Research phase", "priority": "high", "dependencies": []}
        ]''')

        planner = HierarchicalPlanner(ai_client=mock_ai)
        plan = await planner.plan("Test goal")

        assert plan is not None
        assert len(plan.steps) >= 1

    @pytest.mark.asyncio
    async def test_execute_plan(self):
        """Test executing a plan."""
        planner = HierarchicalPlanner()

        # Create a simple plan manually
        plan = Plan(plan_id="test", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="First"))
        plan.add_step(PlanStep(
            step_id="s2",
            name="Step 2",
            description="Second",
            dependencies=["s1"],
        ))

        async def dummy_executor(step, context):
            return {"completed": step.name}

        planner.set_default_executor(dummy_executor)

        result = await planner.execute_plan(plan)

        assert result.is_complete()
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel step execution."""
        planner = HierarchicalPlanner(parallel_execution=True, max_parallel=2)

        # Create plan with independent steps
        plan = Plan(plan_id="test", goal="Test")
        plan.add_step(PlanStep(step_id="s1", name="Step 1", description="Independent"))
        plan.add_step(PlanStep(step_id="s2", name="Step 2", description="Independent"))
        plan.add_step(PlanStep(
            step_id="s3",
            name="Step 3",
            description="Depends on both",
            dependencies=["s1", "s2"],
        ))

        execution_order = []

        async def tracking_executor(step, context):
            execution_order.append(step.step_id)
            return {}

        planner.set_default_executor(tracking_executor)

        await planner.execute_plan(plan)

        # s1 and s2 should execute before s3
        assert execution_order.index("s3") > execution_order.index("s1")
        assert execution_order.index("s3") > execution_order.index("s2")

    @pytest.mark.asyncio
    async def test_plan_and_execute(self):
        """Test combined plan and execute."""
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(return_value='''[
            {"name": "Only Step", "description": "Single step", "priority": "high", "dependencies": []}
        ]''')

        planner = HierarchicalPlanner(ai_client=mock_ai)

        async def simple_executor(step, context):
            return {"done": True}

        planner.set_default_executor(simple_executor)

        result = await planner.plan_and_execute("Simple goal")

        assert result.is_complete()


class TestGlobalPlanner:
    """Tests for global planner functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_hierarchical_planner()

    def test_get_hierarchical_planner_singleton(self):
        """Test singleton behavior."""
        p1 = get_hierarchical_planner()
        p2 = get_hierarchical_planner()
        assert p1 is p2

    def test_reset_hierarchical_planner(self):
        """Test resetting the singleton."""
        p1 = get_hierarchical_planner()
        reset_hierarchical_planner()
        p2 = get_hierarchical_planner()
        assert p1 is not p2
