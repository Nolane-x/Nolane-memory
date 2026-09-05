from datetime import datetime, timedelta, timezone
import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale, MemoryTransitionIncomplete


class TemporalProcedureConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = datetime(2026, 9, 5, 0, 0, tzinfo=timezone.utc)
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db", clock=lambda: self.now)
        self.rt.create_domain("d")
        self.region = self.rt.create_region("d", "r", principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _evidence(self, op, sid, world_time):
        h = self.rt._head_row("d")
        return self.rt.capture_evidence(
            domain_id="d", operation_id=op, expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), source_event_identity=sid,
            content={"state": "ON"}, principal="alice", world_time=world_time,
        ).object_id

    def test_point_observations_do_not_prove_continuous_interval_without_contract(self):
        t1 = self.now; t3 = self.now + timedelta(hours=2)
        e1 = self._evidence("e1", "s1", t1); e3 = self._evidence("e3", "s3", t3)
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.certify_temporal_coverage(
                "d", [e1, e3], valid_from=t1, valid_to=t3,
                principal="alice", coverage_contract=None,
            )
        receipt = self.rt.certify_temporal_coverage(
            "d", [e1, e3], valid_from=t1, valid_to=t3,
            principal="alice", coverage_contract="sensor-continuity-v1",
        )
        self.assertTrue(self.rt.temporal_coverage_contains(receipt.receipt_id, t1))
        self.assertTrue(self.rt.temporal_coverage_contains(receipt.receipt_id, t3 - timedelta(microseconds=1)))
        self.assertFalse(self.rt.temporal_coverage_contains(receipt.receipt_id, t3))
        self.rt.revoke_evidence("d", e1, principal="alice")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_temporal_coverage(receipt.receipt_id)

    def test_procedure_learning_partitions_outcomes_by_applicability_and_dedupes_events(self):
        proposal = self.rt.learn_procedure(
            "d", procedure_key="install-tool", principal="alice", experiences=[
                {"event_identity": "run-1", "outcome": "SUCCESS", "applicability": {"os": "linux", "tool": "v1"}},
                {"event_identity": "run-1", "outcome": "SUCCESS", "applicability": {"os": "linux", "tool": "v1"}},
                {"event_identity": "run-2", "outcome": "FAILURE", "applicability": {"os": "windows", "tool": "v1"}},
            ],
        )
        self.assertEqual(proposal["generic_status"], "CONDITIONAL")
        self.assertEqual(proposal["unique_event_count"], 2)
        by_os = {s["applicability"]["os"]: s for s in proposal["slices"]}
        self.assertEqual(by_os["linux"]["success_count"], 1)
        self.assertEqual(by_os["linux"]["status"], "SUPPORTED")
        self.assertEqual(by_os["windows"]["failure_count"], 1)
        self.assertEqual(by_os["windows"]["status"], "NEGATIVE_APPLICABILITY")

    def test_contradictory_outcomes_inside_same_slice_remain_unresolved(self):
        proposal = self.rt.learn_procedure(
            "d", procedure_key="deploy", principal="alice", experiences=[
                {"event_identity": "a", "outcome": "SUCCESS", "applicability": {"env": "prod"}},
                {"event_identity": "b", "outcome": "FAILURE", "applicability": {"env": "prod"}},
            ],
        )
        self.assertEqual(proposal["generic_status"], "UNRESOLVED")
        self.assertEqual(proposal["slices"][0]["status"], "UNRESOLVED")

    def test_transient_failure_is_retained_but_does_not_falsify_procedure_hypothesis(self):
        proposal = self.rt.learn_procedure(
            "d", procedure_key="fetch", principal="alice", experiences=[
                {"event_identity":"ok","outcome":"SUCCESS","applicability":{"env":"prod"}},
                {"event_identity":"timeout","outcome":"FAILURE","failure_kind":"TRANSIENT_TIMEOUT",
                 "reproducer_ref":"trace:timeout","applicability":{"env":"prod"}},
            ],
        )
        sl = proposal["slices"][0]
        self.assertEqual(sl["status"], "SUPPORTED_WITH_TRANSIENT_FAILURE")
        self.assertEqual(sl["hypothesis_failure_event_ids"], [])
        self.assertEqual(sl["transient_failure_event_ids"], ["timeout"])
        self.assertEqual(sl["reproducer_refs"]["timeout"], "trace:timeout")

    def test_catastrophic_failure_is_protected_even_when_single_observation(self):
        proposal = self.rt.learn_procedure(
            "d", procedure_key="delete-db", principal="alice", experiences=[
                {"event_identity":"cat-1","outcome":"FAILURE","failure_kind":"HYPOTHESIS_RELEVANT",
                 "severity":"CATASTROPHIC","reproducer_ref":"trace:cat",
                 "applicability":{"env":"prod"}},
            ],
        )
        sl = proposal["slices"][0]
        self.assertEqual(sl["status"], "NEGATIVE_APPLICABILITY")
        self.assertEqual(sl["protected_failure_event_ids"], ["cat-1"])
        self.assertEqual(proposal["when_not_to_use"], [{"env":"prod"}])


    def test_selective_consolidation_triggers_from_store_pressure_not_age_alone(self):
        self.rt.register_consolidation_policy(
            "d", revision=1, trigger_on_open_debt=True, trigger_on_counterexample=True,
            min_active_representations=99, max_derivation_depth=99,
        )
        quiet = self.rt.assess_consolidation_pressure("d", self.region, principal="alice")
        self.assertFalse(quiet["triggered"])
        self.rt.create_semantic_debt(
            "d", subject_kind="region", subject_id=self.region, kind="TEST_DEBT",
            severity="high", evidence_needed="source", consequence="unknown",
            principal="alice",
        )
        pressured = self.rt.assess_consolidation_pressure("d", self.region, principal="alice")
        self.assertTrue(pressured["triggered"])
        self.assertIn("OPEN_SEMANTIC_DEBT", pressured["reasons"])


if __name__ == "__main__": unittest.main()
