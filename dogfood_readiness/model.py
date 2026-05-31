"""Data model for readiness reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    """A single falsification or readiness finding."""

    id: str
    title: str
    severity: str
    status: str
    claim_tested: str
    evidence: str
    expected: str
    actual: str
    impact: str
    recommendation: str
    security_domain: str = "not-applicable"


@dataclass(frozen=True)
class MutationEvent:
    """A deterministic mutation record for reproducibility auditing."""

    timestamp: str
    event: str
    command: str
    details: str


@dataclass(frozen=True)
class GoalSlice:
    """One slice in a goal-mode run.

    A goal is an ordered list of slices. Overall completion is the share of
    slice weight that has reached `merged` status, so a long-running /goal run
    can report where it is (slice k of N) instead of a hand-typed percentage.
    """

    id: str
    title: str
    weight: float = 1.0
    status: str = "pending"  # pending | merged
    merged_at: str | None = None
    merge_confidence: int | None = None  # 1..5 fused confidence at merge time


@dataclass(frozen=True)
class GoalState:
    """A persisted goal ledger. Immutable: advancing returns a new state."""

    goal_id: str
    title: str
    slices: list[GoalSlice] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProgressPulse:
    """High-level status that keeps slice and objective truth separate."""

    slice_readiness: int
    slice_status: str
    overall_completion: float | None
    overall_source: str
    blocked_gates: list[str]
    next_best_slice: str
    merge_confidence: int | None = None  # 1..5 fused merge-confidence band
    merge_confidence_source: str = "internal"  # e.g. "internal-min-greptile"


@dataclass(frozen=True)
class ReadinessReport:
    """A complete portable readiness report."""

    target: str
    claim: str
    score: int
    pulse: ProgressPulse
    findings: list[Finding] = field(default_factory=list)
    matrix: list[dict[str, str]] = field(default_factory=list)
    mutation_log: list[MutationEvent] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        import json

        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
