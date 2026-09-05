import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryTransitionIncomplete


class ResearchAcceptanceRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.rt=MemoryRuntime(f"{self.tmp.name}/m.db"); self.rt.create_domain("d")
    def tearDown(self): self.rt.close(); self.tmp.cleanup()

    def _fairness(self):
        return {
            "base_model_version":"model-v1","context_limit":8192,"tool_access":["none"],
            "embedding_reranker":"none","consolidation_model":"none","memory_construction_cost":10,
            "maintenance_cost":2,"storage_size":100,"random_seeds":[1,2,3],"judge_configuration":"exact",
            "baselines":["no_persistent_memory","long_context"],
        }

    def test_benchmark_evidence_rejects_incomplete_fairness_contract(self):
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.record_benchmark_evidence(
                benchmark="Synthetic",claim="temporal_correctness",score={"accuracy":0.9},metadata={"base_model_version":"m"}
            )
        rec=self.rt.record_benchmark_evidence(
            benchmark="Synthetic",claim="temporal_correctness",score={"accuracy":0.9},metadata=self._fairness()
        )
        self.assertEqual(rec["claim"],"temporal_correctness")
        self.assertEqual(rec["fairness_status"],"COMPLETE")

    def test_migration_manifest_requires_explicit_action_for_every_critical_surface(self):
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.register_migration_manifest(
                "d",migration_id="m1",from_schema="legacy",to_schema="v0.6.3",
                field_actions={"origin_identity":"DOWNGRADE"},
            )
        actions={field:"REVALIDATE" for field in self.rt.migration_correctness_fields()}
        actions["origin_identity"]="DOWNGRADE"
        actions["approximate_indexes"]="RECOMPUTE"
        manifest=self.rt.register_migration_manifest(
            "d",migration_id="m2",from_schema="legacy",to_schema="v0.6.3",field_actions=actions,
        )
        self.assertEqual(manifest["status"],"VALIDATED")
        self.assertEqual(manifest["field_actions"]["origin_identity"],"DOWNGRADE")

    def test_migration_manifest_rejects_semantic_upgrade_action(self):
        actions={field:"REVALIDATE" for field in self.rt.migration_correctness_fields()}
        actions["origin_identity"]="UPGRADE_TO_EXACT"
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.register_migration_manifest(
                "d",migration_id="m3",from_schema="legacy",to_schema="v0.6.3",field_actions=actions,
            )

    def test_context_scalability_probe_separates_store_size_from_dependency_width(self):
        report=self.rt.run_context_scalability_probe(
            store_sizes=[10,100],dependency_widths=[1,2,4],token_cost_per_dependency=3,token_budget=7,
        )
        store_tokens=[p["frame_tokens"] for p in report["store_size_axis"]]
        self.assertEqual(store_tokens,[3,3])
        width=[(p["dependency_width"],p["frame_tokens"],p["status"]) for p in report["dependency_width_axis"]]
        self.assertEqual(width[0],(1,3,"SUFFICIENT"))
        self.assertEqual(width[1],(2,6,"SUFFICIENT"))
        self.assertEqual(width[2],(4,12,"OVERFLOW_ESCALATED"))
        self.assertEqual(report["wrong_decision_without_escalation"],0)


if __name__=='__main__': unittest.main()
