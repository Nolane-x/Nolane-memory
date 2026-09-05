import tempfile
import unittest

from nolane_memory import MemoryRuntime


class VersionedSeamCalculiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/seams.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_section_347_v061_seam_calculus(self):
        report = self.rt.run_v061_seam_calculus(seed=347)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["property_family_count"], 36)
        self.assertEqual(report["cases"], 80_553)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["large_randomized_cases"], {
            "obligation_closure": 20_000,
            "region_identity": 20_000,
            "confidentiality_composition": 20_000,
            "hard_role_resource_pressure": 20_000,
        })
        self.assertFalse(report["historical_digest_claimed"])

    def test_section_370_v062_continuity_recovery_erasure_calculus(self):
        report = self.rt.run_v062_continuity_recovery_erasure_calculus(seed=370)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["property_family_count"], 24)
        self.assertEqual(report["cases"], 135_880)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["large_randomized_cases"], {
            "recovery_barrier_resurrection": 40_000,
            "handoff_hard_cover": 30_000,
            "derivative_erasure": 30_000,
            "recovery_trust_stack": 30_000,
        })
        self.assertFalse(report["historical_digest_claimed"])


if __name__ == "__main__":
    unittest.main()
