"""
AgentPort compiler — resolves references, topologically sorts the graph,
and produces a CompiledPlan ready for template rendering.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .schema import AgentSchema, EdgeCondition, NodeSchema, NodeType, ToolSchema


@dataclass
class CompiledNode:
    name: str
    type: NodeType
    system_prompt: str | None
    tools: list[ToolSchema]  # resolved tool objects (empty for tool_executor)


@dataclass
class CompiledEdge:
    from_node: str
    to: str
    condition: EdgeCondition | None


@dataclass
class ConditionalGroup:
    """All outgoing conditional edges from a single source node."""
    from_node: str
    # condition-value → target node name (or __end__)
    routes: dict[str, str] = field(default_factory=dict)


@dataclass
class CompiledPlan:
    schema: AgentSchema
    nodes: list[CompiledNode]
    edges: list[CompiledEdge]
    # Nodes whose outbound edges are all unconditional (add_edge)
    simple_edges: list[CompiledEdge]
    # Per-source conditional routing groups (add_conditional_edges)
    conditional_groups: list[ConditionalGroup]
    # Flat map of tool name → ToolSchema for all tools in the schema
    tool_map: dict[str, ToolSchema]
    # Topological order of node names (excluding __start__ / __end__)
    execution_order: list[str]


# ── helpers ───────────────────────────────────────────────────────────────────

def _topological_sort(
    nodes: list[str],
    edges: list[CompiledEdge],
) -> list[str]:
    """Kahn's algorithm. __start__ / __end__ are excluded from the result."""
    real_nodes = [n for n in nodes if n not in ("__start__", "__end__")]
    # Build adjacency + in-degree
    in_degree: dict[str, int] = {n: 0 for n in real_nodes}
    adj: dict[str, list[str]] = {n: [] for n in real_nodes}
    for e in edges:
        src = e.from_node if e.from_node != "__start__" else None
        dst = e.to if e.to != "__end__" else None
        if src and dst:
            adj[src].append(dst)
            in_degree[dst] += 1

    queue = [n for n in real_nodes if in_degree[n] == 0]
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for nxt in adj.get(node, []):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    # If we have a cycle the order will be shorter than real_nodes;
    # fall back to declaration order (graph is still runnable in LangGraph).
    if len(order) < len(real_nodes):
        return real_nodes
    return order


# ── public API ────────────────────────────────────────────────────────────────

def compile_schema(schema: AgentSchema) -> CompiledPlan:
    """Compile a validated AgentSchema into a CompiledPlan."""

    tool_map: dict[str, ToolSchema] = {t.name: t for t in schema.tools}

    # Resolve nodes
    compiled_nodes: list[CompiledNode] = []
    for node in schema.nodes:
        resolved_tools: list[ToolSchema] = []
        if node.tools:
            for tname in node.tools:
                if tname in tool_map:
                    resolved_tools.append(tool_map[tname])
        compiled_nodes.append(
            CompiledNode(
                name=node.name,
                type=node.type,
                system_prompt=node.system_prompt,
                tools=resolved_tools,
            )
        )

    # Resolve edges
    compiled_edges: list[CompiledEdge] = [
        CompiledEdge(from_node=e.from_node, to=e.to, condition=e.condition)
        for e in schema.edges
    ]

    # Partition into simple vs conditional
    # A source node uses conditional routing if *any* outgoing edge has a condition.
    conditional_sources: set[str] = {
        e.from_node for e in compiled_edges if e.condition is not None
    }
    simple_edges = [e for e in compiled_edges if e.from_node not in conditional_sources]

    # Build conditional groups
    groups: dict[str, ConditionalGroup] = {}
    for edge in compiled_edges:
        if edge.from_node in conditional_sources:
            if edge.from_node not in groups:
                groups[edge.from_node] = ConditionalGroup(from_node=edge.from_node)
            condition_key = edge.condition.value if edge.condition else "always"
            groups[edge.from_node].routes[condition_key] = edge.to

    node_names = [n.name for n in schema.nodes]
    execution_order = _topological_sort(node_names, compiled_edges)

    return CompiledPlan(
        schema=schema,
        nodes=compiled_nodes,
        edges=compiled_edges,
        simple_edges=simple_edges,
        conditional_groups=list(groups.values()),
        tool_map=tool_map,
        execution_order=execution_order,
    )
