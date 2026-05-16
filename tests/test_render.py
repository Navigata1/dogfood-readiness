import unittest

from dogfood_readiness.model import ProgressPulse, ReadinessReport
from dogfood_readiness.render import render_markdown


class RenderTests(unittest.TestCase):
    def test_render_markdown_keeps_slice_and_overall_completion_separate(self):
        report = ReadinessReport(
            target="PR 1",
            claim="ready for review",
            score=92,
            pulse=ProgressPulse(
                slice_readiness=92,
                slice_status="ready-with-caveats",
                overall_completion=58.6,
                overall_source="repo reporter",
                blocked_gates=["notarization"],
                next_best_slice="tighten evidence",
            ),
        )

        markdown = render_markdown(report)

        self.assertIn("Slice readiness: **92/100**", markdown)
        self.assertIn("Overall objective completion: **58.6%**", markdown)
        self.assertIn("notarization", markdown)


if __name__ == "__main__":
    unittest.main()
