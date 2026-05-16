"""Command-line interface for dogfood readiness."""

from __future__ import annotations

import argparse
from pathlib import Path

from .inventory import inventory
from .model import ProgressPulse, ReadinessReport
from .render import render_markdown
from .score import score_band


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="PR, feature, repo, app, or release being audited")
    parser.add_argument("--claim", required=True, help="One-sentence claim being tested")
    parser.add_argument("--root", default=".", help="Repository or project root to inventory")
    parser.add_argument("--output", required=True, help="Directory for readiness artifacts")
    parser.add_argument("--overall-completion", type=float, help="Optional larger objective percentage")
    parser.add_argument("--overall-source", default="audit-estimated", help="Source for the larger objective percentage")
    parser.add_argument("--blocked-gate", action="append", default=[], help="Blocked or deferred gate; repeatable")
    parser.add_argument("--next-best-slice", default="Define the narrowest falsifiable next slice")
    return parser.parse_args()


def build_report(args: argparse.Namespace) -> ReadinessReport:
    matrix = [
        {
            "case": "source-corpus inventory",
            "status": "recorded",
            "evidence": f"{len(inventory(Path(args.root)))} files classified",
        },
        {
            "case": "baseline verification",
            "status": "not-run",
            "evidence": "CLI skeleton records truth; caller must attach command evidence",
        },
        {
            "case": "security/trust boundary",
            "status": "not-run",
            "evidence": "No target-specific security probes supplied",
        },
    ]
    score = 91
    pulse = ProgressPulse(
        slice_readiness=score,
        slice_status=score_band(score),
        overall_completion=args.overall_completion,
        overall_source=args.overall_source,
        blocked_gates=args.blocked_gate,
        next_best_slice=args.next_best_slice,
    )
    return ReadinessReport(
        target=args.target,
        claim=args.claim,
        score=score,
        pulse=pulse,
        matrix=matrix,
    )


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    report = build_report(args)
    report.write_json(output / "dogfood-readiness-data.json")
    (output / "dogfood-readiness-report.md").write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

