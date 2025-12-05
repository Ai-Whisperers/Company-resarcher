"""
Graph backend abstraction layer.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any


class GraphBackend(ABC):
    """
    Abstract interface for graph execution backends.

    Addresses tight coupling to LangGraph by providing an abstraction
    layer that allows switching to different graph execution frameworks.
    """

    @abstractmethod
    def add_node(self, name: str, func: Callable) -> None:
        """Add a node to the graph."""
        pass

    @abstractmethod
    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add an edge between nodes."""
        pass

    @abstractmethod
    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable,
        branches: Dict[str, str],
    ) -> None:
        """Add a conditional edge from a node."""
        pass

    @abstractmethod
    def set_entry_point(self, node_name: str) -> None:
        """Set the graph entry point."""
        pass

    @abstractmethod
    def set_end_node(self, node_name: str) -> None:
        """Mark a node as an end node."""
        pass

    @abstractmethod
    def compile(self) -> Any:
        """Compile the graph for execution."""
        pass


class LangGraphBackend(GraphBackend):
    """
    LangGraph implementation of the graph backend.

    This wraps LangGraph's StateGraph to implement the GraphBackend interface.
    """

    def __init__(self, state_class: type):
        # Import here to isolate LangGraph dependency
        from langgraph.graph import StateGraph, END

        self._StateGraph = StateGraph
        self._END = END
        self._graph = StateGraph(state_class)
        self._end_marker = END

    def add_node(self, name: str, func: Callable) -> None:
        self._graph.add_node(name, func)

    def add_edge(self, from_node: str, to_node: str) -> None:
        if to_node == "__end__":
            self._graph.add_edge(from_node, self._end_marker)
        else:
            self._graph.add_edge(from_node, to_node)

    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable,
        branches: Dict[str, str],
    ) -> None:
        # Convert __end__ markers
        converted_branches = {
            k: self._end_marker if v == "__end__" else v for k, v in branches.items()
        }
        self._graph.add_conditional_edges(from_node, condition, converted_branches)

    def set_entry_point(self, node_name: str) -> None:
        self._graph.set_entry_point(node_name)

    def set_end_node(self, node_name: str) -> None:
        self._graph.add_edge(node_name, self._end_marker)

    def compile(self) -> Any:
        return self._graph.compile()
