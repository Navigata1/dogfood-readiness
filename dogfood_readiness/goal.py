"""Goal-mode ledger.

The fusion function's purpose: during a long-running ``/goal`` run that posts and
merges many slices, report where you are against the *whole* goal. If you are on
slice 1 of 10, overall completion is 10% -- computed from a persisted ledger, not
typed in by hand.

A goal is an ordered list of slices with weights (default 1.0). Overall completion
is merged-weight / total-weight. Advancing a slice is gated on a merge-confidence
threshold so a slice only counts once it has actually earned its stamp.

This module is dependency-free and writes a deterministic, committable JSON ledger.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .model import GoalSlice, GoalState


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_goal(goal_id: str, title: str, slices: list[tuple[str, str, float]]) -> GoalState:
    """Build a fresh goal ledger from ``(id, title, weight)`` tuples (ordered)."""

    if not slices:
        raise ValueError("a goal needs at least one slice")
    built = [GoalSlice(id=s_id, title=s_title, weight=float(weight)) for s_id, s_title, weight in slices]
    return GoalState(goal_id=goal_id, title=title, slices=built)


def load_goal(path: Path) -> GoalState:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    slices = [
        GoalSlice(
            id=str(s["id"]),
            title=str(s.get("title", "")),
            weight=float(s.get("weight", 1.0)),
            status=str(s.get("status", "pending")),
            merged_at=s.get("merged_at"),
            merge_confidence=s.get("merge_confidence"),
        )
        for s in raw.get("slices", [])
    ]
    return GoalState(
        goal_id=str(raw["goal_id"]),
        title=str(raw.get("title", "")),
        slices=slices,
        created_at=str(raw.get("created_at", _now())),
    )


def save_goal(state: GoalState, path: Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def advance_goal(
    state: GoalState,
    slice_id: str,
    *,
    confidence: int | None = None,
    threshold: int = 5,
) -> GoalState:
    """Mark a slice merged. Refuses unless ``confidence >= threshold``.

    Returns a NEW GoalState (the model is frozen/immutable).
    """

    if not any(s.id == slice_id for s in state.slices):
        raise ValueError(f"slice {slice_id!r} is not part of goal {state.goal_id!r}")
    if confidence is not None and confidence < threshold:
        raise ValueError(
            f"slice {slice_id!r} confidence {confidence} is below merge threshold {threshold}; "
            f"run the grep loop until it reaches {threshold}/5"
        )
    new_slices = [
        replace(s, status="merged", merged_at=_now(), merge_confidence=confidence)
        if s.id == slice_id
        else s
        for s in state.slices
    ]
    return replace(state, slices=new_slices)


def completion(state: GoalState) -> float:
    """Overall completion percentage = merged weight / total weight."""

    total = sum(s.weight for s in state.slices)
    if total <= 0:
        return 0.0
    merged = sum(s.weight for s in state.slices if s.status == "merged")
    return round(merged / total * 100, 1)


def next_slice(state: GoalState) -> str:
    """First still-pending slice, as ``id: title``; sentinel if the goal is done."""

    for s in state.slices:
        if s.status != "merged":
            return f"{s.id}: {s.title}"
    return "goal complete -- all slices merged"


def position(state: GoalState) -> str:
    """Human 'slice k of N' string."""

    merged = sum(1 for s in state.slices if s.status == "merged")
    return f"slice {merged} of {len(state.slices)} merged"
