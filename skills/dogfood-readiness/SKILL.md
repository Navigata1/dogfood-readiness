---
name: dogfood-readiness
description: Use when reviewing a PR, issue, feature, app, language, release, or agentic/goal-mode run where green checks may be misleading and an evidence-backed merge decision is needed. Fuses your own falsification findings with external reviewer confidence (e.g. Greptile) into a single 1-5 merge-confidence band, runs a grep loop to 5/5, and tracks overall goal progress.
---

# Dogfood Readiness

Dogfood readiness is a falsification audit and an **evidence ledger** — not a courtesy review, and **not a second code reviewer**.

It does not replace an AI reviewer such as Greptile. It **consumes** the reviewer's signal as one input, fuses it with your own falsification findings and verification evidence into one deterministic, committed artifact, expresses that as a 1-5 merge-confidence band, and gates merge on a grep loop to 5/5 — while tracking where a long-running goal run actually is.

Green tests are evidence, not proof. Every claim must be tied to a command, file path, observed output, diff, reproducible probe, direct source inspection, or explicitly marked unverified.

## Division Of Labor (why this is not redundant with Greptile)

- **An external reviewer (Greptile, etc.)** reads the diff and answers "does this change look correct/safe?" → emits a 1-5 confidence. That is its job; do not re-implement it.
- **A capability/authority diff (on a Garnet-style project)** answers "what authority changed?" → also a reviewable signal.
- **dogfood-readiness** is the ledger that (a) resolves current truth, (b) runs falsification probes the reviewer does not, (c) records deterministic evidence artifacts, (d) **fuses** the reviewer's confidence with its own score, and (e) reports goal progress. No external reviewer produces this artifact.

Treat the external reviewer as an evidence **source**. This skill is the **fuser, the loop, and the ledger**.

## Merge Confidence Fusion

Map the 0-100 readiness score to a 1-5 band (`merge_confidence_band`): blocked=1, risky=2, partial=3, ready-with-caveats=4, ready=5. A **5/5 stamp == the top band (score >= 95)**.

Fuse with the external reviewer's 1-5 score (`fuse_merge_confidence`):

- **Gate (default): `min`.** The weakest signal governs. Never merge on a high reviewer score while falsification findings are low — or vice versa.
- **Report only: `weighted`** (0.6 internal / 0.4 external), never for the gate.

```
python3 -m dogfood_readiness \
  --target "PR 123" --claim "..." --output .dogfood/readiness \
  --external-review-score 4 --external-review-source greptile --fusion-mode min
```

The pulse then carries `merge_confidence` and `merge_confidence_source` (e.g. `internal-min-greptile`).

## The Grep Loop (merge confidence to 5/5)

Borrowed from Greptile's grep-loop idea, generalized to the fused signal:

1. Audit the slice; compute fused merge confidence.
2. If `< 5`: address the finding (or evidence gap) costing the most points — re-run the highest-severity probe, attach the missing verification, or get the authority change reviewed.
3. Re-audit. Repeat until fused confidence is `5/5`.
4. Merge only at `5/5`, or have the **human** explicitly defer with a recorded reason. Auto-fix/push/merge only when the task grants that authority and remote checks are green.

The loop converges the *fused* score, so it cannot be satisfied by a confident reviewer alone — the falsification ledger has to agree.

## Goal Mode (where am I in a long run?)

During a `/goal` run that posts and merges many slices, overall completion is computed from a **persisted ledger**, not typed by hand. On slice 1 of 10, overall completion is 10%.

```
# define the goal once (ordered slices, optional :weight)
python3 -m dogfood_readiness --goal-action init --goal-file .dogfood/goal.json \
  --goal-id g1 --goal-title "Phase A" --goal-slice s31:reporter --goal-slice s32:fusion ...

# advance only when the slice earned its stamp (refused below threshold)
python3 -m dogfood_readiness --goal-action advance --goal-file .dogfood/goal.json \
  --advance-slice s31 --advance-confidence 5

# status: overall %, slice k of N, next best slice
python3 -m dogfood_readiness --goal-action status --goal-file .dogfood/goal.json
```

A report run given `--goal-file` auto-fills overall completion from the ledger and labels the source `goal-tracked`. Keep slice readiness separate from overall objective completion — never blend the two numbers.

## Progress Pulse

For long-running work, emit a short pulse after each checkpoint:

- slice readiness score (and merge-confidence band)
- overall objective completion (`goal-tracked` if a ledger exists; else `repo-reported` from a native reporter; else an explicit `audit-estimated` value with its calculation)
- blocked/deferred gates
- next best slice

## Audit Workflow

1. Resolve target and success claim.
2. Verify provenance: repo root, branch, remotes, head SHA, dirty state, open PRs.
3. Inventory the source corpus before judging completeness.
4. Extract claims from PR body, README, docs, specs, release notes, examples, handoffs.
5. Reproduce baseline verification.
6. Run falsification probes: bad inputs, missing files, broken links, wrong commands, stale examples, permission failures, cross-platform assumptions, malformed workflows.
7. Dogfood behavior as the intended user, maintainer, developer, agent, or downstream app.
8. Add a security/trust-boundary row group; record any unreviewed high-risk boundary or capability/authority change (these subtract from the score and block 5/5).
9. Reconcile implementation against specs and marketing claims.
10. Score readiness; map to a merge-confidence band; fuse with the external reviewer; run the grep loop.
11. Produce artifacts: Markdown report, JSON data, readiness matrix, mutation log, PR evidence body, and (if in goal mode) the updated goal ledger.

## Score Formula

```text
readiness = max(
  0,
  100
  - critical_findings * 25
  - high_findings * 12
  - medium_findings * 5
  - low_findings * 1
  - missed_checker_failures * 4
  - blocked_core_cases * 3
  - unverified_core_claims * 3
  - corpus_coverage_gaps * 2
  - security_coverage_gaps * 3
  - unreviewed_high_risk_trust_boundaries * 4
)
```

## No-Mistakes Fusion

Borrow the no-mistakes stance:

- PRs should be clean sources of truth.
- Evidence should be deterministic and attached before merge.
- The human stays in charge of irreversible actions.
- Auto-fix, push, and merge are allowed only when the task explicitly grants that authority and remote checks are green.

Do not claim that this skill has run `no-mistakes`, Greptile, or any external reviewer unless that tool actually ran. Record the external score's provenance; do not invent it.
