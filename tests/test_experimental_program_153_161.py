import tempfile
import unittest

from nolane_memory import MemoryRuntime


class ExperimentalProgram153To161Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/exp.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_metric_catalog_and_summary_preserve_silent_violation_denominators_and_tails(self):
        catalog = self.rt.experimental_metric_catalog()
        for name in ("MAPE", "ARCE", "WDWRE", "CPIL", "RSD", "DEAR", "FIPR"):
            self.assertIn(name, catalog["semantic_errors"])
        self.assertIn("Protected Query Family Coverage", catalog["preservation_corrigibility"])
        self.assertIn("Memory-enabled vs NullMemory decision delta", catalog["effect_interference"])
        summary = self.rt.summarize_experiment_metrics([
            {"silent_violation": False, "abstained": False, "overflow": False, "frame_tokens": 10, "latency_ms": 4, "page_faults": 0},
            {"silent_violation": True, "abstained": False, "overflow": False, "frame_tokens": 20, "latency_ms": 8, "page_faults": 1},
            {"silent_violation": False, "abstained": True, "overflow": True, "frame_tokens": 30, "latency_ms": 12, "page_faults": 2},
        ])
        self.assertEqual(summary["denominator"], 3)
        self.assertEqual(summary["silent_violation_numerator"], 1)
        self.assertEqual(summary["abstentions"], 1)
        self.assertEqual(summary["overflows"], 1)
        self.assertEqual(summary["frame_tokens"]["p50"], 20)
        self.assertEqual(summary["latency_ms"]["p95"], 12)

    def test_interaction_ablation_protocol_contains_all_required_composition_pairs(self):
        protocol = self.rt.interaction_ablation_protocol()
        self.assertEqual(len(protocol["interactions"]), 8)
        names = {x["name"] for x in protocol["interactions"]}
        self.assertIn("consolidation_x_counterexample_preservation", names)
        self.assertIn("witness_cover_retention_x_privacy_deletion", names)
        self.assertIn("effect_guard_x_hard_role_conservation", names)
        self.assertTrue(all(x["reports_task_quality"] and x["reports_semantic_violations"] for x in protocol["interactions"]))
        self.assertEqual(protocol["external_result_status"], "NOT_RUN")

    def test_private_stress_world_campaign_executes_all_section_160_worlds(self):
        report = self.rt.run_private_stress_world_campaign(seed=160)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["world_count"], 12)
        self.assertTrue(all(x["typed_outcome"] for x in report["worlds"]))

    def test_longitudinal_protocol_pins_configuration_and_records_nullmemory_and_exposure_chain(self):
        report = self.rt.run_longitudinal_experiment_protocol(seed=161, checkpoints=(1, 2, 4))
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["checkpoint_count"], 3)
        self.assertEqual([x["prefix"] for x in report["checkpoints"]], [1, 2, 4])
        self.assertTrue(all(x["configuration_digest"] == report["configuration_digest"] for x in report["checkpoints"]))
        self.assertTrue(all("null_memory" in x and "memory_enabled" in x for x in report["checkpoints"]))
        self.assertTrue(all(x["memory_enabled"]["exposure_chain"]["candidate"] for x in report["checkpoints"]))
        self.assertEqual(report["external_validity"], "NOT_CLAIMED")


if __name__ == "__main__":
    unittest.main()
