import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryDependencyStale
from nolane_memory.types import Answerability, RepairCause


class DynamicRecoverabilityAndCounterexampleRecallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})
        self.rt.register_query_family("Y", {"y"})
        self.region = self.rt.create_region("d", "r", principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _source(self, value=1, cost=30):
        return self.rt.add_representation(
            "d", self.region, kind="raw", payload={"x": value},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(),
            token_cost=cost, principal="alice",
        )

    def test_rehydratable_status_requires_live_source_route_at_use_time(self):
        raw = self._source()
        compact = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"text": "one"},
            source_representation_ids=[raw], loss={"x": LossState.LOST},
            recoverable={"x"}, token_cost=2, principal="alice",
        )
        self.assertEqual(self.rt.answerability(compact, "X"), Answerability.REHYDRATABLE)
        self.rt.invalidate_representation("d", raw, principal="alice")
        self.assertEqual(self.rt.answerability(compact, "X"), Answerability.UNSUPPORTED)

    def test_recoverability_survives_when_an_alternative_live_source_remains(self):
        raw1 = self._source(1)
        raw2 = self._source(1, cost=31)
        compact = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"text": "one"},
            source_representation_ids=[raw1, raw2], loss={"x": LossState.LOST},
            recoverable={"x"}, token_cost=2, principal="alice",
        )
        self.rt.invalidate_representation("d", raw1, principal="alice")
        self.assertEqual(self.rt.answerability(compact, "X"), Answerability.REHYDRATABLE)

    def test_unresolved_counterexample_removes_falsified_representation_from_role_resolution(self):
        raw = self._source(97, cost=30)
        bad = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"x": 100},
            source_representation_ids=[raw], loss={"x": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice", transform_kind="SOURCE_REBASE",
        )
        before = self.rt.compile_recall("d", "alice", [RecallRole("need-x", self.region, "X")], 50)
        self.assertEqual(before.fragments[0].representation_id, bad)
        self.rt.record_query_counterexample(
            "d", region_id=self.region, representation_id=bad, query_family="X",
            lost_dimensions={"x"}, source_witness_id=raw,
            decision_relevance="exact threshold", cause_type=RepairCause.REGION_CONTENT,
            principal="alice",
        )
        after = self.rt.compile_recall("d", "alice", [RecallRole("need-x", self.region, "X")], 50)
        self.assertEqual(after.fragments[0].representation_id, raw)

    def test_counterexample_is_scoped_to_its_query_family(self):
        raw = self._source(1, cost=20)
        bad = self.rt.add_representation(
            "d", self.region, kind="structured", payload={"x": 1, "y": 2},
            loss={"x": LossState.PRESERVED_EXACT, "y": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.record_query_counterexample(
            "d", region_id=self.region, representation_id=bad, query_family="Y",
            lost_dimensions={"y"}, source_witness_id=None,
            decision_relevance="y-only defect", cause_type=RepairCause.REGION_CONTENT,
            principal="alice",
        )
        frame = self.rt.compile_recall("d", "alice", [RecallRole("need-x", self.region, "X")], 50)
        self.assertEqual(frame.fragments[0].representation_id, bad)

    def test_new_counterexample_stales_previously_compiled_frame(self):
        raw = self._source(1, cost=20)
        bad = self.rt.add_representation(
            "d", self.region, kind="structured", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice",
        )
        frame = self.rt.compile_recall("d", "alice", [RecallRole("need-x", self.region, "X")], 50)
        self.assertTrue(self.rt.validate_frame(frame.frame_id))
        self.rt.record_query_counterexample(
            "d", region_id=self.region, representation_id=bad, query_family="X",
            lost_dimensions={"x"}, source_witness_id=raw,
            decision_relevance="newly falsified", cause_type=RepairCause.REGION_CONTENT,
            principal="alice",
        )
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_frame(frame.frame_id)


if __name__ == "__main__":
    unittest.main()
