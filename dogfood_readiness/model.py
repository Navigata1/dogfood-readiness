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
class ProgressPulse:
    """High-level status that keeps slice and objective truth separate."""

    slice_readiness: int
    slice_status: str
    overall_completion: float | None
    overall_source: str
    blocked_gates: list[str]
    next_best_slice: str


@dataclass(frozen=True)
class ReadinessReport:
    """A complete portable readiness report."""

    target: str
    claim: str
    score: int
    pulse: ProgressPulse
    findings: list[Finding] = field(default_factory=list)
    matrix: list[dict[str, str]] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        import json

        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

