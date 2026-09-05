import tempfile
import unittest

from nolane_memory import MemoryRuntime


class PersistenceLifelongFuzzTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/host.db")
        self.rt.create_domain("host")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_real_persistence_state_machine_fuzz_checks_incremental_vs_full_recompute(self):
        report = self.rt.run_persistence_lifelong_fuzz(seed=261, cases=800, restart_interval=73, recompute_interval=17)
        self.assertEqual(report.failed, 0, report.details)
        self.assertEqual(report.cases, 800)
        self.assertGreater(report.details["restart_count"], 0)
        self.assertGreater(report.details["full_recomputation_checks"], 0)
        self.assertEqual(report.details["projection_drift_failures"], 0)

    def test_persistence_fuzz_exercises_all_required_lifelong_operation_families(self):
        report = self.rt.run_persistence_lifelong_fuzz(seed=262, cases=1200, restart_interval=101, recompute_interval=29)
        self.assertEqual(report.failed, 0, report.details)
        required = {
            "capture", "claim_correction", "transform", "consolidate", "split_merge",
            "archive_delete", "counterexample_repair", "regime_change", "model_upgrade",
            "index_lag_rebuild", "context_reset_recovery", "migration",
        }
        self.assertTrue(required.issubset(set(report.details["operation_counts"])), report.details["operation_counts"])
        self.assertTrue(all(report.details["operation_counts"][name] > 0 for name in required))


if __name__ == "__main__": unittest.main()
