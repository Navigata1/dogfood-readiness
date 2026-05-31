import tempfile
import unittest
from pathlib import Path

from dogfood_readiness.cli import build_report, parse_args, _run_goal_action


class CliGoalModeTests(unittest.TestCase):
    def test_goal_init_advance_status_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            goal_file = Path(tmp) / ".dogfood" / "goal.json"
            init = parse_args([
                "--goal-action", "init",
                "--goal-file", str(goal_file),
                "--goal-id", "demo",
                "--goal-title", "Demo goal",
                "--goal-slice", "s1:first",
                "--goal-slice", "s2:second",
                "--goal-slice", "s3:third",
            ])
            self.assertEqual(_run_goal_action(init), 0)
            self.assertTrue(goal_file.exists())

            advance = parse_args([
                "--goal-action", "advance",
                "--goal-file", str(goal_file),
                "--advance-slice", "s1",
                "--advance-confidence", "5",
            ])
            self.assertEqual(_run_goal_action(advance), 0)

            # report reads the ledger and computes overall completion
            report = build_report(parse_args([
                "--target", "demo-pr",
                "--claim", "slice 1 ready",
                "--output", str(Path(tmp) / "out"),
                "--goal-file", str(goal_file),
            ]))
        self.assertAlmostEqual(report.pulse.overall_completion, 33.3, places=1)
        self.assertEqual(report.pulse.overall_source, "goal-tracked")
        self.assertTrue(report.pulse.next_best_slice.startswith("s2:"))

    def test_advance_below_threshold_returns_error_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            goal_file = Path(tmp) / "goal.json"
            _run_goal_action(parse_args([
                "--goal-action", "init", "--goal-file", str(goal_file),
                "--goal-id", "g", "--goal-slice", "s1:first",
            ]))
            rc = _run_goal_action(parse_args([
                "--goal-action", "advance", "--goal-file", str(goal_file),
                "--advance-slice", "s1", "--advance-confidence", "3",
            ]))
        self.assertEqual(rc, 2)

    def test_external_review_fuses_into_merge_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            # clean slice (score 100 -> internal band 5) but external reviewer says 2
            report = build_report(parse_args([
                "--target", "pr", "--claim", "fusion",
                "--output", str(Path(tmp) / "out"),
                "--external-review-score", "2",
                "--external-review-source", "greptile",
            ]))
        self.assertEqual(report.pulse.merge_confidence, 2)  # min governs the gate
        self.assertEqual(report.pulse.merge_confidence_source, "internal-min-greptile")


if __name__ == "__main__":
    unittest.main()
