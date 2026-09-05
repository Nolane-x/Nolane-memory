import json
import os
import subprocess
import sys
import tempfile
import unittest


class PublicAPIReleaseSurfaceTests(unittest.TestCase):
    def test_correctness_bearing_dtos_are_exported_from_package_root(self):
        from nolane_memory import (
            AccessProfileRevision,
            CommitReceipt,
            CounterexampleApplicabilityRevision,
            Dependency,
            FrameFragment,
            FullSpecReleaseGateReport,
            NoTwoWritableClocksAudit,
            RegimeRevision,
            ReplayForensicAssessment,
            SelfVersionProfileRevision,
        )
        self.assertTrue(all(x is not None for x in (
            AccessProfileRevision, CommitReceipt, CounterexampleApplicabilityRevision,
            Dependency, FrameFragment, FullSpecReleaseGateReport,
            NoTwoWritableClocksAudit, RegimeRevision, ReplayForensicAssessment,
            SelfVersionProfileRevision,
        )))

    def _run_cli(self, db, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = "src"
        cp = subprocess.run(
            [sys.executable, "-m", "nolane_memory.cli", "--db", db, *args],
            cwd=os.path.dirname(os.path.dirname(__file__)), env=env,
            text=True, capture_output=True, check=True,
        )
        return json.loads(cp.stdout)

    def test_cli_exposes_ownership_and_release_gate(self):
        with tempfile.TemporaryDirectory() as td:
            db = f"{td}/m.db"
            self._run_cli(db, "init", "d")
            ownership = self._run_cli(db, "ownership")
            self.assertTrue(ownership["passed"])
            self.assertEqual(ownership["primitive_count"], 48)
            gate = self._run_cli(db, "release-gate", "d", "--seed", "7", "--fuzz-cases", "100", "--differential-cases", "8")
            self.assertTrue(gate["implementation_ready"])
            self.assertFalse(gate["research_complete"])
            self.assertEqual(gate["metrics"]["lifelong_fuzz_cases"], 100)


if __name__ == "__main__":
    unittest.main()
