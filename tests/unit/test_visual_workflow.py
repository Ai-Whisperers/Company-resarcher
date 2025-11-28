"""Tests for visual workflow definition."""

import pytest
import tempfile
import json
from pathlib import Path

from src.core.visual_workflow import (
    Edge,
    EdgeType,
    EndNodeExecutor,
    IfElseNodeExecutor,
    LLMNodeExecutor,
    NodeConfig,
    NodeResult,
    NodeStatus,
    NodeType,
    StartNodeExecutor,
    TemplateNodeExecutor,
    ToolNodeExecutor,
    VariableNodeExecutor,
    WorkflowBuilder,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowManager,
    WorkflowResult,
    WorkflowStatus,
    get_workflow_manager,
    reset_workflow_manager,
)


class TestNodeConfig:
    """Tests for NodeConfig class."""

    def test_create_config(self):
        """Test creating a node config."""
        config = NodeConfig(
            node_id="node_1",
            node_type=NodeType.LLM,
            name="My Node",
            config={"prompt": "Hello"},
        )

        assert config.node_id == "node_1"
        assert config.node_type == NodeType.LLM
        assert config.config["prompt"] == "Hello"

    def test_to_dict(self):
        """Test serialization."""
        config = NodeConfig(
            node_id="n1",
            node_type=NodeType.TOOL,
            name="Tool Node",
            position=(100, 200),
        )
        data = config.to_dict()

        assert data["node_id"] == "n1"
        assert data["node_type"] == "tool"
        assert data["position"] == [100, 200]

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "node_id": "n2",
            "node_type": "code",
            "name": "Code Node",
            "config": {"code": "x = 1"},
        }
        config = NodeConfig.from_dict(data)

        assert config.node_id == "n2"
        assert config.node_type == NodeType.CODE


