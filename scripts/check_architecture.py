#!/usr/bin/env python3
"""Automated architecture-boundary checks for StoreOps.

Enforces two of the harness's hard gates (Evaluator dimension: Architecture Compliance —
see .harness/skills/grading-criteria/SKILL.md):

  1. Module boundary  — no module may import another module's repository.py directly.
     Cross-module reads must go through the target module's service.py.
  2. Layer separation — repository.py must never import fastapi (no HTTP concerns in the
     data layer); routes.py must never import its own module's repository directly (must
     go through its own service.py).

This directly targets client failure modes 1 and (partially) 4 from the case study's
Section 2 (direct imports bypassing the service boundary; state changes written directly
to sibling module repositories).

Exit code 0 = no violations. Exit code 1 = at least one violation, printed to stdout.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent / "app"
MODULES = {"activities", "programmes", "staff", "alerts", "reports"}

REPO_IMPORT_RE = re.compile(r"from app\.([a-z]+)\.repository import")


def check_module_boundary() -> list[str]:
    violations = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        rel = path.relative_to(APP_ROOT)
        owning_module = rel.parts[0] if rel.parts[0] in MODULES else None
        text = path.read_text()
        for match in REPO_IMPORT_RE.finditer(text):
            imported_module = match.group(1)
            if imported_module != owning_module:
                line_no = text[: match.start()].count("\n") + 1
                violations.append(
                    f"{path.relative_to(APP_ROOT.parent)}:{line_no}: imports "
                    f"app.{imported_module}.repository from outside app/{imported_module}/ "
                    f"(owning module: {owning_module or 'shared'}) — go through "
                    f"app.{imported_module}.service instead"
                )
    return violations


def check_layer_separation() -> list[str]:
    violations = []
    for path in sorted(APP_ROOT.rglob("repository.py")):
        text = path.read_text()
        if "fastapi" in text:
            violations.append(
                f"{path.relative_to(APP_ROOT.parent)}: repository.py must not import "
                f"fastapi — HTTP concerns belong in routes.py"
            )
    for path in sorted(APP_ROOT.rglob("routes.py")):
        owning_module = path.relative_to(APP_ROOT).parts[0]
        text = path.read_text()
        if re.search(rf"from app\.{owning_module}\.repository import", text):
            violations.append(
                f"{path.relative_to(APP_ROOT.parent)}: routes.py must not import its own "
                f"repository directly — go through service.py"
            )
    return violations


def main() -> int:
    violations = check_module_boundary() + check_layer_separation()
    if violations:
        print("Architecture boundary violations found:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("Architecture boundary checks passed: 0 violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
