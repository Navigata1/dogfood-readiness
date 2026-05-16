# No-Mistakes Fusion

`dogfood-readiness` complements push-gate tools such as `no-mistakes`.

The fusion is conceptual and procedural:

- Use a gate before PR merge.
- Require deterministic evidence in the PR body.
- Separate local verification from remote verification.
- Preserve the source of truth in durable artifacts.
- Keep the human in charge of irreversible actions.

This repository does not copy `no-mistakes` implementation code. It provides a portable readiness layer that can be called from a no-mistakes-style pipeline, a GitHub Action, an agent run, or a local terminal.

