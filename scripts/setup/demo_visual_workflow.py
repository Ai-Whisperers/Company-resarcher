"""
Demo of the built-in Visual Workflow system.
This generates JSON/YAML that can be visualized with tools like:
- Draw.io (import JSON)
- Mermaid (generate diagrams)
- D3.js / React Flow (web visualization)

No cloud service needed - everything is local!
"""
import asyncio
import json
from pathlib import Path

from src.core.workflow.visual_workflow import (
    WorkflowManager,
    NodeType,
)


def create_research_workflow():
    """Create a visual workflow for company research."""

    manager = WorkflowManager()

    # Build the workflow
    workflow = (
        manager.create_workflow(
            name="Company Research Pipeline",
            description="Multi-stage company intelligence gathering"
        )
        .start(node_id="start")
        .variable(
            node_id="set_company",
            name="company_name",
            value="{{input.company_name}}"
        )

        # Search Phase
        .tool(
            node_id="web_search",
            tool="tavily_search",
            args={"query": "{{company_name}} company information"},
            name="Search Web"
        )

        # Analysis Phase
        .llm(
            node_id="analyze_results",
            prompt="Analyze these search results for {{company_name}}: {{web_search}}",
            system="You are a business analyst specializing in company research.",
            name="Analyze Results"
        )

        # Check quality
        .if_else(
            node_id="quality_check",
            condition="len(analyze_results) > 100",
            true_target="generate_report",
            false_target="search_more"
        )

        # Branch 1: Good results
        .template(
            node_id="generate_report",
            template="# {{company_name}} Research Report\n\n{{analyze_results}}",
            name="Generate Report"
        )
        .connect("generate_report", "end")

        # Branch 2: Need more data
        .tool(
            node_id="search_more",
            tool="tavily_search",
            args={"query": "{{company_name}} detailed analysis"},
            name="Deep Search"
        )
        .connect("search_more", "generate_report")

        .end(node_id="end", output_key="generate_report")
        .build()
    )

    return workflow


def export_workflow_formats(workflow):
    """Export workflow to multiple formats for visualization."""

    output_dir = Path("workflow_exports")
    output_dir.mkdir(exist_ok=True)

    # Export to JSON
    json_path = output_dir / "research_workflow.json"
    json_path.write_text(workflow.to_json())
    print(f"✓ Exported JSON: {json_path}")

    # Export to YAML
    yaml_path = output_dir / "research_workflow.yaml"
    yaml_path.write_text(workflow.to_yaml())
    print(f"✓ Exported YAML: {yaml_path}")

    # Export to Mermaid diagram
    mermaid = generate_mermaid_diagram(workflow)
    mermaid_path = output_dir / "research_workflow.mmd"
    mermaid_path.write_text(mermaid)
    print(f"✓ Exported Mermaid: {mermaid_path}")

    # Export node list for documentation
    nodes_md = generate_nodes_markdown(workflow)
    nodes_path = output_dir / "workflow_nodes.md"
    nodes_path.write_text(nodes_md)
    print(f"✓ Exported Docs: {nodes_path}")


def generate_mermaid_diagram(workflow):
    """Generate a Mermaid flowchart from workflow."""

    lines = ["graph TD"]

    for node_id, node in workflow.nodes.items():
        # Format node based on type
        if node.node_type == NodeType.START:
            lines.append(f'    {node_id}[["START"]]')
        elif node.node_type == NodeType.END:
            lines.append(f'    {node_id}[["END"]]')
        elif node.node_type == NodeType.IF_ELSE:
            lines.append(f'    {node_id}{{{node.name}}}')
        elif node.node_type == NodeType.LLM:
            lines.append(f'    {node_id}["🤖 {node.name}"]')
        elif node.node_type == NodeType.TOOL:
            lines.append(f'    {node_id}["🔧 {node.name}"]')
        else:
            lines.append(f'    {node_id}["{node.name}"]')

    # Add edges
    for edge_id, edge in workflow.edges.items():
        if edge.edge_type.value == "true":
            lines.append(f'    {edge.source_id} -->|Yes| {edge.target_id}')
        elif edge.edge_type.value == "false":
            lines.append(f'    {edge.source_id} -->|No| {edge.target_id}')
        else:
            lines.append(f'    {edge.source_id} --> {edge.target_id}')

    return "\n".join(lines)


def generate_nodes_markdown(workflow):
    """Generate markdown documentation of nodes."""

    lines = [f"# {workflow.name}\n"]
    lines.append(f"{workflow.description}\n")
    lines.append(f"## Workflow Nodes ({len(workflow.nodes)})\n")

    for node_id, node in workflow.nodes.items():
        lines.append(f"### {node.name} (`{node_id}`)")
        lines.append(f"- **Type:** {node.node_type.value}")
        lines.append(f"- **Description:** {node.description or 'N/A'}")

        if node.config:
            lines.append(f"- **Config:** `{node.config}`")

        # Show connections
        outgoing = workflow.get_outgoing_edges(node_id)
        if outgoing:
            lines.append(f"- **Next:** {', '.join(e.target_id for e in outgoing)}")

        lines.append("")

    return "\n".join(lines)


async def test_workflow_execution(workflow):
    """Execute the workflow and track execution."""

    from src.core.workflow.visual_workflow import WorkflowEngine

    # Create engine
    engine = WorkflowEngine()

    # Register mock tools for demo
    def mock_search(query):
        return f"Search results for: {query}\n- Result 1\n- Result 2\n- Result 3"

    engine.register_tools({
        "tavily_search": mock_search
    })

    # Register mock LLM
    async def mock_llm(prompt, system=""):
        return f"Analysis complete for the query. Found relevant information."

    engine.register_llm(mock_llm)

    # Execute
    print("\n" + "="*60)
    print("Executing Workflow...")
    print("="*60)

    result = await engine.execute(
        workflow,
        input_data={"company_name": "Tesla"}
    )

    print(f"\nStatus: {result.status.value}")
    print(f"Duration: {result.duration_ms:.2f}ms")
    print(f"\nNodes executed: {len(result.node_results)}")

    for node_id, node_result in result.node_results.items():
        print(f"  - {node_id}: {node_result.status.value} ({node_result.duration_ms:.2f}ms)")

    # Export execution trace
    trace_path = Path("workflow_exports") / "execution_trace.json"
    trace_path.write_text(json.dumps(result.to_dict(), indent=2))
    print(f"\n✓ Execution trace saved: {trace_path}")


async def main():
    """Demo the visual workflow system."""

    print("="*60)
    print("Visual Workflow Demo - Local Visualization")
    print("="*60)

    # Create workflow
    print("\n1. Creating workflow...")
    workflow = create_research_workflow()

    # Validate
    valid, errors = workflow.validate()
    if valid:
        print("   ✓ Workflow is valid")
    else:
        print("   ✗ Validation errors:")
        for error in errors:
            print(f"     - {error}")
        return

    # Export to various formats
    print("\n2. Exporting to visualization formats...")
    export_workflow_formats(workflow)

    # Test execution
    print("\n3. Testing workflow execution...")
    await test_workflow_execution(workflow)

    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("\n📊 Visualize your workflow:")
    print("  1. Mermaid: Copy workflow_exports/research_workflow.mmd")
    print("     to https://mermaid.live")
    print("\n  2. Draw.io: Import workflow_exports/research_workflow.json")
    print("     at https://app.diagrams.net")
    print("\n  3. View execution trace:")
    print("     cat workflow_exports/execution_trace.json")
    print("\n  4. Read documentation:")
    print("     cat workflow_exports/workflow_nodes.md")


if __name__ == "__main__":
    asyncio.run(main())
