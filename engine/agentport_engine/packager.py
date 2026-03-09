"""
AgentPort packager — takes a generated project directory and produces a
distributable ZIP archive with Dockerfile, docker-compose, .env.example,
and requirements.txt included.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .compiler import CompiledPlan, compile_schema
from .generator import generate
from .validator import ValidationResult, validate, validate_yaml


def package(
    plan: CompiledPlan,
    output_zip: Path | str,
    templates_dir: Path | str | None = None,
) -> Path:
    """
    Generate a full project from *plan* and compress it to *output_zip*.

    Returns the path to the created ZIP file (with .zip extension appended
    if missing).
    """
    output_zip = Path(output_zip)
    if output_zip.suffix != ".zip":
        output_zip = output_zip.with_suffix(".zip")

    with tempfile.TemporaryDirectory(prefix="agentport_") as tmpdir:
        project_dir = Path(tmpdir) / plan.schema.name
        generate(plan, project_dir, templates_dir=templates_dir)

        # shutil.make_archive wants the base name *without* .zip
        archive_base = str(output_zip.with_suffix(""))
        shutil.make_archive(
            base_name=archive_base,
            format="zip",
            root_dir=project_dir,
            base_dir=".",
        )

    return output_zip


def package_yaml(
    yaml_path: Path | str,
    output_zip: Path | str | None = None,
    templates_dir: Path | str | None = None,
) -> tuple[Path, ValidationResult]:
    """
    High-level convenience: YAML path → ZIP file.

    If *output_zip* is not specified the archive is written next to the YAML
    file with the agent name as the filename.

    Returns ``(zip_path, validation_result)``.  Raises ``ValueError`` if
    validation fails.
    """
    yaml_path = Path(yaml_path)
    schema, result = validate_yaml(yaml_path)

    if not result.valid:
        raise ValueError(
            f"Validation failed for '{yaml_path}':\n{result}"
        )

    plan = compile_schema(schema)  # type: ignore[arg-type]

    if output_zip is None:
        output_zip = yaml_path.parent / f"{schema.name}.zip"  # type: ignore[union-attr]

    zip_path = package(plan, output_zip, templates_dir=templates_dir)
    return zip_path, result
