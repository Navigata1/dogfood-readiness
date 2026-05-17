import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_github_actions_node24.py"
SPEC = importlib.util.spec_from_file_location("check_github_actions_node24", SCRIPT_PATH)
assert SPEC and SPEC.loader
check_github_actions_node24 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_github_actions_node24)


class GithubActionsNode24Tests(unittest.TestCase):
    def test_current_workflows_have_no_runtime_regressions(self):
        self.assertEqual(check_github_actions_node24.validate(), [])

    def test_old_first_party_action_major_is_rejected(self):
        text = "steps:\n  - uses: actions/checkout@v4\n"

        errors = check_github_actions_node24.validate_text(Path(".github/workflows/ci.yml"), text)

        self.assertEqual(
            errors,
            [".github/workflows/ci.yml pins actions/checkout@v4; expected v6+"],
        )

    def test_explicit_node20_variant_is_rejected(self):
        text = "steps:\n  - uses: example/action-node20@v1\n"

        errors = check_github_actions_node24.validate_text(Path(".github/workflows/ci.yml"), text)

        self.assertEqual(
            errors,
            [".github/workflows/ci.yml mentions node20 explicitly"],
        )


if __name__ == "__main__":
    unittest.main()
