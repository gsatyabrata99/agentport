"""
agentport_engine — the AgentPort code-generation engine.

Public API
----------
validate_yaml(path)          → (AgentSchema | None, ValidationResult)
validate(schema)             → ValidationResult
compile_schema(schema)       → CompiledPlan
generate(plan, output_dir)   → Path
package(plan, output_zip)    → Path
package_yaml(yaml_path)      → (Path, ValidationResult)
"""
from .compiler import CompiledPlan, compile_schema
from .generator import generate
from .packager import package, package_yaml
from .schema import AgentSchema
from .validator import ValidationResult, validate, validate_yaml

__all__ = [
    "AgentSchema",
    "ValidationResult",
    "CompiledPlan",
    "validate",
    "validate_yaml",
    "compile_schema",
    "generate",
    "package",
    "package_yaml",
]
