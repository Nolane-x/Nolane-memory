import tempfile
import unittest

from nolane_memory import MemoryRuntime


class AcceptanceCampaigns263To268Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _assert_campaign(self, method_name, expected_count, seed):
        report = getattr(self.rt, method_name)(seed=seed)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["fixture_count"], expected_count)
        self.assertEqual(report["failed"], 0)

    def test_section_263_temporal_acceptance_campaign(self):
        self._assert_campaign("run_temporal_acceptance_campaign", 9, 263)

    def test_section_264_procedure_failure_acceptance_campaign(self):
        self._assert_campaign("run_procedure_failure_acceptance_campaign", 7, 264)

    def test_section_265_security_privacy_acceptance_campaign(self):
        self._assert_campaign("run_security_privacy_acceptance_campaign", 9, 265)

    def test_section_266_migration_acceptance_campaign(self):
        self._assert_campaign("run_migration_acceptance_campaign", 8, 266)

    def test_section_268_performance_semantic_gate_campaign(self):
        self._assert_campaign("run_performance_semantic_gate_campaign", 5, 268)


if __name__ == "__main__":
    unittest.main()
