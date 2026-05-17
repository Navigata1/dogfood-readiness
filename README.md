# Dogfood Readiness

Evidence-first readiness auditing for pull requests, product slices, apps, tools, programming languages, and agentic build systems.

`dogfood-readiness` is the portable version of the Garnet readiness gate: it treats green tests as evidence, not proof. It combines falsification-oriented dogfooding, no-mistakes-style PR hygiene, explicit progress percentages, and reusable evidence artifacts.

## What It Does

- Resolves current truth before judging a PR, feature, repo, or release.
- Builds a source-corpus map so specs, implementation, examples, generated files, and handoffs are not confused.
- Extracts claims and asks what would falsify them.
- Runs or records baseline verification.
- Scores readiness with a transparent formula.
- Emits a progress pulse: slice readiness, overall objective completion, blockers, and next best slice.
- Produces Markdown, JSON, matrix, mutation-log, and PR-body evidence artifacts.
- Provides a reusable skill prompt for Codex, Claude Code, and other agent workflows.

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
