import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_github_actions_node24.py"
SPEC = importlib.util.spec_from_file_location("check_github_actions_node24", SCRIPT_PATH)
assert SPEC and SPEC.loader
node24 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(node24)


class GithubActionsNode24Tests(unittest.TestCase):
    def test_current_repo_workflows_are_node24_ready(self):
        errors = node24.validate_workflows(Path(__file__).resolve().parents[1])

        self.assertEqual([], errors)

    def test_old_first_party_actions_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow = root / ".github" / "workflows" / "ci.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "\n".join(
                    [
                        "name: stale",
                        "jobs:",
                        "  test:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - uses: actions/checkout@v4",
                        "      - uses: actions/setup-python@v5",
                    ]
                ),
                encoding="utf-8",
            )

            errors = node24.validate_workflows(root)

        self.assertIn(".github/workflows/ci.yml:6 uses actions/checkout@v4; expected v6+", errors)
        self.assertIn(".github/workflows/ci.yml:7 uses actions/setup-python@v5; expected v6+", errors)

    def test_explicit_node20_runtime_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow = root / ".github" / "workflows" / "ci.yaml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "\n".join(
                    [
                        "name: stale-runtime",
                        "jobs:",
                        "  test:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: echo node20",
                    ]
                ),
                encoding="utf-8",
            )

            errors = node24.validate_workflows(root)

        self.assertIn(".github/workflows/ci.yaml:6 references node20 explicitly", errors)


if __name__ == "__main__":
    unittest.main()
