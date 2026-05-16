"""Render readiness reports."""

from __future__ import annotations

from .model import Finding, ReadinessReport


def render_markdown(report: ReadinessReport) -> str:
    """Render a report as portable Markdown."""

    findings = "\n".join(_render_finding(finding) for finding in report.findings)
    if not findings:
        findings = "- No findings recorded. Treat this as no findings observed, not proof of absence."

    matrix = "\n".join(
        f"| {row.get('case', '')} | {row.get('status', '')} | {row.get('evidence', '')} |"
        for row in report.matrix
    )
    if not matrix:
        matrix = "| Baseline | not-run | No matrix rows supplied. |"

    overall = (
        f"{report.pulse.overall_completion:.1f}%"
        if report.pulse.overall_completion is not None
        else "not available"
    )
    blockers = "\n".join(f"- {gate}" for gate in report.pulse.blocked_gates) or "- None recorded."

    return f"""# Dogfood Readiness Report

Generated: `{report.generated_at}`

Target: **{report.target}**

Claim tested: {report.claim}

## Progress Pulse

- Slice readiness: **{report.pulse.slice_readiness}/100** (`{report.pulse.slice_status}`)
- Overall objective completion: **{overall}** (`{report.pulse.overall_source}`)
- Next best slice: {report.pulse.next_best_slice}

Blocked/deferred gates:
{blockers}

## Findings

{findings}

## Readiness Matrix

| Case | Status | Evidence |
| --- | --- | --- |
{matrix}

## Boundary Note

This report is evidence, not proof. Passing scores do not replace tests, CI, security review, release signing, or human review.
"""


def _render_finding(finding: Finding) -> str:
    return (
        f"- **{finding.id} [{finding.severity}/{finding.status}] {finding.title}**: "
        f"{finding.impact} Evidence: `{finding.evidence}`. Recommendation: {finding.recommendation}"
    )

