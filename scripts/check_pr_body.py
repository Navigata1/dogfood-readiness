#!/usr/bin/env python3
"""Validate evidence sections in PR bodies."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = (
    "## Dogfood Readiness",
    "### Current truth",
    "### Local verification",
    "### Remote verification",
    "### Evidence bundle",
    "### Deferred / out of scope",
)


def section(body: str, heading: str) -> str:
    start = body.find(heading)
    if start < 0:
        return ""
    next_heading = body.find("\n### ", start + len(heading))
    return body[start:] if next_heading < 0 else body[start:next_heading]


def has_checked_item(text: str) -> bool:
    return bool(re.search(r"(?m)^\s*-\s+\[x\]\s+", text))


def validate(body: str) -> list[str]:
    errors: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if heading not in body:
            errors.append(f"missing required heading: {heading}")

    for heading in ("### Current truth", "### Local verification", "### Evidence bundle"):
        if heading in body and not has_checked_item(section(body, heading)):
            errors.append(f"{heading} must include at least one checked evidence item")

    if "production ready" in body.lower() and "not production ready" not in body.lower():
        errors.append("unqualified production-ready claim")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", required=True)
    args = parser.parse_args()

    body = Path(args.body_file).read_text(encoding="utf-8")
    errors = validate(body)
    if errors:
        for error in errors:
            print(f"::error::{error}", file=sys.stderr)
        return 1
    print("dogfood-readiness-pr-body: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

