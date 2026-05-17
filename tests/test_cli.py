"""CLI-level tests for readiness report generation artifacts."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from dogfood_readiness import Finding
from dogfood_readiness.cli import build_report, write_bundle, parse_args
from dogfood_readiness.cli import _load_findings
from dogfood_readiness.model import MutationEvent


class LoadFindingsTests(unittest.TestCase):
    def test_load_findings_reads_valid_file(self):
        payload = [
            {
                "id": "F1",
                "title": "Bad conversion path",
                "severity": "high",
                "status": "blocked",
                "claim_tested": "converter",
                "evidence": "No tests",
                "expected": "deterministic output",
                "actual": "nondeterministic output",
                "impact": "may mis-translate user code",
                "recommendation": "add differential testing",
                "security_domain": "code-execution",
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            finding_path = Path(tmpdir) / "findings.json"
            finding_path.write_text(json.dumps(payload), encoding="utf-8")
            findings = _load_findings(finding_path)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0], Finding(
            id="F1",
            title="Bad conversion path",
            severity="high",
            status="blocked",
            claim_tested="converter",
            evidence="No tests",
            expected="deterministic output",
            actual="nondeterministic output",
            impact="may mis-translate user code",
            recommendation="add differential testing",
            security_domain="code-execution",
        ))

    def test_load_findings_rejects_non_array(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            finding_path = Path(tmpdir) / "findings.json"
            finding_path.write_text('{"id":"F1"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                _load_findings(finding_path)


class CliArtifactTests(unittest.TestCase):
    def _build_args(self, temp_root: Path) -> argparse.Namespace:
        return parse_args(
            [
                "--target",
                "repo-pr",
                "--claim",
                "converter import is safe",
                "--output",
                str(temp_root / "out"),
                "--findings",
                str(temp_root / "findings.json"),
                "--next-best-slice",
                "stabilize converter advisory",
                "--overall-completion",
                "58.6",
                "--overall-source",
                "manual-estimate",
                "--blocked-gate",
                "notarization",
                "--blocked-gate",
                "windows-mvp",
                "--missed-checker-failures",
                "2",
                "--blocked-core-cases",
                "1",
            ]
        )

    def test_build_report_includes_findings_and_mutation_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            finding_path = temp_root / "findings.json"
            finding_path.write_text(
                json.dumps([
                    {
                        "id": "F1",
                        "title": "Missing evidence row",
                        "severity": "low",
                        "status": "risk",
                        "claim_tested": "baseline",
                        "evidence": "No evidence attached",
                        "expected": "artifact exists",
                        "actual": "missing",
                        "impact": "unknown",
                        "recommendation": "attach verifier output",
                    }
                ]),
                encoding="utf-8",
            )

            args = self._build_args(temp_root)
            report = build_report(args)

        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].id, "F1")
        self.assertGreaterEqual(len(report.matrix), 4)
        self.assertGreater(len(report.mutation_log), 0)
        self.assertIsInstance(report.mutation_log[0], MutationEvent)
        self.assertIn("findings=1", report.mutation_log[0].details)

    def test_write_bundle_writes_all_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outdir = Path(tmpdir) / "bundle"
            report = build_report(
                parse_args(
                    [
                        "--target",
                        "repo-pr",
                        "--claim",
                        "local smoke",
                        "--output",
                        str(outdir),
                    ]
                )
            )
            write_bundle(report, outdir)
            artifacts = {
                (outdir / "dogfood-readiness-data.json"),
                (outdir / "dogfood-readiness-report.md"),
                (outdir / "dogfood-readiness-mutation-log.md"),
            }
            for path in artifacts:
                self.assertTrue(path.exists(), f"expected artifact: {path}")

            json_payload = json.loads((outdir / "dogfood-readiness-data.json").read_text(encoding="utf-8"))
            self.assertEqual(json_payload["target"], "repo-pr")


if __name__ == "__main__":
    unittest.main()
