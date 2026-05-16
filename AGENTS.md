# AGENTS.md

This repo is a portable evidence/readiness toolkit.

## Rules

- Keep the package dependency-free unless a dependency is explicitly justified.
- Prefer deterministic outputs that can be committed or attached to PRs.
- Do not claim production readiness from a score alone.
- Keep Garnet-specific details in examples, not core logic.
- Run verification before claiming completion:
  - `python3 -m unittest discover -s tests`
  - `python3 -m dogfood_readiness --target "smoke" --claim "CLI renders artifacts" --output /tmp/dogfood-readiness-smoke`
  - `python3 scripts/check_pr_body.py --body-file templates/pr-body.md`

