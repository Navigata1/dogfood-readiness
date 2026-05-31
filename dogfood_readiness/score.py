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

# Maps the five readiness bands onto a 1..5 merge-confidence scale.
# This is the bridge to Greptile-style "N out of 5" merge confidence:
# a 5/5 stamp == the top band ("ready", score >= 95).
BAND_TO_CONFIDENCE = {
    "blocked": 1,
    "risky": 2,
    "partial": 3,
    "ready-with-caveats": 4,
    "ready": 5,
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


def merge_confidence_band(score: int) -> int:
    """Map a 0-100 readiness score to a 1..5 merge-confidence band.

    5 == top band ("ready"). This is the internal half of the merge-confidence
    signal; an external reviewer (e.g. Greptile) supplies the other half.
    """

    return BAND_TO_CONFIDENCE[score_band(score)]


def fuse_merge_confidence(
    internal_band: int,
    external_band: int | None = None,
    *,
    mode: str = "min",
) -> int:
    """Fuse the internal readiness band with an optional external reviewer band.

    `internal_band` comes from `merge_confidence_band`. `external_band` is a
    1..5 score from a reviewer such as Greptile (the "grep loop" target) or,
    on the Garnet side, a capability-diff acceptance signal.

    For a MERGE GATE the safe default is ``min`` -- the weakest signal governs,
    so you never merge on a high reviewer score while your own falsification
    findings are low (or vice versa). ``weighted`` is offered for non-gating
    reporting only.
    """

    if external_band is None:
        return _clamp_band(internal_band)
    internal_band = _clamp_band(internal_band)
    external_band = _clamp_band(external_band)
    if mode == "min":
        return min(internal_band, external_band)
    if mode == "weighted":
        return _clamp_band(round(0.6 * internal_band + 0.4 * external_band))
    raise ValueError(f"unknown fusion mode: {mode!r} (use 'min' or 'weighted')")


def _clamp_band(band: int) -> int:
    return max(1, min(5, int(band)))
