"""
AgentPort generator — renders Jinja2 templates from a CompiledPlan into
a full Python project directory.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .compiler import CompiledPlan

# ── Jinja2 custom filters ─────────────────────────────────────────────────────

_TYPE_MAP: dict[str, str] = {
    "str": "str",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "list": "list",
    "dict": "dict",
    "Any": "Any",
}


def _python_type(schema_type: str) -> str:
    return _TYPE_MAP.get(schema_type, "Any")


def _python_repr(value: Any) -> str:
    """Render a Python value as a valid Python literal (handles JSON types)."""
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, list):
        inner = ", ".join(_python_repr(v) for v in value)
        return f"[{inner}]"
    if isinstance(value, dict):
        pairs = ", ".join(
            f"{_python_repr(k)}: {_python_repr(v)}" for k, v in value.items()
        )
        return f"{{{pairs}}}"
    # Fallback: JSON → Python (safe for the types we accept)
    return json.dumps(value)


# ── template environment ──────────────────────────────────────────────────────

def _build_env(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["python_type"] = _python_type
    env.filters["python_repr"] = _python_repr
    return env


# ── file manifest ─────────────────────────────────────────────────────────────

# Maps template filename → generated output path (relative to output root)
_PACKAGE_TEMPLATES: list[tuple[str, str]] = [
    ("state.py.j2", "{pkg}/state.py"),
    ("tools.py.j2", "{pkg}/tools.py"),
    ("graph.py.j2", "{pkg}/graph.py"),
    ("audit.py.j2", "{pkg}/audit.py"),
    ("main.py.j2", "{pkg}/main.py"),
]

_INFRA_TEMPLATES: list[tuple[str, str]] = [
    ("requirements.txt.j2", "requirements.txt"),
    ("Dockerfile.j2", "Dockerfile"),
    ("docker-compose.yml.j2", "docker-compose.yml"),
    (".env.example.j2", ".env.example"),
]


# ── public API ────────────────────────────────────────────────────────────────

def generate(
    plan: CompiledPlan,
    output_dir: Path | str,
    templates_dir: Path | str | None = None,
) -> Path:
    """
    Render all templates and write the generated project to *output_dir*.

    Returns the output directory path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Locate templates directory relative to this file if not provided
    if templates_dir is None:
        templates_dir = Path(__file__).parent.parent.parent / "templates"
    templates_dir = Path(templates_dir)

    env = _build_env(templates_dir)

    # Snake-case package name
    pkg = re.sub(r"[^a-z0-9_]", "_", plan.schema.name.lower())

    ctx: dict[str, Any] = {
        "schema": plan.schema,
        "plan": plan,
    }

    # Package directory (e.g. output_dir/patient_intake/)
    pkg_dir = output_dir / pkg
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "__init__.py").write_text(
        f'"""Auto-generated package for {plan.schema.name}."""\n'
    )

    # Render Python source files
    for tmpl_name, out_rel in _PACKAGE_TEMPLATES:
        out_path = output_dir / out_rel.format(pkg=pkg)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmpl = env.get_template(tmpl_name)
        out_path.write_text(tmpl.render(**ctx))

    # Render infra files at root
    for tmpl_name, out_rel in _INFRA_TEMPLATES:
        out_path = output_dir / out_rel
        tmpl = env.get_template(tmpl_name)
        out_path.write_text(tmpl.render(**ctx))

    return output_dir
