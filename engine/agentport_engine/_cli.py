"""Minimal CLI entry-point: agentport <yaml_path> [output_zip]"""
from __future__ import annotations

import sys
from pathlib import Path

from . import package_yaml


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: agentport <agent.yaml> [output.zip]", file=sys.stderr)
        sys.exit(1)

    yaml_path = Path(args[0])
    output_zip = Path(args[1]) if len(args) > 1 else None

    try:
        zip_path, result = package_yaml(yaml_path, output_zip)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if result.warnings:
        for w in result.warnings:
            print(w, file=sys.stderr)

    print(f"✓ Generated: {zip_path}")


if __name__ == "__main__":
    main()
