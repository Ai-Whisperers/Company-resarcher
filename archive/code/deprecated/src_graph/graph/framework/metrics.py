from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""

    node_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    duration_ms: float = 0.0

    def complete(self, success: bool, error: Optional[str] = None) -> None:
        """Complete the node execution metrics."""
        self.end_time = datetime.now()
        self.success = success
        self.error = error
        if self.start_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


@dataclass
class ExecutionMetrics:
    """Metrics for the entire graph execution."""

    workflow_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    node_metrics: Dict[str, List[NodeMetrics]] = field(default_factory=dict)
    total_retries: int = 0
    total_cost: float = 0.0

    def record_node_start(self, node_name: str) -> None:
        """Record the start of a node execution."""
        if node_name not in self.node_metrics:
            self.node_metrics[node_name] = []
        self.node_metrics[node_name].append(
            NodeMetrics(node_name=node_name, start_time=datetime.now())
        )

    def record_node_end(
        self, node_name: str, success: bool, error: Optional[str] = None
    ) -> None:
        """Record the end of a node execution."""
        if node_name in self.node_metrics and self.node_metrics[node_name]:
            # Get the last metric for this node (the active one)
            metric = self.node_metrics[node_name][-1]
            metric.complete(success, error)

    def complete(self) -> None:
        """Complete the workflow execution metrics."""
        self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (
                (self.end_time - self.start_time).total_seconds() * 1000
                if self.end_time
                else 0
            ),
            "total_retries": self.total_retries,
            "total_cost": self.total_cost,
            "nodes": {
                name: [
                    {
                        "start": m.start_time.isoformat(),
                        "end": m.end_time.isoformat() if m.end_time else None,
                        "duration_ms": m.duration_ms,
                        "success": m.success,
                        "error": m.error,
                    }
                    for m in metrics
                ]
                for name, metrics in self.node_metrics.items()
            },
        }
