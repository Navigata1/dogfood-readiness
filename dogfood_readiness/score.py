"""Readiness scoring formula."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .model import Finding


WEIGHTS = {
    "critical": 25,
    "high": 12,
    "medium": 5,
    "low": 1,
}


def readiness_score(
    findings: Iterable[Finding],
    *,
    missed_checker_failures: int = 0,
    blocked_core_cases: int = 0,
    unverified_core_claims: int = 0,
    corpus_coverage_gaps: int = 0,
    security_coverage_gaps: int = 0,
    unreviewed_high_risk_trust_boundaries: int = 0,
) -> int:
    """Return a transparent 0-100 readiness score."""

    counts = Counter(finding.severity.lower() for finding in findings)
    score = 100
    for severity, weight in WEIGHTS.items():
        score -= counts[severity] * weight

    score -= missed_checker_failures * 4
    score -= blocked_core_cases * 3
    score -= unverified_core_claims * 3
    score -= corpus_coverage_gaps * 2
    score -= security_coverage_gaps * 3
    score -= unreviewed_high_risk_trust_boundaries * 4
    return max(0, min(100, score))


def score_band(score: int) -> str:
    """Classify a readiness score for human reports."""

    if score >= 95:
        return "ready"
    if score >= 85:
        return "ready-with-caveats"
    if score >= 70:
        return "partial"
    if score >= 50:
        return "risky"
    return "blocked"

