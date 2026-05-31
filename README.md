# Dogfood Readiness

Evidence-first readiness auditing for pull requests, product slices, apps, tools, programming languages, and agentic build systems.

`dogfood-readiness` is the portable version of the Garnet readiness gate: it treats green tests as evidence, not proof. It is an **evidence ledger and merge-confidence fuser**, not a code reviewer. It combines falsification-oriented dogfooding, no-mistakes-style PR hygiene, explicit progress percentages, reusable evidence artifacts, a 1-5 merge-confidence band that **fuses an external reviewer's score** (e.g. Greptile's grep-loop signal) with its own findings, and a goal-mode ledger that reports where a long-running run actually is.

## What It Does

- Resolves current truth before judging a PR, feature, repo, or release.
- Builds a source-corpus map so specs, implementation, examples, generated files, and handoffs are not confused.
- Extracts claims and asks what would falsify them.
- Runs or records baseline verification.
- Scores readiness with a transparent formula.
- Emits a progress pulse: slice readiness, overall objective completion, blockers, and next best slice.
- Produces Markdown, JSON, matrix, mutation-log, and PR-body evidence artifacts.
- Provides a reusable skill prompt for Codex, Claude Code, and other agent workflows.

`dogfood-readiness` difference is Greptile is a reviewer: it reads a diff and emits a confidence number. dogfood-readiness is not a reviewer and shouldn't try to be one — that's where redundancy would creep in. Its real job is to be the evidence ledger and confidence fuser: it consumes review signals (Greptile's 5/5, and on the Garnet side, diff-caps) as inputs, fuses them with falsification findings and verification evidence into one deterministic, committed score, expresses that as a 1–5 merge-confidence band, and runs the grep-loop — iterate until 5/5 — before merge. Greptile tells you "this PR looks right." dogfood-readiness tells you "here is the committed evidence that it's right, here is the fused confidence across every signal, and here is where this slice sits in a 10-slice goal." No external reviewer produces that artifact. So they compose; they don't collide.  

## Quick Start

Run a local readiness report from any repository:

```sh
python3 -m dogfood_readiness \
  --target "current branch" \
  --claim "This change is ready for PR review" \
  --output .dogfood/readiness
```

Attach falsification findings and evidence gaps as a JSON manifest:

```sh
python3 -m dogfood_readiness \
  --target "PR 999" \
  --claim "Converter import path is safe" \
  --findings .dogfood/findings.json \
  --missed-checker-failures 2 \
  --blocked-core-cases 1 \
  --overall-completion 58.6 \
  --blocked-gate "notarization" \
  --overall-source "audit-estimated" \
  --next-best-slice "close converter evidence gap" \
  --output .dogfood/readiness
```

Artifacts:

- `dogfood-readiness-report.md`
- `dogfood-readiness-data.json`
- `dogfood-readiness-mutation-log.md`

Validate a PR body against the evidence template:

```sh
python3 scripts/check_pr_body.py --body-file /tmp/pr-body.md
```

Check repo-owned GitHub workflow action pins before they become runtime drift:

```sh
python3 scripts/check_github_actions_node24.py
```

Install the skill by copying `skills/dogfood-readiness` into your agent skill folder.

## No-Mistakes Fusion

This repo does not vendor or reimplement `no-mistakes`. It borrows the operating idea:

- PRs should carry deterministic evidence.
- A gate should run before merge, not after regret.
- The human remains in charge, but the evidence should be structured enough that agents cannot hand-wave.

Proof updates are intentionally scoped to this repo only; portable consumers should still keep their own project-local truth and blocker maps in the target evidence bundle.

Where `no-mistakes` acts as a push/PR gate, `dogfood-readiness` acts as the evidence and readiness layer that can be used inside any workflow, including no-mistakes-style pipelines.

## Progress Pulse

The progress pulse keeps local slice quality separate from the larger project goal:

```text
Slice readiness: 92/100, ready with caveats
Overall objective: 58.6%, repo-reported
Blocked gates: notarization, provider adapter, native backend
Next best slice: package the smallest missing evidence gate
```

If a project has a native status reporter, use it. If not, compute an `audit-estimated` percentage and label it honestly.

## Merge Confidence and the Grep Loop

The readiness score (0-100) maps to a 1-5 merge-confidence band — `blocked`=1 ... `ready`=5. A **5/5 stamp == the top band (score >= 95)**. An external reviewer's 1-5 score (e.g. Greptile) is fused in; for a merge **gate** the default `min` lets the weakest signal govern.

```
python3 -m dogfood_readiness \
  --target "PR 123" --claim "converter is safe" --output .dogfood/readiness \
  --external-review-score 4 --external-review-source greptile --fusion-mode min
```

The grep loop iterates the *fused* confidence to 5/5 before merge, so a confident reviewer alone cannot satisfy it — the falsification ledger must agree. This is why the toolkit complements Greptile rather than duplicating it: Greptile answers "does this look right?"; dogfood-readiness fuses that with deterministic evidence and gates the merge.

## Goal Mode

During a long `/goal` run, overall completion is computed from a persisted ledger, not typed by hand. On slice 1 of 10, completion is 10%.

```
python3 -m dogfood_readiness --goal-action init --goal-file .dogfood/goal.json \
  --goal-id phase-a --goal-title "Phase A" --goal-slice s31:reporter --goal-slice s32:fusion

python3 -m dogfood_readiness --goal-action advance --goal-file .dogfood/goal.json \
  --advance-slice s31 --advance-confidence 5     # refused unless confidence >= threshold

python3 -m dogfood_readiness --goal-action status --goal-file .dogfood/goal.json
```

A report run given `--goal-file` auto-fills overall completion from the ledger and labels the source `goal-tracked`.

## Repository Layout

- `dogfood_readiness/`: dependency-free Python package and CLI.
- `skills/dogfood-readiness/`: reusable agent skill.
- `scripts/check_pr_body.py`: PR evidence gate.
- `scripts/check_github_actions_node24.py`: GitHub Actions Node 24 readiness gate for repo-owned workflows.
- `templates/pr-body.md`: PR body template.
- `.github/workflows/dogfood-readiness.yml`: optional CI gate.
- `examples/garnet-phase6ax.json`: example progress pulse data.

## Boundaries

- This tool does not replace real tests, CI, security review, release signing, or human judgment.
- It does not claim a project is production-ready merely because a score is high.
- It can record external blockers, but it should not pretend to solve account-holder, legal, credential, or hardware-only gates.
