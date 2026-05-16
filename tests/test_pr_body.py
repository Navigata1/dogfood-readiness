import importlib.util
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_pr_body.py"
SPEC = importlib.util.spec_from_file_location("check_pr_body", SCRIPT_PATH)
assert SPEC and SPEC.loader
check_pr_body = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_pr_body)


VALID_BODY = """## Dogfood Readiness

### Current truth

- [x] Base verified.

### Local verification

- [x] Tests passed.

### Remote verification

- [ ] Pending.

### Evidence bundle

- [x] Bundle attached.

### Deferred / out of scope

- This does not claim production readiness.
"""


class PrBodyTests(unittest.TestCase):
    def test_valid_pr_body_passes(self):
        self.assertEqual(check_pr_body.validate(VALID_BODY), [])

    def test_missing_sections_fail(self):
        errors = check_pr_body.validate("## Dogfood Readiness\n")

        self.assertIn("missing required heading: ### Current truth", errors)

    def test_unqualified_production_ready_claim_fails(self):
        body = VALID_BODY + "\nThis is production ready.\n"

        self.assertIn("unqualified production-ready claim", check_pr_body.validate(body))


if __name__ == "__main__":
    unittest.main()
