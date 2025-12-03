"""Visual Workflow Definition for agent logic.

This module provides a DSL and runtime engine for defining agent workflows
as directed acyclic graphs (DAGs) that can be visualized and debugged.

Inspired by langgenius/dify workflow system.
"""

import asyncio
import json
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import yaml

from src.core.security.safe_eval import (
    SafeConditionEvaluator,
    SafeExpressionEvaluator,
    SafeEvalError,
)

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Types of workflow nodes."""

    START = "start"
    END = "end"
    LLM = "llm"
    TOOL = "tool"
    CODE = "code"
    IF_ELSE = "if_else"
    SWITCH = "switch"
    LOOP = "loop"
    PARALLEL = "parallel"
    MERGE = "merge"
    VARIABLE = "variable"
    HTTP = "http"
    TEMPLATE = "template"


class EdgeType(str, Enum):
    """Types of edges between nodes."""

    DEFAULT = "default"
    TRUE = "true"
    FALSE = "false"
    CASE = "case"
    ERROR = "error"
    TIMEOUT = "timeout"


class WorkflowStatus(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class NodeStatus(str, Enum):
    """Status of node execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeConfig:
    """Configuration for a workflow node."""

    node_id: str
    node_type: NodeType
    name: str = ""
    description: str = ""

    # Type-specific configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Position for visualization
    position: Tuple[float, float] = (0, 0)

    # Timeouts and retries
    timeout_seconds: float = 60.0
    max_retries: int = 0
    retry_delay_seconds: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name or self.node_id,
            "description": self.description,
            "config": self.config,
            "position": list(self.position),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeConfig":
        """Deserialize from dictionary."""
        return cls(
            node_id=data["node_id"],
            node_type=NodeType(data["node_type"]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=data.get("config", {}),
            position=tuple(data.get("position", [0, 0])),
            timeout_seconds=data.get("timeout_seconds", 60.0),
            max_retries=data.get("max_retries", 0),
        )


@dataclass
class Edge:
    """Connection between two nodes."""

    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.DEFAULT
    condition: Optional[str] = None
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "condition": self.condition,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        """Deserialize from dictionary."""
        return cls(
            edge_id=data.get("edge_id", str(uuid.uuid4())[:8]),
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=EdgeType(data.get("edge_type", "default")),
            condition=data.get("condition"),
            label=data.get("label", ""),
        )


@dataclass
class NodeResult:
    """Result of executing a node."""

    node_id: str
    status: NodeStatus
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retries: int = 0

    @property
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
        }


