#!/usr/bin/env python3
"""Reject repo-owned GitHub workflow pins that are not Node 24 ready."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

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


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _major(version: str) -> int | None:
    match = MAJOR_RE.match(version)
    if match is None:
        return None
    return int(match.group(1))


def validate_workflows(root: Path) -> list[str]:
    errors: list[str] = []
    for path in workflow_files(root):
        rel = _relative(root, path)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "node20" in line.lower():
                errors.append(f"{rel}:{line_number} references node20 explicitly")

            match = USES_RE.search(line)
            if match is None:
                continue

            action, version = match.groups()
            minimum = MINIMUM_ACTION_MAJORS.get(action)
            if minimum is None:
                continue

            major = _major(version)
            if major is None or major < minimum:
                errors.append(f"{rel}:{line_number} uses {action}@{version}; expected v{minimum}+")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root to scan")
    args = parser.parse_args(argv)

    errors = validate_workflows(args.root.resolve())
    for error in errors:
        print(f"::error::{error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
