import tempfile
import unittest

from nolane_memory import MemoryRuntime


class RecoveryPrivacyAcceptanceCampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("root")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_section_373_all_mandatory_fixtures_are_executable(self):
        report = self.rt.run_recovery_privacy_acceptance_campaign(seed=373)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["fixture_count"], 18)
        self.assertEqual(report["failed"], 0)

    def test_campaign_includes_restore_erasure_and_handoff_barrier_families(self):
        report = self.rt.run_recovery_privacy_acceptance_campaign(seed=374)
        by = {x["fixture"]: x for x in report["outcomes"]}
        for name in (
            "checkpoint_before_privacy_delete_restore_after_barrier",
            "source_compromise_after_snapshot",
            "raw_delete_derived_private_summary",
            "continuity_handoff_deleted_source_content",
            "missing_barrier_ledger_during_recovery",
        ):
            self.assertIn(name, by)
            self.assertTrue(by[name]["passed"], by[name])

    def test_campaign_preserves_independent_support_while_quarantining_tainted_derivative(self):
        report = self.rt.run_recovery_privacy_acceptance_campaign(seed=375)
        item = next(x for x in report["outcomes"] if x["fixture"] == "independent_support_tainted_derivative_clean_rederive")
        self.assertTrue(item["passed"])
        self.assertEqual(item["observed"], "SUPPORTED_WITH_CLEAN_REDERIVATION")


if __name__ == "__main__": unittest.main()
