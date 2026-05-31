"""Command-line interface for dogfood readiness."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .goal import advance_goal, completion, init_goal, load_goal, next_slice, position, save_goal
from .inventory import inventory
from .model import Finding, MutationEvent, ProgressPulse, ReadinessReport
from .render import render_markdown
from .score import fuse_merge_confidence, merge_confidence_band, readiness_score, score_band

DEFAULT_NEXT_SLICE = "Define the narrowest falsifiable next slice"
DEFAULT_OVERALL_SOURCE = "audit-estimated"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    # Report mode (default). Not required at parse time so goal-mode actions can run
    # without them; enforced in main() for the report path.
    parser.add_argument("--target", help="PR, feature, repo, app, or release being audited")
    parser.add_argument("--claim", help="One-sentence claim being tested")
    parser.add_argument("--root", default=".", help="Repository or project root to inventory")
    parser.add_argument("--output", help="Directory for readiness artifacts")
    parser.add_argument("--overall-completion", type=float, help="Optional larger objective percentage")
    parser.add_argument(
        "--overall-source",
        default=DEFAULT_OVERALL_SOURCE,
        help="Source for the larger objective percentage",
    )
    parser.add_argument("--blocked-gate", action="append", default=[], help="Blocked or deferred gate; repeatable")
    parser.add_argument("--next-best-slice", default=DEFAULT_NEXT_SLICE, help="Next best concrete slice recommendation")
    parser.add_argument("--findings", type=Path, help="Optional JSON file with finding list")
    parser.add_argument("--missed-checker-failures", type=int, default=0)
    parser.add_argument("--blocked-core-cases", type=int, default=0)
    parser.add_argument("--unverified-core-claims", type=int, default=0)
    parser.add_argument("--corpus-coverage-gaps", type=int, default=0)
    parser.add_argument("--security-coverage-gaps", type=int, default=0)
    parser.add_argument("--unreviewed-high-risk-trust-boundaries", type=int, default=0)

    # Merge-confidence fusion (the "grep loop" / Greptile 5-of-5 signal).
    parser.add_argument(
        "--external-review-score",
        type=int,
        help="External reviewer merge confidence, 1..5 (e.g. Greptile, or a capability-diff signal)",
    )
    parser.add_argument("--external-review-source", default="external", help="Name of the external reviewer")
    parser.add_argument(
        "--fusion-mode",
        choices=("min", "weighted"),
        default="min",
        help="How to fuse internal and external confidence (min governs a merge gate)",
    )

    # Goal-mode ledger.
    parser.add_argument(
        "--goal-action",
        choices=("init", "advance", "status"),
        help="Manage the goal ledger instead of building a report",
    )
    parser.add_argument("--goal-file", type=Path, help="Path to the persisted goal ledger JSON")
    parser.add_argument("--goal-id", help="Goal id (for --goal-action init)")
    parser.add_argument("--goal-title", default="", help="Goal title (for --goal-action init)")
    parser.add_argument(
        "--goal-slice",
        action="append",
        default=[],
        help="Goal slice as 'id:title[:weight]'; repeatable (for --goal-action init)",
    )
    parser.add_argument("--advance-slice", help="Slice id to mark merged (for --goal-action advance)")
    parser.add_argument("--advance-confidence", type=int, help="Earned 1..5 merge confidence for the advancing slice")
    parser.add_argument("--merge-threshold", type=int, default=5, help="Minimum confidence to merge a slice")
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
        args.target or "",
        "--claim",
        args.claim or "",
        "--root",
        args.root,
        "--output",
        args.output or "",
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

    # Fuse merge confidence: internal band (from score) + optional external reviewer.
    internal_band = merge_confidence_band(score)
    fused = fuse_merge_confidence(internal_band, args.external_review_score, mode=args.fusion_mode)
    if args.external_review_score is None:
        confidence_source = "internal"
    else:
        confidence_source = f"internal-{args.fusion_mode}-{args.external_review_source}"

    # Goal-mode: if a ledger is supplied, compute overall completion from it
    # (the source of truth) rather than a hand-typed percentage.
    overall_completion = args.overall_completion
    overall_source = args.overall_source
    next_best = args.next_best_slice
    if args.goal_file is not None and Path(args.goal_file).exists():
        goal = load_goal(args.goal_file)
        if overall_completion is None:
            overall_completion = completion(goal)
            overall_source = "goal-tracked"
        if next_best == DEFAULT_NEXT_SLICE:
            next_best = next_slice(goal)

    pulse = ProgressPulse(
        slice_readiness=score,
        slice_status=score_band(score),
        overall_completion=overall_completion,
        overall_source=overall_source,
        blocked_gates=args.blocked_gate,
        next_best_slice=next_best,
        merge_confidence=fused,
        merge_confidence_source=confidence_source,
    )
    mutation_log = _build_mutation_log(args, findings, score)
    return ReadinessReport(
        target=args.target or "unspecified-target",
        claim=args.claim or "unspecified-claim",
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


def _parse_goal_slices(specs: list[str]) -> list[tuple[str, str, float]]:
    out: list[tuple[str, str, float]] = []
    for spec in specs:
        parts = spec.split(":")
        if len(parts) < 2:
            raise ValueError(f"goal slice {spec!r} must be 'id:title[:weight]'")
        s_id, s_title = parts[0], parts[1]
        weight = float(parts[2]) if len(parts) >= 3 and parts[2] else 1.0
        out.append((s_id, s_title, weight))
    return out


def _run_goal_action(args: argparse.Namespace) -> int:
    if args.goal_file is None:
        print("dogfood-readiness: --goal-file is required for --goal-action")
        return 2

    try:
        if args.goal_action == "init":
            if not args.goal_id or not args.goal_slice:
                print("dogfood-readiness: --goal-id and at least one --goal-slice are required for init")
                return 2
            state = init_goal(args.goal_id, args.goal_title or args.goal_id, _parse_goal_slices(args.goal_slice))
            save_goal(state, args.goal_file)
        elif args.goal_action == "advance":
            if not args.advance_slice:
                print("dogfood-readiness: --advance-slice is required for advance")
                return 2
            state = load_goal(args.goal_file)
            confidence = args.advance_confidence if args.advance_confidence is not None else args.external_review_score
            state = advance_goal(state, args.advance_slice, confidence=confidence, threshold=args.merge_threshold)
            save_goal(state, args.goal_file)
        else:  # status
            state = load_goal(args.goal_file)
    except (ValueError, OSError, KeyError) as exc:
        print(f"dogfood-readiness: {exc}")
        return 2

    print(
        f"goal {state.goal_id}: {completion(state):.1f}% ({position(state)}) | next: {next_slice(state)}"
    )
    return 0


def main() -> int:
    args = parse_args()

    if args.goal_action:
        try:
            return _run_goal_action(args)
        except (ValueError, OSError, KeyError) as exc:
            print(f"dogfood-readiness: {exc}")
            return 2

    if not args.target or not args.claim or not args.output:
        print("dogfood-readiness: --target, --claim, and --output are required for a report")
        return 2

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
