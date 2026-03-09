"""
AgentPort validator — validates an AgentSchema and returns structured errors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

from .schema import AgentSchema, EdgeCondition, NodeType


@dataclass
class ValidationError:
    field: str
    message: str
    severity: Literal["error", "warning"] = "error"

    def __str__(self) -> str:
        tag = "ERROR" if self.severity == "error" else "WARN"
        return f"[{tag}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def __str__(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(str(e))
        for w in self.warnings:
            lines.append(str(w))
        if not lines:
            lines.append("OK — no issues found")
        return "\n".join(lines)


def validate(schema: AgentSchema) -> ValidationResult:
    """Validate an AgentSchema and return a ValidationResult with all issues."""
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    def err(f: str, msg: str) -> None:
        errors.append(ValidationError(f, msg, "error"))

    def warn(f: str, msg: str) -> None:
        warnings.append(ValidationError(f, msg, "warning"))

    node_names = {n.name for n in schema.nodes}
    tool_names = {t.name for t in schema.tools}

    # ── Schema basics ─────────────────────────────────────────────────────────
    if not schema.name:
        err("name", "Agent name is required")
    if not schema.name.replace("_", "").replace("-", "").isalnum():
        err("name", f"Agent name must be alphanumeric (got '{schema.name}')")
    if not schema.nodes:
        err("nodes", "At least one node is required")
    if not schema.edges:
        err("edges", "At least one edge is required")

    # ── Node validation ────────────────────────────────────────────────────────
    for node in schema.nodes:
        if node.type == NodeType.llm and node.tools:
            for tname in node.tools:
                if tname not in tool_names:
                    err(f"nodes[{node.name}].tools", f"Unknown tool '{tname}'")
        if node.type == NodeType.llm and not node.system_prompt:
            warn(f"nodes[{node.name}]", "LLM node has no system_prompt")

    llm_nodes = [n for n in schema.nodes if n.type == NodeType.llm]
    if not llm_nodes:
        warn("nodes", "No LLM nodes defined — agent will not call an LLM")

    # ── Edge validation ────────────────────────────────────────────────────────
    valid_froms = node_names | {"__start__"}
    valid_tos = node_names | {"__end__"}

    has_start_edge = False
    has_end_edge = False
    seen_unconditional: dict[str, int] = {}  # from_node → count

    for i, edge in enumerate(schema.edges):
        if edge.from_node not in valid_froms:
            err(f"edges[{i}].from", f"Unknown node '{edge.from_node}'")
        if edge.to not in valid_tos:
            err(f"edges[{i}].to", f"Unknown node '{edge.to}'")
        if edge.from_node == "__start__":
            has_start_edge = True
        if edge.to == "__end__":
            has_end_edge = True
        if edge.condition is None:
            seen_unconditional[edge.from_node] = seen_unconditional.get(edge.from_node, 0) + 1

    if not has_start_edge:
        err("edges", "No edge from __start__ — graph has no entry point")
    if not has_end_edge:
        warn("edges", "No edge to __end__ — graph may run forever")

    # A node with both conditional and unconditional outgoing edges is ambiguous
    for node in schema.nodes:
        outgoing = [e for e in schema.edges if e.from_node == node.name]
        has_cond = any(e.condition is not None for e in outgoing)
        has_uncond = any(e.condition is None for e in outgoing)
        if has_cond and has_uncond:
            warn(
                f"nodes[{node.name}]",
                "Node has both conditional and unconditional outgoing edges — "
                "unconditional edges will be ignored in favour of conditional routing",
            )

    # ── Tool validation ────────────────────────────────────────────────────────
    for tool in schema.tools:
        if not tool.name.replace("_", "").isalnum():
            err(f"tools[{tool.name}]", "Tool name must be alphanumeric with underscores")
        param_names: set[str] = set()
        for p in tool.parameters:
            if p.name in param_names:
                err(f"tools[{tool.name}].parameters", f"Duplicate parameter '{p.name}'")
            param_names.add(p.name)

    # ── Compliance checks ──────────────────────────────────────────────────────
    phi_fields = [k for k, v in schema.state.items() if v.phi]
    if phi_fields and "HIPAA" not in schema.compliance:
        warn(
            "compliance",
            f"State fields {phi_fields} are marked phi=true but HIPAA is not listed in compliance",
        )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_yaml(path: str | Path) -> tuple[AgentSchema | None, ValidationResult]:
    """Load a YAML file, parse into AgentSchema, and validate it."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text())

    try:
        schema = AgentSchema.model_validate(raw)
    except Exception as exc:
        result = ValidationResult(
            valid=False,
            errors=[ValidationError("schema", f"Failed to parse YAML: {exc}", "error")],
        )
        return None, result

    result = validate(schema)
    return schema, result
