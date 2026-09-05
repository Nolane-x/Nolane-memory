import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import (
    DebtOutcome, EffectTier, FlowDecision, RecoveryLayerStatus,
    SemanticDebt, QueryCounterexample, FrameInformationFlowReceipt,
    RecoveryResumeAssessment, MemoryErasureClosureReceipt,
)


class FullProfileSchemaTests(unittest.TestCase):
    def test_full_profile_types_and_tables_exist(self):
        self.assertEqual(DebtOutcome.OPEN.value, "OPEN")
        self.assertEqual(EffectTier.E0.value, "E0")
        self.assertEqual(FlowDecision.ALLOW.value, "ALLOW")
        self.assertEqual(RecoveryLayerStatus.PASS.value, "PASS")
        self.assertTrue(hasattr(SemanticDebt, "__dataclass_fields__"))
        self.assertTrue(hasattr(QueryCounterexample, "__dataclass_fields__"))
        self.assertTrue(hasattr(FrameInformationFlowReceipt, "__dataclass_fields__"))
        self.assertTrue(hasattr(RecoveryResumeAssessment, "__dataclass_fields__"))
        self.assertTrue(hasattr(MemoryErasureClosureReceipt, "__dataclass_fields__"))

        tmp = tempfile.TemporaryDirectory()
        rt = MemoryRuntime(f"{tmp.name}/memory.db")
        try:
            tables = {r[0] for r in rt.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for required in {
                "semantic_debts", "query_counterexamples", "retention_events", "protected_obligations",
                "access_profiles", "declassification_receipts", "flow_receipts", "effect_evidence",
                "prospective_triggers", "self_versions", "continuity_pins", "recovery_assessments",
                "erasure_closure_receipts", "discovery_index", "capability_availability",
                "maintenance_receipts", "probe_checkpoints", "publication_receipts",
            }:
                self.assertIn(required, tables)
        finally:
            rt.close(); tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
