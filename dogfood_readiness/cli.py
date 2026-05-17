"""Command-line interface for dogfood readiness."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .inventory import inventory
from .model import Finding, MutationEvent, ProgressPulse, ReadinessReport
from .render import render_markdown
from .score import readiness_score, score_band


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="PR, feature, repo, app, or release being audited")
    parser.add_argument("--claim", required=True, help="One-sentence claim being tested")
    parser.add_argument("--root", default=".", help="Repository or project root to inventory")
    parser.add_argument("--output", required=True, help="Directory for readiness artifacts")
    parser.add_argument("--overall-completion", type=float, help="Optional larger objective percentage")
    parser.add_argument(
        "--overall-source",
        default="audit-estimated",
        help="Source for the larger objective percentage",
    )
    parser.add_argument(
        "--blocked-gate",
        action="append",
        default=[],
        help="Blocked or deferred gate; repeatable",
    )
    parser.add_argument(
        "--next-best-slice",
        default="Define the narrowest falsifiable next slice",
        help="Next best concrete slice recommendation",
    )
    parser.add_argument("--findings", type=Path, help="Optional JSON file with finding list")
    parser.add_argument("--missed-checker-failures", type=int, default=0)
    parser.add_argument("--blocked-core-cases", type=int, default=0)
    parser.add_argument("--unverified-core-claims", type=int, default=0)
    parser.add_argument("--corpus-coverage-gaps", type=int, default=0)
    parser.add_argument("--security-coverage-gaps", type=int, default=0)
    parser.add_argument(
        "--unreviewed-high-risk-trust-boundaries",
        type=int,
        default=0,
    )
    return parser.parse_args(argv)


def _load_findings(path: Path | None) -> list[Finding]:
    if path is None:
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("--findings must be a JSON array")

    findings: list[Finding] = []
    for index, payload in enumerate(raw):
        if not isinstance(payload, dict):
            raise ValueError(f"finding at index {index} must be object")
        finding = Finding(
            id=str(payload.get("id", f"F{index+1}")),
            title=str(payload.get("title", "Unnamed finding")),
            severity=str(payload.get("severity", "low")),
            status=str(payload.get("status", "unknown")),
            claim_tested=str(payload.get("claim_tested", "")),
            evidence=str(payload.get("evidence", "")),
            expected=str(payload.get("expected", "")),
            actual=str(payload.get("actual", "")),
            impact=str(payload.get("impact", "")),
            recommendation=str(payload.get("recommendation", "")),
            security_domain=str(payload.get("security_domain", "not-applicable")),
        )
        findings.append(finding)
    return findings


def _build_matrix(args: argparse.Namespace, findings: list[Finding], root: Path) -> list[dict[str, str]]:
    matrix = [
        {
            "case": "source-corpus inventory",
            "status": "recorded",
            "evidence": f"{len(inventory(root))} files classified",
        },
        {
            "case": "baseline verification",
            "status": "not-run",
            "evidence": "Attach command-level output in the artifact bundle before marking complete",
        },
        {
            "case": "security/trust boundary",
            "status": "not-run",
            "evidence": "Attach security review artifacts for claim-specific boundaries",
        },
    ]

    for finding in findings:
        matrix.append(
            {
                "case": f"{finding.id}: {finding.title}",
                "status": finding.status,
                "evidence": finding.evidence,
            }
        )

    if not matrix:
        matrix.append(
            {
                "case": "No claims attached",
                "status": "recorded",
                "evidence": "No explicit finding records were supplied for this report.",
            }
        )

    return matrix


def _build_mutation_log(args: argparse.Namespace, findings: list[Finding], score: int) -> list[MutationEvent]:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    details = (
        f"findings={len(findings)}; score={score}; "
        f"blocked_gates={','.join(args.blocked_gate)}; next='{args.next_best_slice}'"
    )
    return [MutationEvent(timestamp=timestamp, event="dogfood-report-built", command=" ".join(_argv(args)), details=details)]


def _argv(args: argparse.Namespace) -> list[str]:
    return [
        "dogfood-readiness",
        "--target",
        args.target,
        "--claim",
        args.claim,
        "--root",
        args.root,
        "--output",
        args.output,
    ]


def build_report(args: argparse.Namespace) -> ReadinessReport:
    root = Path(args.root).resolve()
    findings = _load_findings(args.findings)
    score = readiness_score(
        findings,
        missed_checker_failures=args.missed_checker_failures,
        blocked_core_cases=args.blocked_core_cases,
        unverified_core_claims=args.unverified_core_claims,
        corpus_coverage_gaps=args.corpus_coverage_gaps,
        security_coverage_gaps=args.security_coverage_gaps,
        unreviewed_high_risk_trust_boundaries=args.unreviewed_high_risk_trust_boundaries,
    )
    matrix = _build_matrix(args, findings, root)
    pulse = ProgressPulse(
        slice_readiness=score,
        slice_status=score_band(score),
        overall_completion=args.overall_completion,
        overall_source=args.overall_source,
        blocked_gates=args.blocked_gate,
        next_best_slice=args.next_best_slice,
    )
    mutation_log = _build_mutation_log(args, findings, score)
    return ReadinessReport(
        target=args.target,
        claim=args.claim,
        score=score,
        pulse=pulse,
        findings=findings,
        matrix=matrix,
        mutation_log=mutation_log,
    )


def write_bundle(report: ReadinessReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report.write_json(output_dir / "dogfood-readiness-data.json")
    (output_dir / "dogfood-readiness-report.md").write_text(render_markdown(report), encoding="utf-8")
    mutation_log = "\n".join(
        [
            f"- {event.timestamp} {event.event}: {event.command} :: {event.details}"
            for event in report.mutation_log
        ]
    )
    (output_dir / "dogfood-readiness-mutation-log.md").write_text(
        f"# Mutation Log\n\n{mutation_log or '- No mutations'}\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    try:
        report = build_report(args)
    except (ValueError, OSError) as exc:
        print(f"dogfood-readiness: {exc}")
        return 2

    write_bundle(report, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
