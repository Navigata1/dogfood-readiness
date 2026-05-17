#!/usr/bin/env python3
"""Reject repo-owned GitHub workflow pins that are not Node 24 ready."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

MINIMUM_ACTION_MAJORS = {
    "actions/checkout": 6,
    "actions/setup-python": 6,
    "actions/cache": 5,
    "actions/upload-artifact": 6,
    "actions/download-artifact": 8,
    "github/codeql-action/init": 4,
    "github/codeql-action/autobuild": 4,
    "github/codeql-action/analyze": 4,
}

USES_RE = re.compile(r"\buses:\s*['\"]?([^@'\"\s#]+)@([^'\"\s#]+)")
MAJOR_RE = re.compile(r"^v([0-9]+)(?:\.|$)")


def workflow_files(root: Path) -> list[Path]:
    workflow_root = root / ".github" / "workflows"
    if not workflow_root.is_dir():
        return []
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in workflow_root.glob(pattern)
        if path.is_file()
    )


def _major(version: str) -> int | None:
    match = MAJOR_RE.match(version)
    if match is None:
        return None
    return int(match.group(1))


def validate_text(path: Path, text: str) -> list[str]:
    """Return workflow action-runtime errors for one workflow body."""
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if "node20" in line.lower():
            errors.append(f"{path}:{line_number} references node20 explicitly")

        match = USES_RE.search(line)
        if match is None:
            continue

        action, version = match.groups()
        minimum = MINIMUM_ACTION_MAJORS.get(action)
        if minimum is None:
            continue

        major = _major(version)
        if major is None or major < minimum:
            errors.append(f"{path}:{line_number} uses {action}@{version}; expected v{minimum}+")
    return errors


def validate_workflows(root: Path) -> list[str]:
    errors: list[str] = []
    for path in workflow_files(root):
        rel = path.relative_to(root)
        errors.extend(validate_text(rel, path.read_text(encoding="utf-8")))
    return errors


def validate(workflows: Path = WORKFLOWS) -> list[str]:
    """Return all repo workflow action-runtime errors."""
    root = workflows.parent.parent if workflows.name == "workflows" else workflows
    return validate_workflows(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to scan")
    args = parser.parse_args(argv)

    errors = validate_workflows(args.root.resolve())
    for error in errors:
        print(f"::error::{error}", file=sys.stderr)
    if errors:
        return 1
    print("github-actions-node24: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
