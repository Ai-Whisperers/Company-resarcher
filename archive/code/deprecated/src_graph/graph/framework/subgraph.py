"""
Subgraph and conditional edge configuration.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Any, List

from src.core.logging import setup_logger

logger = setup_logger("graph_subgraph")


@dataclass
class ConditionalEdgeConfig:
    """
    Configuration for a conditional edge.

    Provides more flexibility in defining conditional routing.
    """

    from_node: str
    condition: Callable[[Any], str]
    branches: Dict[str, str]
    default_branch: Optional[str] = None
    fallback_on_error: Optional[str] = None

    def evaluate(self, state: Any) -> str:
        """Evaluate the condition and return the target node."""
        try:
            result = self.condition(state)
            if result in self.branches:
                return self.branches[result]
            if self.default_branch:
                return self.default_branch
            raise ValueError(f"Condition returned unknown branch: {result}")
        except Exception as e:
            if self.fallback_on_error:
                logger.warning(f"Conditional edge error, using fallback: {e}")
                return self.fallback_on_error
            raise


class Subgraph:
    """
    Represents a subgraph that can be embedded in a parent graph.

    Subgraphs enable modular graph composition and reuse.
    """

    def __init__(
        self,
        name: str,
        entry_node: str,
        exit_node: str,
    ):
        self.name = name
        self.entry_node = entry_node
        self.exit_node = exit_node
        self._nodes: Dict[str, Callable] = {}
        self._edges: List[Tuple[str, str]] = []
        self._conditional_edges: List[ConditionalEdgeConfig] = []

    def add_node(self, name: str, func: Callable) -> "Subgraph":
        """Add a node to the subgraph."""
        self._nodes[f"{self.name}_{name}"] = func
        return self

    def add_edge(self, from_node: str, to_node: str) -> "Subgraph":
        """Add an edge within the subgraph."""
        self._edges.append((f"{self.name}_{from_node}", f"{self.name}_{to_node}"))
        return self

    def add_conditional_edge(self, config: ConditionalEdgeConfig) -> "Subgraph":
        """Add a conditional edge within the subgraph."""
        prefixed_config = ConditionalEdgeConfig(
            from_node=f"{self.name}_{config.from_node}",
            condition=config.condition,
            branches={k: f"{self.name}_{v}" for k, v in config.branches.items()},
            default_branch=(
                f"{self.name}_{config.default_branch}"
                if config.default_branch
                else None
            ),
            fallback_on_error=(
                f"{self.name}_{config.fallback_on_error}"
                if config.fallback_on_error
                else None
            ),
        )
        self._conditional_edges.append(prefixed_config)
        return self

    def get_prefixed_entry(self) -> str:
        """Get the prefixed entry node name."""
        return f"{self.name}_{self.entry_node}"

    def get_prefixed_exit(self) -> str:
        """Get the prefixed exit node name."""
        return f"{self.name}_{self.exit_node}"

    def get_nodes(self) -> Dict[str, Callable]:
        """Get all nodes with prefixed names."""
        return self._nodes

    def get_edges(self) -> List[Tuple[str, str]]:
        """Get all edges with prefixed node names."""
        return self._edges

    def get_conditional_edges(self) -> List[ConditionalEdgeConfig]:
        """Get all conditional edges."""
        return self._conditional_edges
