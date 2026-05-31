import unittest

from dogfood_readiness.score import fuse_merge_confidence, merge_confidence_band


class MergeConfidenceTests(unittest.TestCase):
    def test_band_maps_scores_to_one_through_five(self):
        self.assertEqual(merge_confidence_band(96), 5)
        self.assertEqual(merge_confidence_band(90), 4)
        self.assertEqual(merge_confidence_band(75), 3)
        self.assertEqual(merge_confidence_band(55), 2)
        self.assertEqual(merge_confidence_band(40), 1)

    def test_fuse_without_external_returns_internal(self):
        self.assertEqual(fuse_merge_confidence(5), 5)
        self.assertEqual(fuse_merge_confidence(3), 3)

    def test_fuse_min_lets_weakest_signal_govern(self):
        self.assertEqual(fuse_merge_confidence(5, 2), 2)
        self.assertEqual(fuse_merge_confidence(2, 5), 2)
        self.assertEqual(fuse_merge_confidence(4, 4), 4)

    def test_fuse_weighted_blends(self):
        self.assertEqual(fuse_merge_confidence(5, 3, mode="weighted"), 4)
        self.assertEqual(fuse_merge_confidence(5, 5, mode="weighted"), 5)

    def test_fuse_clamps_and_rejects_unknown_mode(self):
        self.assertEqual(fuse_merge_confidence(9, 9), 5)
        self.assertEqual(fuse_merge_confidence(0, 0), 1)
        with self.assertRaises(ValueError):
            fuse_merge_confidence(5, 5, mode="bogus")


if __name__ == "__main__":
    unittest.main()
