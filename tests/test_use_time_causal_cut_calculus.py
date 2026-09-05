import tempfile
import unittest

from nolane_memory import MemoryRuntime


class UseTimeCausalCutCalculusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/calc.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_section_396_reexecutes_all_34_property_families_and_131701_cases(self):
        report = self.rt.run_use_time_causal_cut_calculus(seed=396)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["property_family_count"], 34)
        self.assertEqual(len(report["property_families"]), 34)
        self.assertEqual(report["cases"], 131_701)
        self.assertEqual(report["large_randomized_cases"], {
            "use_time_toctou": 40_000,
            "proposal_semantic_occ": 30_000,
            "multi_domain_causal_cut": 30_000,
            "applicability_scope": 20_000,
        })
        self.assertTrue(report["relevant_mutation_invalidates"])
        self.assertTrue(report["irrelevant_mutation_tolerated"])
        self.assertFalse(report["historical_digest_claimed"])
        self.assertEqual(len(report["digest"]), 64)


if __name__ == "__main__":
    unittest.main()