@dataclass
class WorkflowResult:
    """Result of executing a workflow."""

    workflow_id: str
    status: WorkflowStatus
    output: Any = None
    error: Optional[str] = None
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_ms(self) -> float:
        """Get total duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "node_results": {k: v.to_dict() for k, v in self.node_results.items()},
            "duration_ms": self.duration_ms,
        }


class WorkflowDefinition:
    """Definition of a workflow graph."""

    def __init__(
        self,
        workflow_id: Optional[str] = None,
        name: str = "",
        description: str = "",
    ):
        """Initialize workflow definition."""
        self.workflow_id = workflow_id or str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.nodes: Dict[str, NodeConfig] = {}
        self.edges: Dict[str, Edge] = {}
        self.variables: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_node(self, config: NodeConfig) -> "WorkflowDefinition":
        """Add a node to the workflow."""
        self.nodes[config.node_id] = config
        self.updated_at = datetime.utcnow()
        return self

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType = EdgeType.DEFAULT,
        condition: Optional[str] = None,
    ) -> "WorkflowDefinition":
        """Add an edge between nodes."""
        edge_id = f"{source_id}->{target_id}"
        self.edges[edge_id] = Edge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            condition=condition,
        )
        self.updated_at = datetime.utcnow()
        return self

    def get_start_node(self) -> Optional[NodeConfig]:
        """Get the start node."""
        for node in self.nodes.values():
            if node.node_type == NodeType.START:
                return node
        return None

    def get_end_nodes(self) -> List[NodeConfig]:
        """Get all end nodes."""
        return [n for n in self.nodes.values() if n.node_type == NodeType.END]

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Get all outgoing edges from a node."""
        return [e for e in self.edges.values() if e.source_id == node_id]

    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """Get all incoming edges to a node."""
        return [e for e in self.edges.values() if e.target_id == node_id]

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the workflow definition."""
        errors = []

        start_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.START]
        if len(start_nodes) == 0:
            errors.append("Workflow must have a start node")
        elif len(start_nodes) > 1:
            errors.append("Workflow can only have one start node")

        end_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.END]
        if len(end_nodes) == 0:
            errors.append("Workflow must have at least one end node")

        for edge in self.edges.values():
            if edge.source_id not in self.nodes:
                errors.append(f"Edge references non-existent source node: {edge.source_id}")
            if edge.target_id not in self.nodes:
                errors.append(f"Edge references non-existent target node: {edge.target_id}")

        if self._has_cycle():
            errors.append("Workflow contains a cycle")

        return len(errors) == 0, errors

    def _has_cycle(self) -> bool:
        """Check if the graph has a cycle using DFS."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for edge in self.get_outgoing_edges(node_id):
                if edge.target_id not in visited:
                    if dfs(edge.target_id):
                        return True
                elif edge.target_id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowDefinition":
        """Deserialize from dictionary."""
        workflow = cls(
            workflow_id=data.get("workflow_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
        )

        for node_data in data.get("nodes", []):
            workflow.add_node(NodeConfig.from_dict(node_data))

        for edge_data in data.get("edges", []):
            edge = Edge.from_dict(edge_data)
            workflow.edges[edge.edge_id] = edge

        workflow.variables = data.get("variables", {})

        return workflow

    def to_yaml(self) -> str:
        """Export to YAML format."""
        return yaml.dump(self.to_dict(), default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "WorkflowDefinition":
        """Import from YAML format."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    def to_json(self) -> str:
        """Export to JSON format."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowDefinition":
        """Import from JSON format."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class NodeExecutor(ABC):
    """Abstract base class for node executors."""

    @abstractmethod
    async def execute(
        self,
        node: NodeConfig,
        context: Dict[str, Any],
    ) -> Any:
        """Execute a node and return the result."""
        pass


class StartNodeExecutor(NodeExecutor):
    """Executor for start nodes."""

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Pass through input."""
        return context.get("input")


class EndNodeExecutor(NodeExecutor):
    """Executor for end nodes."""

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Return final output."""
        output_key = node.config.get("output_key", "output")
        return context.get(output_key, context.get("last_output"))


class LLMNodeExecutor(NodeExecutor):
    """Executor for LLM nodes."""

    def __init__(self, llm_func: Optional[Callable] = None):
        """Initialize with LLM function."""
        self.llm_func = llm_func

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Execute LLM call."""
        prompt = node.config.get("prompt", "")
        system = node.config.get("system", "")

        prompt = self._render_template(prompt, context)
        system = self._render_template(system, context)

        if self.llm_func:
            if asyncio.iscoroutinefunction(self.llm_func):
                return await self.llm_func(prompt, system=system)
            return self.llm_func(prompt, system=system)

        return f"[LLM Response to: {prompt[:50]}...]"

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables."""
        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template


class ToolNodeExecutor(NodeExecutor):
    """Executor for tool nodes."""

    def __init__(self, tools: Optional[Dict[str, Callable]] = None):
        """Initialize with tools."""
        self.tools = tools or {}

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Execute tool."""
        tool_name = node.config.get("tool", "")
        tool_args = node.config.get("args", {})

        for key, value in tool_args.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                var_name = value[2:-2].strip()
                tool_args[key] = context.get(var_name, value)

        if tool_name in self.tools:
            tool = self.tools[tool_name]
            if asyncio.iscoroutinefunction(tool):
                return await tool(**tool_args)
            return tool(**tool_args)

        return f"[Tool {tool_name} not found]"


class CodeNodeExecutor(NodeExecutor):
    """Executor for code nodes.

    Note: For security reasons, arbitrary code execution is not supported.
    Only safe expression evaluation is allowed. Use expressions that set
    'result' variable, e.g., "result = x + y * 2".
    """

    def __init__(self):
        """Initialize with safe expression evaluator."""
        self._evaluator = SafeExpressionEvaluator()

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Execute safe expression (not arbitrary code)."""
        code = node.config.get("code", "")
        language = node.config.get("language", "python")

        if language != "python":
            return f"[Unsupported language: {language}]"

        # For security, we only support simple assignment expressions
        # Format: "result = <expression>"
        code = code.strip()
        if code.startswith("result"):
            # Extract expression after "result ="
            if "=" in code:
                _, expression = code.split("=", 1)
                expression = expression.strip()
            else:
                raise RuntimeError(
                    "Code must be in format 'result = <expression>'. "
                    "Arbitrary code execution is not supported for security reasons."
                )
        else:
            # Treat entire code as expression
            expression = code

        try:
            return self._evaluator.evaluate(expression, context)
        except SafeEvalError as e:
            raise RuntimeError(f"Expression evaluation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Code execution failed: {e}")


class IfElseNodeExecutor(NodeExecutor):
    """Executor for if/else nodes using safe condition evaluation."""

    def __init__(self):
        """Initialize with safe condition evaluator."""
        self._evaluator = SafeConditionEvaluator()

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Evaluate condition safely."""
        condition = node.config.get("condition", "")

        try:
            result = self._evaluator.evaluate(condition, context)
            return {"branch": "true" if result else "false", "value": result}
        except SafeEvalError as e:
            logger.warning(f"Condition evaluation failed: {e}")
            return {"branch": "false", "error": str(e)}
        except Exception as e:
            logger.warning(f"Unexpected error in condition: {e}")
            return {"branch": "false", "error": str(e)}


class VariableNodeExecutor(NodeExecutor):
    """Executor for variable nodes."""

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Set or get variables."""
        operation = node.config.get("operation", "set")
        var_name = node.config.get("name", "")
        var_value = node.config.get("value")

        if operation == "set":
            if isinstance(var_value, str) and var_value.startswith("{{"):
                var_name_ref = var_value[2:-2].strip()
                return context.get(var_name_ref)
            return var_value
        else:
            return context.get(var_name)


class TemplateNodeExecutor(NodeExecutor):
    """Executor for template nodes."""

    async def execute(self, node: NodeConfig, context: Dict[str, Any]) -> Any:
        """Render template."""
        template = node.config.get("template", "")

        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))

        return template


class WorkflowEngine:
    """Engine for executing workflows."""

    def __init__(self):
        """Initialize engine."""
        self.executors: Dict[NodeType, NodeExecutor] = {
            NodeType.START: StartNodeExecutor(),
            NodeType.END: EndNodeExecutor(),
            NodeType.LLM: LLMNodeExecutor(),
            NodeType.TOOL: ToolNodeExecutor(),
            NodeType.CODE: CodeNodeExecutor(),
            NodeType.IF_ELSE: IfElseNodeExecutor(),
            NodeType.VARIABLE: VariableNodeExecutor(),
            NodeType.TEMPLATE: TemplateNodeExecutor(),
        }
        self._lock = threading.Lock()

    def register_executor(self, node_type: NodeType, executor: NodeExecutor) -> None:
        """Register a custom executor."""
        with self._lock:
            self.executors[node_type] = executor

    def register_llm(self, llm_func: Callable) -> None:
        """Register LLM function."""
        self.executors[NodeType.LLM] = LLMNodeExecutor(llm_func)

    def register_tools(self, tools: Dict[str, Callable]) -> None:
        """Register tools."""
        self.executors[NodeType.TOOL] = ToolNodeExecutor(tools)

    async def execute(
        self,
        workflow: WorkflowDefinition,
        input_data: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute a workflow."""
        valid, errors = workflow.validate()
        if not valid:
            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                status=WorkflowStatus.FAILED,
                error=f"Invalid workflow: {', '.join(errors)}",
            )

        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        exec_context = dict(context or {})
        exec_context["input"] = input_data
        exec_context.update(workflow.variables)

        try:
            start_node = workflow.get_start_node()
            if not start_node:
                raise RuntimeError("No start node found")

            output = await self._execute_node(
                workflow, start_node, exec_context, result
            )

            result.status = WorkflowStatus.COMPLETED
            result.output = output

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
            logger.exception(f"Workflow execution failed: {e}")

        result.end_time = datetime.utcnow()
        return result

    async def _execute_node(
        self,
        workflow: WorkflowDefinition,
        node: NodeConfig,
        context: Dict[str, Any],
        result: WorkflowResult,
    ) -> Any:
        """Execute a single node and continue to next nodes."""
        node_result = NodeResult(
            node_id=node.node_id,
            status=NodeStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        try:
            executor = self.executors.get(node.node_type)
            if executor is None:
                raise RuntimeError(f"No executor for node type: {node.node_type}")

            output = await asyncio.wait_for(
                executor.execute(node, context),
                timeout=node.timeout_seconds,
            )

            node_result.status = NodeStatus.COMPLETED
            node_result.output = output

            context["last_output"] = output
            context[node.node_id] = output

        except asyncio.TimeoutError:
            node_result.status = NodeStatus.FAILED
            node_result.error = "Timeout"
            raise

        except Exception as e:
            node_result.status = NodeStatus.FAILED
            node_result.error = str(e)
            raise

        finally:
            node_result.end_time = datetime.utcnow()
            result.node_results[node.node_id] = node_result

        if node.node_type == NodeType.END:
            return output

        next_node = self._get_next_node(workflow, node, output)
        if next_node:
            return await self._execute_node(workflow, next_node, context, result)

        return output

    def _get_next_node(
        self,
        workflow: WorkflowDefinition,
        current_node: NodeConfig,
        output: Any,
    ) -> Optional[NodeConfig]:
        """Determine the next node to execute."""
        edges = workflow.get_outgoing_edges(current_node.node_id)

        if not edges:
            return None

        if current_node.node_type == NodeType.IF_ELSE:
            branch = output.get("branch", "false") if isinstance(output, dict) else "false"
            for edge in edges:
                if edge.edge_type.value == branch:
                    return workflow.nodes.get(edge.target_id)

        for edge in edges:
            if edge.edge_type == EdgeType.DEFAULT:
                return workflow.nodes.get(edge.target_id)

        return workflow.nodes.get(edges[0].target_id) if edges else None


class WorkflowBuilder:
    """Builder for creating workflows fluently."""

    def __init__(self, name: str = "", description: str = ""):
        """Initialize builder."""
        self.workflow = WorkflowDefinition(name=name, description=description)
        self._last_node_id: Optional[str] = None

    def start(self, node_id: str = "start") -> "WorkflowBuilder":
        """Add start node."""
        self.workflow.add_node(NodeConfig(
            node_id=node_id,
            node_type=NodeType.START,
            name="Start",
        ))
        self._last_node_id = node_id
        return self

    def end(self, node_id: str = "end", output_key: str = "output") -> "WorkflowBuilder":
        """Add end node."""
        self.workflow.add_node(NodeConfig(
            node_id=node_id,
            node_type=NodeType.END,
            name="End",
            config={"output_key": output_key},
        ))
        if self._last_node_id:
            self.workflow.add_edge(self._last_node_id, node_id)
        self._last_node_id = node_id
        return self

    def llm(
        self,
        node_id: str,
        prompt: str,
        system: str = "",
        name: str = "",
    ) -> "WorkflowBuilder":
        """Add LLM node."""
        self.workflow.add_node(NodeConfig(
            node_id=node_id,
            node_type=NodeType.LLM,
            name=name or f"LLM: {node_id}",
            config={"prompt": prompt, "system": system},
        ))
        if self._last_node_id:
            self.workflow.add_edge(self._last_node_id, node_id)
        self._last_node_id = node_id
        return self

    def tool(
        self,
        node_id: str,
        tool: str,
        args: Optional[Dict[str, Any]] = None,
        name: str = "",
    ) -> "WorkflowBuilder":
        """Add tool node."""
        self.workflow.add_node(NodeConfig(
            node_id=node_id,
            node_type=NodeType.TOOL,
            name=name or f"Tool: {tool}",
            config={"tool": tool, "args": args or {}},
        ))
        if self._last_node_id:
            self.workflow.add_edge(self._last_node_id, node_id)
        self._last_node_id = node_id
        return self

    def if_else(
        self,
        node_id: str,
        condition: str,
        true_target: str,
        false_target: str,
    ) -> "WorkflowBuilder":
        """Add if/else node with branches."""
        self.workflow.add_node(NodeConfig(
            node_id=node_id,
            node_type=NodeType.IF_ELSE,
            name=f"If: {condition[:20]}",
            config={"condition": condition},
        ))
        if self._last_node_id:
            self.workflow.add_edge(self._last_node_id, node_id)
        self.workflow.add_edge(node_id, true_target, EdgeType.TRUE)
        self.workflow.add_edge(node_id, false_target, EdgeType.FALSE)
        self._last_node_id = None
        return self

    def variable(
        self,
        node_id: str,
        name: str,
        value: Any,
    ) -> "WorkflowBuilder":
        """Add variable node."""
        self.workflow.add_node(NodeConfig(
            node_id=node_id,
            node_type=NodeType.VARIABLE,
            name=f"Set: {name}",
            config={"operation": "set", "name": name, "value": value},
        ))
        if self._last_node_id:
            self.workflow.add_edge(self._last_node_id, node_id)
        self._last_node_id = node_id
        return self

    def template(
        self,
        node_id: str,
        template: str,
        name: str = "",
    ) -> "WorkflowBuilder":
        """Add template node."""
        self.workflow.add_node(NodeConfig(
            node_id=node_id,
            node_type=NodeType.TEMPLATE,
            name=name or "Template",
            config={"template": template},
        ))
        if self._last_node_id:
            self.workflow.add_edge(self._last_node_id, node_id)
        self._last_node_id = node_id
        return self

    def connect(self, source_id: str, target_id: str) -> "WorkflowBuilder":
        """Manually connect two nodes."""
        self.workflow.add_edge(source_id, target_id)
        return self

    def build(self) -> WorkflowDefinition:
        """Build and return the workflow."""
        return self.workflow


class WorkflowManager:
    """Manager for workflow operations."""

    def __init__(self):
        """Initialize manager."""
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.engine = WorkflowEngine()
        self._lock = threading.Lock()

    def create_workflow(
        self,
        name: str = "",
        description: str = "",
    ) -> WorkflowBuilder:
        """Create a new workflow using the builder."""
        return WorkflowBuilder(name=name, description=description)

    def add_workflow(self, workflow: WorkflowDefinition) -> None:
        """Add a workflow to the manager."""
        with self._lock:
            self.workflows[workflow.workflow_id] = workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all workflows."""
        return list(self.workflows.values())

    async def execute(
        self,
        workflow_id: str,
        input_data: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute a workflow by ID."""
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error=f"Workflow not found: {workflow_id}",
            )

        return await self.engine.execute(workflow, input_data, context)

    def remove_workflow(self, workflow_id: str) -> bool:
        """Remove a workflow."""
        with self._lock:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
                return True
            return False

    def save_workflow(self, workflow_id: str, path: Union[str, Path]) -> None:
        """Save a workflow to file."""
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        path = Path(path)
        if path.suffix == ".yaml" or path.suffix == ".yml":
            path.write_text(workflow.to_yaml())
        else:
            path.write_text(workflow.to_json())

    def load_workflow(self, path: Union[str, Path]) -> WorkflowDefinition:
        """Load a workflow from file."""
        path = Path(path)
        content = path.read_text()

        if path.suffix == ".yaml" or path.suffix == ".yml":
            workflow = WorkflowDefinition.from_yaml(content)
        else:
            workflow = WorkflowDefinition.from_json(content)

        self.add_workflow(workflow)
        return workflow

    def register_llm(self, llm_func: Callable) -> None:
        """Register LLM function."""
        self.engine.register_llm(llm_func)

    def register_tools(self, tools: Dict[str, Callable]) -> None:
        """Register tools."""
        self.engine.register_tools(tools)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about workflows."""
        return {
            "total_workflows": len(self.workflows),
            "workflows": [
                {
                    "id": w.workflow_id,
                    "name": w.name,
                    "nodes": len(w.nodes),
                    "edges": len(w.edges),
                }
                for w in self.workflows.values()
            ],
        }


_workflow_manager: Optional[WorkflowManager] = None
_workflow_lock = threading.Lock()


def get_workflow_manager() -> WorkflowManager:
    """Get singleton workflow manager."""
    global _workflow_manager

    with _workflow_lock:
        if _workflow_manager is None:
            _workflow_manager = WorkflowManager()
        return _workflow_manager


def reset_workflow_manager() -> None:
    """Reset singleton workflow manager."""
    global _workflow_manager

    with _workflow_lock:
        _workflow_manager = None
