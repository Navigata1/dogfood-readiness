import unittest

from dogfood_readiness.model import Finding
from dogfood_readiness.score import readiness_score, score_band


class ReadinessScoreTests(unittest.TestCase):
    def test_readiness_score_penalizes_severity_weights(self):
        findings = [
            Finding(
                id="F1",
                title="Critical issue",
                severity="critical",
                status="blocker",
                claim_tested="claim",
                evidence="evidence",
                expected="expected",
                actual="actual",
                impact="impact",
                recommendation="recommendation",
            ),
            Finding(
                id="F2",
                title="Medium issue",
                severity="medium",
                status="risk",
                claim_tested="claim",
                evidence="evidence",
                expected="expected",
                actual="actual",
                impact="impact",
                recommendation="recommendation",
            ),
        ]

        self.assertEqual(readiness_score(findings), 70)

    def test_readiness_score_clamps_to_zero(self):
        findings = [
            Finding(
                id=f"F{index}",
                title="Critical issue",
                severity="critical",
                status="blocker",
                claim_tested="claim",
                evidence="evidence",
                expected="expected",
                actual="actual",
                impact="impact",
                recommendation="recommendation",
            )
            for index in range(8)
        ]

        self.assertEqual(readiness_score(findings), 0)

    def test_score_band_names_readiness_ranges(self):
        self.assertEqual(score_band(96), "ready")
        self.assertEqual(score_band(90), "ready-with-caveats")
        self.assertEqual(score_band(75), "partial")
        self.assertEqual(score_band(55), "risky")
        self.assertEqual(score_band(40), "blocked")


if __name__ == "__main__":
    unittest.main()
