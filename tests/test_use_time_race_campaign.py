import tempfile
import unittest

from nolane_memory import MemoryRuntime


class UseTimeRaceCampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db", clock_authority_id="race-clock", clock_epoch="race-epoch")
        self.rt.create_domain("root")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_section_401_campaign_executes_all_required_interleavings(self):
        report = self.rt.run_use_time_race_campaign(seed=401)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["schedule_count"], 10)
        self.assertEqual(report["failed"], 0)
        names = {x["schedule"] for x in report["outcomes"]}
        self.assertEqual(names, {
            "proposal_revoke_promote",
            "outer_query_concurrent_stale",
            "frame_access_revoke_use",
            "frame_unrelated_write_use",
            "frame_argument_mutation_dispatch",
            "fence_tool_generation_change",
            "protected_lease_clock_authority",
            "context_scoped_foreign_profile",
            "publication_causal_cut_lag",
            "negative_result_matching_write",
        })

    def test_unrelated_write_is_dependency_minimal_not_false_stale(self):
        report = self.rt.run_use_time_race_campaign(seed=402)
        outcome = next(x for x in report["outcomes"] if x["schedule"] == "frame_unrelated_write_use")
        self.assertTrue(outcome["passed"])
        self.assertEqual(outcome["observed"], "USE_ALLOWED")

    def test_relevant_races_have_typed_fail_visible_outcomes(self):
        report = self.rt.run_use_time_race_campaign(seed=403)
        by = {x["schedule"]: x for x in report["outcomes"]}
        self.assertEqual(by["proposal_revoke_promote"]["observed"], "PROPOSAL_STALE")
        self.assertEqual(by["frame_access_revoke_use"]["observed"], "MEMORY_DEPENDENCY_STALE")
        self.assertEqual(by["frame_argument_mutation_dispatch"]["observed"], "ACTION_ARGUMENT_MISMATCH")
        self.assertEqual(by["fence_tool_generation_change"]["observed"], "MEMORY_DEPENDENCY_STALE")
        self.assertEqual(by["protected_lease_clock_authority"]["observed"], "CLOCK_AUTHORITY_REQUIRED")
        self.assertEqual(by["negative_result_matching_write"]["observed"], "MEMORY_DEPENDENCY_STALE")


if __name__ == "__main__": unittest.main()
