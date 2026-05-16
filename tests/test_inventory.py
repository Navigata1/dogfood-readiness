import tempfile
import unittest
from pathlib import Path

from dogfood_readiness.inventory import classify_path, inventory


class InventoryTests(unittest.TestCase):
    def test_classify_path_identifies_common_project_surfaces(self):
        self.assertEqual(classify_path(Path("README.md")), "project-contract")
        self.assertEqual(classify_path(Path(".github/workflows/ci.yml")), "ci-release")
        self.assertEqual(classify_path(Path("tests/test_app.py")), "test-evidence")
        self.assertEqual(classify_path(Path("src/app.py")), "implementation")
        self.assertEqual(classify_path(Path("docs/guide.md")), "documentation")

    def test_inventory_is_bounded_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("hello", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")

            self.assertEqual(
                inventory(root),
                [
                    {"kind": "project-contract", "path": "README.md"},
                    {"kind": "implementation", "path": "src/app.py"},
                ],
            )


if __name__ == "__main__":
    unittest.main()