class TestEdge:
    """Tests for Edge class."""

    def test_create_edge(self):
        """Test creating an edge."""
        edge = Edge(
            edge_id="e1",
            source_id="n1",
            target_id="n2",
            edge_type=EdgeType.TRUE,
        )

        assert edge.source_id == "n1"
        assert edge.edge_type == EdgeType.TRUE

    def test_to_dict(self):
        """Test serialization."""
        edge = Edge(
            edge_id="e1",
            source_id="a",
            target_id="b",
            condition="x > 0",
        )
        data = edge.to_dict()

        assert data["source_id"] == "a"
        assert data["condition"] == "x > 0"


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition class."""

    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow = WorkflowDefinition(
            name="Test Workflow",
            description="A test",
        )

        assert workflow.name == "Test Workflow"
        assert workflow.workflow_id is not None

    def test_add_node(self):
        """Test adding nodes."""
        workflow = WorkflowDefinition()
        workflow.add_node(NodeConfig("n1", NodeType.START))
        workflow.add_node(NodeConfig("n2", NodeType.END))

        assert len(workflow.nodes) == 2
        assert "n1" in workflow.nodes

    def test_add_edge(self):
        """Test adding edges."""
        workflow = WorkflowDefinition()
        workflow.add_node(NodeConfig("n1", NodeType.START))
        workflow.add_node(NodeConfig("n2", NodeType.END))
        workflow.add_edge("n1", "n2")

        assert len(workflow.edges) == 1

    def test_get_start_node(self):
        """Test getting start node."""
        workflow = WorkflowDefinition()
        workflow.add_node(NodeConfig("start", NodeType.START))
        workflow.add_node(NodeConfig("end", NodeType.END))

        start = workflow.get_start_node()

        assert start is not None
        assert start.node_id == "start"

    def test_get_end_nodes(self):
        """Test getting end nodes."""
        workflow = WorkflowDefinition()
        workflow.add_node(NodeConfig("start", NodeType.START))
        workflow.add_node(NodeConfig("end1", NodeType.END))
        workflow.add_node(NodeConfig("end2", NodeType.END))

        ends = workflow.get_end_nodes()

        assert len(ends) == 2

    def test_validate_valid(self):
        """Test validating a valid workflow."""
        workflow = WorkflowDefinition()
        workflow.add_node(NodeConfig("start", NodeType.START))
        workflow.add_node(NodeConfig("end", NodeType.END))
        workflow.add_edge("start", "end")

        valid, errors = workflow.validate()

        assert valid is True
        assert len(errors) == 0

    def test_validate_no_start(self):
        """Test validation without start node."""
        workflow = WorkflowDefinition()
        workflow.add_node(NodeConfig("end", NodeType.END))

        valid, errors = workflow.validate()

        assert valid is False
        assert any("start" in e.lower() for e in errors)

    def test_validate_no_end(self):
        """Test validation without end node."""
        workflow = WorkflowDefinition()
        workflow.add_node(NodeConfig("start", NodeType.START))

        valid, errors = workflow.validate()

        assert valid is False
        assert any("end" in e.lower() for e in errors)

    def test_to_yaml(self):
        """Test YAML export."""
        workflow = WorkflowDefinition(name="YAML Test")
        workflow.add_node(NodeConfig("start", NodeType.START))
        workflow.add_node(NodeConfig("end", NodeType.END))

        yaml_str = workflow.to_yaml()

        assert "YAML Test" in yaml_str
        assert "start" in yaml_str

    def test_from_yaml(self):
        """Test YAML import."""
        workflow = WorkflowDefinition(name="Original")
        workflow.add_node(NodeConfig("start", NodeType.START))
        workflow.add_node(NodeConfig("end", NodeType.END))
        workflow.add_edge("start", "end")

        yaml_str = workflow.to_yaml()
        loaded = WorkflowDefinition.from_yaml(yaml_str)

        assert loaded.name == "Original"
        assert len(loaded.nodes) == 2

    def test_to_json(self):
        """Test JSON export."""
        workflow = WorkflowDefinition(name="JSON Test")
        workflow.add_node(NodeConfig("start", NodeType.START))

        json_str = workflow.to_json()
        data = json.loads(json_str)

        assert data["name"] == "JSON Test"

    def test_from_json(self):
        """Test JSON import."""
        workflow = WorkflowDefinition(name="Original")
        workflow.add_node(NodeConfig("start", NodeType.START))
        workflow.add_node(NodeConfig("end", NodeType.END))

        json_str = workflow.to_json()
        loaded = WorkflowDefinition.from_json(json_str)

        assert loaded.name == "Original"


class TestWorkflowBuilder:
    """Tests for WorkflowBuilder class."""

    def test_simple_workflow(self):
        """Test building a simple workflow."""
        builder = WorkflowBuilder(name="Simple")
        workflow = (
            builder
            .start()
            .llm("analyze", "Analyze: {{input}}")
            .end()
            .build()
        )

        assert len(workflow.nodes) == 3
        assert len(workflow.edges) == 2

    def test_workflow_with_tool(self):
        """Test building workflow with tool."""
        builder = WorkflowBuilder()
        workflow = (
            builder
            .start()
            .tool("search", "web_search", {"query": "{{input}}"})
            .end()
            .build()
        )

        assert "search" in workflow.nodes
        assert workflow.nodes["search"].node_type == NodeType.TOOL

    def test_workflow_with_if_else(self):
        """Test building workflow with if/else."""
        builder = WorkflowBuilder()
        workflow = (
            builder
            .start()
            .if_else("check", "score > 50", "good", "bad")
            .build()
        )

        # Add the target nodes
        workflow.add_node(NodeConfig("good", NodeType.END))
        workflow.add_node(NodeConfig("bad", NodeType.END))

        assert "check" in workflow.nodes
        edges = workflow.get_outgoing_edges("check")
        assert len(edges) == 2

    def test_workflow_with_variable(self):
        """Test building workflow with variable."""
        builder = WorkflowBuilder()
        workflow = (
            builder
            .start()
            .variable("set_name", "user_name", "Alice")
            .end()
            .build()
        )

        assert "set_name" in workflow.nodes

    def test_workflow_with_template(self):
        """Test building workflow with template."""
        builder = WorkflowBuilder()
        workflow = (
            builder
            .start()
            .template("render", "Hello {{name}}!")
            .end()
            .build()
        )

        assert "render" in workflow.nodes


class TestNodeExecutors:
    """Tests for node executors."""

    @pytest.mark.asyncio
    async def test_start_executor(self):
        """Test start node executor."""
        executor = StartNodeExecutor()
        node = NodeConfig("start", NodeType.START)
        context = {"input": "test data"}

        result = await executor.execute(node, context)

        assert result == "test data"

    @pytest.mark.asyncio
    async def test_end_executor(self):
        """Test end node executor."""
        executor = EndNodeExecutor()
        node = NodeConfig("end", NodeType.END, config={"output_key": "result"})
        context = {"result": "final output"}

        result = await executor.execute(node, context)

        assert result == "final output"

    @pytest.mark.asyncio
    async def test_llm_executor_no_func(self):
        """Test LLM executor without function."""
        executor = LLMNodeExecutor()
        node = NodeConfig("llm", NodeType.LLM, config={"prompt": "Hello world"})
        context = {}

        result = await executor.execute(node, context)

        assert "LLM Response" in result

    @pytest.mark.asyncio
    async def test_llm_executor_with_func(self):
        """Test LLM executor with function."""
        async def mock_llm(prompt, system=""):
            return f"Response to: {prompt}"

        executor = LLMNodeExecutor(mock_llm)
        node = NodeConfig("llm", NodeType.LLM, config={"prompt": "Test"})
        context = {}

        result = await executor.execute(node, context)

        assert "Response to: Test" in result

    @pytest.mark.asyncio
    async def test_tool_executor(self):
        """Test tool executor."""
        def search(query: str) -> str:
            return f"Results for: {query}"

        executor = ToolNodeExecutor({"search": search})
        node = NodeConfig("tool", NodeType.TOOL, config={
            "tool": "search",
            "args": {"query": "test"}
        })
        context = {}

        result = await executor.execute(node, context)

        assert "Results for: test" in result

    @pytest.mark.asyncio
    async def test_if_else_executor_true(self):
        """Test if/else executor with true condition."""
        executor = IfElseNodeExecutor()
        node = NodeConfig("check", NodeType.IF_ELSE, config={
            "condition": "x > 5"
        })
        context = {"x": 10}

        result = await executor.execute(node, context)

        assert result["branch"] == "true"

    @pytest.mark.asyncio
    async def test_if_else_executor_false(self):
        """Test if/else executor with false condition."""
        executor = IfElseNodeExecutor()
        node = NodeConfig("check", NodeType.IF_ELSE, config={
            "condition": "x > 5"
        })
        context = {"x": 3}

        result = await executor.execute(node, context)

        assert result["branch"] == "false"

    @pytest.mark.asyncio
    async def test_variable_executor(self):
        """Test variable executor."""
        executor = VariableNodeExecutor()
        node = NodeConfig("var", NodeType.VARIABLE, config={
            "operation": "set",
            "name": "test",
            "value": 42
        })
        context = {}

        result = await executor.execute(node, context)

        assert result == 42

    @pytest.mark.asyncio
    async def test_template_executor(self):
        """Test template executor."""
        executor = TemplateNodeExecutor()
        node = NodeConfig("tmpl", NodeType.TEMPLATE, config={
            "template": "Hello {{name}}!"
        })
        context = {"name": "World"}

        result = await executor.execute(node, context)

        assert result == "Hello World!"


class TestWorkflowEngine:
    """Tests for WorkflowEngine class."""

    def setup_method(self):
        """Create engine."""
        self.engine = WorkflowEngine()

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Test executing a simple workflow."""
        workflow = (
            WorkflowBuilder()
            .start()
            .end()
            .build()
        )

        result = await self.engine.execute(workflow, "test input")

        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_invalid_workflow(self):
        """Test executing an invalid workflow."""
        workflow = WorkflowDefinition()
        # No start node

        result = await self.engine.execute(workflow)

        assert result.status == WorkflowStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_with_llm(self):
        """Test executing workflow with LLM."""
        async def mock_llm(prompt, system=""):
            return f"Analyzed: {prompt}"

        self.engine.register_llm(mock_llm)

        workflow = (
            WorkflowBuilder()
            .start()
            .llm("analyze", "{{input}}")
            .end()
            .build()
        )

        result = await self.engine.execute(workflow, "test data")

        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_with_tools(self):
        """Test executing workflow with tools."""
        self.engine.register_tools({
            "echo": lambda text: f"Echo: {text}"
        })

        workflow = (
            WorkflowBuilder()
            .start()
            .tool("echo_node", "echo", {"text": "hello"})
            .end()
            .build()
        )

        result = await self.engine.execute(workflow)

        assert result.status == WorkflowStatus.COMPLETED


