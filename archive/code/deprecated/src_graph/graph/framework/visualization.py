"""
Graph visualization utilities.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any


@dataclass
class GraphVisualization:
    """
    Graph visualization data structure.

    Provides methods to export graph structure for visualization.
    """

    nodes: List[str]
    edges: List[Tuple[str, str]]
    conditional_edges: List[Tuple[str, List[str]]]
    entry_point: Optional[str] = None
    end_nodes: List[str] = field(default_factory=list)

    def to_mermaid(self) -> str:
        """Export graph as Mermaid diagram syntax."""
        lines = ["graph TD"]

        # Add entry point marker
        if self.entry_point:
            lines.append(f"    START([Start]) --> {self.entry_point}")

        # Add regular edges
        for from_node, to_node in self.edges:
            if to_node == "__end__":
                lines.append(f"    {from_node} --> END([End])")
            else:
                lines.append(f"    {from_node} --> {to_node}")

        # Add conditional edges
        for from_node, targets in self.conditional_edges:
            for target in targets:
                if target == "__end__":
                    lines.append(f"    {from_node} -.-> END([End])")
                else:
                    lines.append(f"    {from_node} -.-> {target}")

        # Mark end nodes
        for node in self.end_nodes:
            if node not in [t for _, t in self.edges]:
                lines.append(f"    {node} --> END([End])")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Export graph as DOT format (Graphviz)."""
        lines = ["digraph G {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box];")

        # Add start node
        if self.entry_point:
            lines.append('    START [shape=ellipse, label="Start"];')
            lines.append(f"    START -> {self.entry_point};")

        # Add end node
        lines.append('    END [shape=ellipse, label="End"];')

        # Add regular edges
        for from_node, to_node in self.edges:
            if to_node == "__end__":
                lines.append(f"    {from_node} -> END;")
            else:
                lines.append(f"    {from_node} -> {to_node};")

        # Add conditional edges (dashed)
        for from_node, targets in self.conditional_edges:
            for target in targets:
                if target == "__end__":
                    lines.append(f"    {from_node} -> END [style=dashed];")
                else:
                    lines.append(f"    {from_node} -> {target} [style=dashed];")

        lines.append("}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "nodes": self.nodes,
            "edges": [{"from": f, "to": t} for f, t in self.edges],
            "conditional_edges": [
                {"from": f, "targets": t} for f, t in self.conditional_edges
            ],
            "entry_point": self.entry_point,
            "end_nodes": self.end_nodes,
        }
