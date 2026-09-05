import tempfile
import unittest

from nolane_memory import MemoryRuntime


class ReferenceFormalSuiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/formal.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_sections_133_139_reference_formal_suite_covers_all_sixteen_property_families(self):
        report = self.rt.run_reference_formal_suite(seed=139, lifelong_cases=2_000)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["property_family_count"], 16)
        self.assertEqual(len(report["property_families"]), 16)
        self.assertEqual(report["answerability_cases"], 32 ** 3)
        self.assertEqual(report["loss_chain_cases"], 20_000)
        self.assertEqual(report["justification_cases"], 8)
        self.assertEqual(report["local_repair_regions"], 1_000)
        self.assertEqual(report["lifelong_cases"], 2_000)
        self.assertGreaterEqual(report["witness_cover_cases"], 1_000)
        self.assertGreaterEqual(report["hard_frame_cases"], 1_000)

    def test_default_formal_suite_uses_section_138_fifty_thousand_step_fuzz(self):
        report = self.rt.run_reference_formal_suite(seed=138)
        self.assertEqual(report["lifelong_cases"], 50_000)
        self.assertEqual(report["failed"], 0)


if __name__ == "__main__":
    unittest.main()