class TestWorkflowManager:
    """Tests for WorkflowManager class."""

    def setup_method(self):
        """Create manager."""
        self.manager = WorkflowManager()

    def test_create_workflow(self):
        """Test creating workflow with builder."""
        builder = self.manager.create_workflow(name="Test")

        assert isinstance(builder, WorkflowBuilder)

    def test_add_and_get_workflow(self):
        """Test adding and getting workflow."""
        workflow = WorkflowDefinition(name="Test")
        self.manager.add_workflow(workflow)

        retrieved = self.manager.get_workflow(workflow.workflow_id)

        assert retrieved is not None
        assert retrieved.name == "Test"

    def test_list_workflows(self):
        """Test listing workflows."""
        self.manager.add_workflow(WorkflowDefinition(name="W1"))
        self.manager.add_workflow(WorkflowDefinition(name="W2"))

        workflows = self.manager.list_workflows()

        assert len(workflows) == 2

    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test executing workflow by ID."""
        workflow = (
            self.manager.create_workflow()
            .start()
            .end()
            .build()
        )
        self.manager.add_workflow(workflow)

        result = await self.manager.execute(workflow.workflow_id)

        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_nonexistent(self):
        """Test executing nonexistent workflow."""
        result = await self.manager.execute("nonexistent")

        assert result.status == WorkflowStatus.FAILED

    def test_remove_workflow(self):
        """Test removing workflow."""
        workflow = WorkflowDefinition()
        self.manager.add_workflow(workflow)

        success = self.manager.remove_workflow(workflow.workflow_id)

        assert success is True
        assert self.manager.get_workflow(workflow.workflow_id) is None

    def test_save_and_load_json(self):
        """Test saving and loading JSON."""
        workflow = (
            self.manager.create_workflow(name="Save Test")
            .start()
            .end()
            .build()
        )
        self.manager.add_workflow(workflow)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            self.manager.save_workflow(workflow.workflow_id, path)
            loaded = self.manager.load_workflow(path)

            assert loaded.name == "Save Test"
        finally:
            path.unlink(missing_ok=True)

    def test_save_and_load_yaml(self):
        """Test saving and loading YAML."""
        workflow = (
            self.manager.create_workflow(name="YAML Test")
            .start()
            .end()
            .build()
        )
        self.manager.add_workflow(workflow)

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            self.manager.save_workflow(workflow.workflow_id, path)
            loaded = self.manager.load_workflow(path)

            assert loaded.name == "YAML Test"
        finally:
            path.unlink(missing_ok=True)

    def test_get_statistics(self):
        """Test getting statistics."""
        workflow = (
            self.manager.create_workflow(name="Stats Test")
            .start()
            .llm("llm", "test")
            .end()
            .build()
        )
        self.manager.add_workflow(workflow)

        stats = self.manager.get_statistics()

        assert stats["total_workflows"] == 1
        assert len(stats["workflows"]) == 1


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_workflow_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_workflow_manager()

    def test_get_workflow_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_workflow_manager()
        m2 = get_workflow_manager()
        assert m1 is m2

    def test_reset_workflow_manager(self):
        """Test resetting singleton."""
        m1 = get_workflow_manager()
        reset_workflow_manager()
        m2 = get_workflow_manager()
        assert m1 is not m2


class TestEnums:
    """Tests for enums."""

    def test_node_types(self):
        """Test all node types."""
        types = [
            NodeType.START,
            NodeType.END,
            NodeType.LLM,
            NodeType.TOOL,
            NodeType.CODE,
            NodeType.IF_ELSE,
            NodeType.SWITCH,
            NodeType.LOOP,
            NodeType.PARALLEL,
            NodeType.MERGE,
            NodeType.VARIABLE,
            NodeType.HTTP,
            NodeType.TEMPLATE,
        ]
        assert len(types) == len(NodeType)

    def test_edge_types(self):
        """Test all edge types."""
        types = [
            EdgeType.DEFAULT,
            EdgeType.TRUE,
            EdgeType.FALSE,
            EdgeType.CASE,
            EdgeType.ERROR,
            EdgeType.TIMEOUT,
        ]
        assert len(types) == len(EdgeType)

    def test_workflow_status(self):
        """Test workflow status values."""
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
