import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import DebtOutcome, LossState, RepairCause
from nolane_memory.errors import MemoryTransitionIncomplete


class K3EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("EXACT", {"exact_number"})
        self.region = self.rt.create_region("d", "r", principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_debt_requires_typed_transition_to_leave_open_state(self):
        debt = self.rt.create_semantic_debt(
            "d", subject_kind="region", subject_id=self.region,
            kind="FUTURE_QUERY_PRESERVATION_UNKNOWN", severity="high",
            evidence_needed="source verification", consequence="exact recall may fail",
            principal="alice",
        )
        self.assertEqual(debt.outcome, DebtOutcome.OPEN.value)
        self.rt.maintenance_fixed_point("d", self.region, {"summary": "unchanged"}, principal="alice")
        still = self.rt.get_semantic_debt(debt.debt_id)
        self.assertEqual(still.outcome, DebtOutcome.OPEN.value)
        closed = self.rt.transition_semantic_debt(
            "d", debt.debt_id, DebtOutcome.DISCHARGED_BY_FORMAL_RESULT,
            evidence_ref="lab:case-17", principal="alice",
        )
        self.assertEqual(closed.outcome, DebtOutcome.DISCHARGED_BY_FORMAL_RESULT.value)
        self.assertIsNotNone(closed.resolved_seq)

    def test_counterexample_repair_keeps_witness_and_uses_source_rebase(self):
        raw = self.rt.add_representation(
            "d", self.region, kind="raw", payload={"exact_number": 97.36},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(),
            token_cost=40, principal="alice", transform_profile="raw-v1",
        )
        summary = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"text": "roughly 100"},
            source_representation_ids=[raw], transform_kind="PURE", transform_profile="summary-v1",
            loss={"exact_number": LossState.LOST}, recoverable={"exact_number"},
            token_cost=5, principal="alice",
        )
        ce = self.rt.record_query_counterexample(
            "d", region_id=self.region, representation_id=summary, query_family="EXACT",
            lost_dimensions={"exact_number"}, source_witness_id=raw,
            decision_relevance="deployment threshold", cause_type=RepairCause.REGION_CONTENT,
            principal="alice",
        )
        receipt = self.rt.repair_counterexample(
            "d", ce.counterexample_id, source_representation_id=raw,
            replacement_payload={"exact_number": 97.36},
            replacement_loss={"exact_number": LossState.PRESERVED_EXACT},
            principal="alice",
        )
        self.assertEqual(receipt.status, "REPAIRED")
        self.assertIn(summary, receipt.invalidated_representation_ids)
        self.assertIsNotNone(receipt.replacement_representation_id)
        persisted = self.rt.get_query_counterexample(ce.counterexample_id)
        self.assertIsNotNone(persisted.resolved_seq)
        self.assertEqual(persisted.replacement_representation_id, receipt.replacement_representation_id)
        row = self.rt.db.execute("SELECT transform_kind FROM representations WHERE representation_id=?", (receipt.replacement_representation_id,)).fetchone()
        self.assertEqual(row[0], "SOURCE_REBASE")

    def test_repair_cannot_restore_from_descendant_that_never_preserved_dimension(self):
        lost = self.rt.add_representation(
            "d", self.region, kind="lossy", payload={"text": "about 100"},
            loss={"exact_number": LossState.LOST}, recoverable=set(), token_cost=5,
            principal="alice", transform_profile="bad-summary",
        )
        ce = self.rt.record_query_counterexample(
            "d", region_id=self.region, representation_id=lost, query_family="EXACT",
            lost_dimensions={"exact_number"}, source_witness_id=None,
            decision_relevance="exact value", cause_type=RepairCause.REGION_CONTENT,
            principal="alice",
        )
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.repair_counterexample(
                "d", ce.counterexample_id, source_representation_id=lost,
                replacement_payload={"exact_number": 100},
                replacement_loss={"exact_number": LossState.PRESERVED_EXACT}, principal="alice",
            )

    def test_stable_maintenance_reaches_fixed_point_without_new_commit(self):
        first = self.rt.maintenance_fixed_point("d", self.region, {"a": 1, "b": [2, 3]}, principal="alice")
        seq = self.rt.head("d").sequence
        second = self.rt.maintenance_fixed_point("d", self.region, {"b": [2, 3], "a": 1}, principal="alice")
        self.assertEqual(first.maintenance_id, second.maintenance_id)
        self.assertEqual(self.rt.head("d").sequence, seq)
        self.assertEqual(second.outcome, "FIXED_POINT")

    def test_shared_transform_profile_repair_fans_out_but_region_content_stays_local(self):
        r2 = self.rt.create_region("d", "r2", principal="alice")
        raw1 = self.rt.add_representation("d", self.region, kind="raw", payload={"exact_number": 1},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=5, principal="alice", transform_profile="raw")
        raw2 = self.rt.add_representation("d", r2, kind="raw", payload={"exact_number": 2},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=5, principal="alice", transform_profile="raw")
        s1 = self.rt.add_representation("d", self.region, kind="summary", payload={"x": 1}, source_representation_ids=[raw1],
            loss={"exact_number": LossState.LOST}, recoverable={"exact_number"}, token_cost=2, principal="alice", transform_profile="buggy-v7")
        s2 = self.rt.add_representation("d", r2, kind="summary", payload={"x": 2}, source_representation_ids=[raw2],
            loss={"exact_number": LossState.LOST}, recoverable={"exact_number"}, token_cost=2, principal="alice", transform_profile="buggy-v7")
        ce = self.rt.record_query_counterexample("d", region_id=self.region, representation_id=s1, query_family="EXACT",
            lost_dimensions={"exact_number"}, source_witness_id=raw1, decision_relevance="profile bug",
            cause_type=RepairCause.SHARED_TRANSFORM_PROFILE, principal="alice")
        receipt = self.rt.repair_counterexample("d", ce.counterexample_id, source_representation_id=raw1,
            replacement_payload={"exact_number": 1}, replacement_loss={"exact_number": LossState.PRESERVED_EXACT}, principal="alice")
        self.assertIn(s1, receipt.invalidated_representation_ids)
        self.assertIn(s2, receipt.invalidated_representation_ids)
        self.assertIn("transform_profile:buggy-v7", receipt.dependency_fanout)


if __name__ == "__main__": unittest.main()
