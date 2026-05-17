#!/usr/bin/env python3
"""Check first-party GitHub Actions pins for Node 24-compatible majors."""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

MINIMUM_FIRST_PARTY_ACTION_MAJORS = {
    "actions/checkout": 6,
    "actions/setup-python": 6,
    "actions/cache": 5,
    "actions/upload-artifact": 6,
    "actions/download-artifact": 8,
}

USES_RE = re.compile(r"uses:\s*[\"']?(actions/[a-z-]+)@v([0-9]+)")


def validate_text(path: Path, text: str) -> list[str]:
    """Return workflow action-runtime errors for a single workflow body."""
    errors: list[str] = []
    for match in USES_RE.finditer(text):
        action = match.group(1)
        major = int(match.group(2))
        minimum = MINIMUM_FIRST_PARTY_ACTION_MAJORS.get(action)
        if minimum is not None and major < minimum:
            errors.append(f"{path} pins {action}@v{major}; expected v{minimum}+")

    if "node20" in text.lower():
        errors.append(f"{path} mentions node20 explicitly")

    return errors


def validate(workflows: Path = WORKFLOWS) -> list[str]:
    """Return all first-party GitHub Actions runtime pin errors."""
    errors: list[str] = []
    for workflow in sorted(workflows.glob("*.yml")):
        path = workflow.relative_to(ROOT)
        errors.extend(validate_text(path, workflow.read_text(encoding="utf-8")))
    return errors


def main() -> int:
    errors = validate()
    for error in errors:
        print(f"::error::{error}", file=sys.stderr)
    if errors:
        return 1
    print("github-actions-node24: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
