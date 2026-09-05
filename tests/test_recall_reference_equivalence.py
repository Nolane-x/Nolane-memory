import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryRecallAmbiguous
from nolane_memory.types import LossState, RecallRole


class RecallReferenceEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_strong_recall_rejects_decision_distinct_exact_histories(self):
        region = self.rt.create_region("d", "ambiguous", principal="alice")
        for value in (1, 2):
            self.rt.add_representation(
                "d", region, kind="raw", payload={"x": value},
                loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
                principal="alice",
            )
        with self.assertRaises(MemoryRecallAmbiguous):
            self.rt.compile_recall("d", "alice", [RecallRole("x", region, "X", hard=True)], 10)

    def test_section_260_reference_campaign_covers_all_representative_worlds(self):
        report = self.rt.run_recall_reference_equivalence_campaign(seed=260)
        self.assertTrue(report["passed"])
        self.assertEqual(report["fixture_count"], 10)
        self.assertEqual(report["failed"], 0)
        self.assertGreater(report["sufficient_reference_comparisons"], 0)
        names = {x["fixture"] for x in report["outcomes"]}
        self.assertIn("decision_distinct_histories", names)
        self.assertIn("partial_connector_no_global_absence", names)
        self.assertIn("hard_roles_over_budget", names)


if __name__ == "__main__":
    unittest.main()
