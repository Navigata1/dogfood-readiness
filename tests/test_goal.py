import tempfile
import unittest
from pathlib import Path

from dogfood_readiness import goal as g


class GoalLedgerTests(unittest.TestCase):
    def _ten_slice_goal(self):
        return g.init_goal(
            "garnet-s31-s40",
            "Foundation + Compatibility",
            [(f"s{n}", f"slice {n}", 1.0) for n in range(31, 41)],
        )

    def test_init_requires_slices(self):
        with self.assertRaises(ValueError):
            g.init_goal("empty", "Empty", [])

    def test_completion_tracks_slice_of_n(self):
        state = self._ten_slice_goal()
        self.assertEqual(g.completion(state), 0.0)
        self.assertEqual(g.position(state), "slice 0 of 10 merged")
        state = g.advance_goal(state, "s31", confidence=5)
        self.assertEqual(g.completion(state), 10.0)
        self.assertEqual(g.position(state), "slice 1 of 10 merged")
        self.assertTrue(g.next_slice(state).startswith("s32:"))

    def test_advance_below_threshold_is_refused(self):
        state = self._ten_slice_goal()
        with self.assertRaises(ValueError):
            g.advance_goal(state, "s31", confidence=3, threshold=5)

    def test_advance_unknown_slice_is_refused(self):
        state = self._ten_slice_goal()
        with self.assertRaises(ValueError):
            g.advance_goal(state, "s99", confidence=5)

    def test_weighted_completion(self):
        state = g.init_goal("w", "Weighted", [("a", "a", 3.0), ("b", "b", 1.0)])
        state = g.advance_goal(state, "a", confidence=5)
        self.assertEqual(g.completion(state), 75.0)

    def test_roundtrip_persistence_is_deterministic(self):
        state = self._ten_slice_goal()
        state = g.advance_goal(state, "s31", confidence=5)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".dogfood" / "goal.json"
            g.save_goal(state, path)
            reloaded = g.load_goal(path)
        self.assertEqual(g.completion(reloaded), 10.0)
        self.assertEqual(reloaded.goal_id, "garnet-s31-s40")
        self.assertEqual(reloaded.slices[0].status, "merged")
        self.assertEqual(reloaded.slices[0].merge_confidence, 5)


if __name__ == "__main__":
    unittest.main()
