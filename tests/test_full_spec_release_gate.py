import tempfile
import unittest

from nolane_memory import MemoryRuntime


class FullSpecReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_full_spec_gate_passes_implementation_checks_but_does_not_fake_research_closure(self):
        report = self.rt.run_full_spec_release_gate("d", seed=603, fuzz_cases=1000, differential_cases=32, persistence_fuzz_cases=120)
        self.assertTrue(report.implementation_ready)
        self.assertFalse(report.research_complete)
        self.assertEqual(report.research_closure, "BLOCKED")
        self.assertTrue(all(v == "PASS" for v in report.checks.values()))
        self.assertEqual(report.metrics["preservation_lab_failures"], 0)
        self.assertEqual(report.metrics["lifelong_fuzz_failures"], 0)
        self.assertEqual(report.metrics["differential_failures"], 0)
        self.assertEqual(report.metrics["fault_probe_failures"], 0)
        self.assertEqual(report.checks["persistence_lifelong_fuzz"], "PASS")
        self.assertEqual(report.checks["use_time_race_campaign"], "PASS")
        self.assertEqual(report.checks["recovery_privacy_campaign"], "PASS")
        self.assertEqual(report.checks["publication_cycle_campaign"], "PASS")
        self.assertEqual(report.checks["information_flow_use_time_campaign"], "PASS")
        self.assertEqual(report.checks["resource_pressure_use_validation_campaign"], "PASS")
        self.assertEqual(report.checks["temporal_acceptance_campaign"], "PASS")
        self.assertEqual(report.checks["procedure_failure_acceptance_campaign"], "PASS")
        self.assertEqual(report.checks["security_privacy_acceptance_campaign"], "PASS")
        self.assertEqual(report.checks["migration_acceptance_campaign"], "PASS")
        self.assertEqual(report.checks["performance_semantic_gate_campaign"], "PASS")
        self.assertEqual(report.checks["reference_formal_suite"], "PASS")
        self.assertEqual(report.checks["experimental_metric_contract"], "PASS")
        self.assertEqual(report.checks["interaction_ablation_protocol"], "PASS")
        self.assertEqual(report.checks["private_stress_world_campaign"], "PASS")
        self.assertEqual(report.checks["longitudinal_experiment_protocol"], "PASS")
        self.assertEqual(report.checks["use_time_causal_cut_calculus"], "PASS")
        self.assertEqual(report.checks["v061_seam_calculus"], "PASS")
        self.assertEqual(report.checks["v062_continuity_recovery_erasure_calculus"], "PASS")
        self.assertEqual(report.metrics["v061_seam_calculus_failures"], 0)
        self.assertEqual(report.metrics["v061_seam_calculus_cases"], 80553)
        self.assertEqual(report.metrics["v061_seam_calculus_property_families"], 36)
        self.assertEqual(report.metrics["v062_continuity_calculus_failures"], 0)
        self.assertEqual(report.metrics["v062_continuity_calculus_cases"], 135880)
        self.assertEqual(report.metrics["v062_continuity_calculus_property_families"], 24)
        self.assertEqual(report.metrics["persistence_fuzz_failures"], 0)
        self.assertEqual(report.metrics["use_time_race_failures"], 0)
        self.assertEqual(report.metrics["recovery_privacy_failures"], 0)
        self.assertEqual(report.metrics["publication_cycle_failures"], 0)
        self.assertEqual(report.metrics["information_flow_use_time_failures"], 0)
        self.assertEqual(report.metrics["resource_pressure_use_validation_failures"], 0)
        self.assertEqual(report.metrics["temporal_acceptance_failures"], 0)
        self.assertEqual(report.metrics["procedure_failure_acceptance_failures"], 0)
        self.assertEqual(report.metrics["security_privacy_acceptance_failures"], 0)
        self.assertEqual(report.metrics["migration_acceptance_failures"], 0)
        self.assertEqual(report.metrics["performance_semantic_gate_failures"], 0)
        self.assertEqual(report.metrics["reference_formal_suite_failures"], 0)
        self.assertEqual(report.metrics["reference_formal_property_families"], 16)
        self.assertEqual(report.metrics["private_stress_world_failures"], 0)
        self.assertEqual(report.metrics["private_stress_world_count"], 12)
        self.assertEqual(report.metrics["interaction_ablation_count"], 8)
        self.assertGreaterEqual(report.metrics["longitudinal_checkpoint_count"], 3)
        self.assertEqual(report.metrics["use_time_calculus_failures"], 0)
        self.assertEqual(report.metrics["use_time_calculus_cases"], 131701)
        self.assertEqual(report.metrics["use_time_calculus_property_families"], 34)

    def test_full_spec_gate_fails_when_single_clock_audit_fails(self):
        self.rt.set_access_profile("d", "alice", ["READ_EXACT"])
        self.rt.db.execute(
            "UPDATE access_profiles SET revision=99 WHERE domain_id='d' AND principal='alice'"
        )
        report = self.rt.run_full_spec_release_gate("d", seed=1, fuzz_cases=50, differential_cases=4, persistence_fuzz_cases=60)
        self.assertFalse(report.implementation_ready)
        self.assertEqual(report.checks["no_two_writable_clocks"], "FAIL")

    def test_release_gate_persists_machine_readable_evidence(self):
        report = self.rt.run_full_spec_release_gate("d", seed=2, fuzz_cases=25, differential_cases=2, persistence_fuzz_cases=60)
        row = self.rt.db.execute(
            "SELECT report_json FROM release_gate_runs WHERE gate_id=?", (report.gate_id,)
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertIn('"research_complete":false', row[0])
        self.assertIn('"implementation_ready":true', row[0])


if __name__ == "__main__":
    unittest.main()
