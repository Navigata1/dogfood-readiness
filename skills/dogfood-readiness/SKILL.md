---
name: dogfood-readiness
description: Use when reviewing a PR, issue, feature idea, application, language, release, or agentic system where green checks may be misleading and an evidence-backed readiness decision is needed.
---

# Dogfood Readiness

Dogfood readiness is a falsification audit, not a courtesy review.

Green tests are evidence, not proof. Every claim must be tied to a command, file path, observed output, diff, reproducible probe, direct source inspection, or explicitly marked as unverified.

## Progress Pulse

For long-running work, emit a short pulse after each major checkpoint:

- slice readiness score
- overall objective completion
- blocked/deferred gates
- next best slice

If the target has a native reporter, use it. If not, compute an explicit `audit-estimated` percentage and say how it was calculated. Never mix local PR readiness with overall product completion.

## Audit Workflow

1. Resolve target and success claim.
2. Verify provenance: repo root, branch, remotes, head SHA, dirty state, open PRs.
3. Inventory the source corpus before judging completeness.
4. Extract claims from PR body, README, docs, specs, release notes, examples, and handoffs.
5. Reproduce baseline verification.
6. Run falsification probes: bad inputs, missing files, broken links, wrong commands, stale examples, permission failures, cross-platform assumptions, malformed workflows.
7. Dogfood behavior as the intended user, maintainer, developer, agent, or downstream app.
8. Add a security/trust-boundary row group.
9. Reconcile implementation against specs and marketing claims.
10. Score readiness with a transparent formula.
11. Produce artifacts: Markdown report, JSON data, readiness matrix, mutation log, PR evidence body, and optional deck.

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
- The human stays in charge.
- Auto-fix, push, and merge are allowed only when the task explicitly grants that authority and remote checks are green.

Do not claim that this skill has run `no-mistakes` unless that tool actually ran.

