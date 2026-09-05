import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryWriteConflict
from nolane_memory.types import RepairCause


class PolicyProfileRevisionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_access_profile_preserves_revision_history_and_historical_lookup(self):
        self.assertEqual(self.rt.set_access_profile("d", "alice", ["READ_EXACT"]), 1)
        seq1 = self.rt.head("d").sequence
        self.assertEqual(self.rt.set_access_profile("d", "alice", ["READ_EXACT", "HYDRATE_SOURCE"]), 2)
        current = self.rt.get_access_profile_revision("d", "alice")
        old = self.rt.get_access_profile_revision("d", "alice", at_seq=seq1)
        self.assertEqual(current.revision, 2)
        self.assertEqual(current.predecessor_revision, 1)
        self.assertEqual(set(current.capabilities), {"READ_EXACT", "HYDRATE_SOURCE"})
        self.assertEqual(old.revision, 1)
        self.assertEqual(old.capabilities, ["READ_EXACT"])
        self.assertEqual([r.revision for r in self.rt.list_access_profile_revisions("d", "alice")], [1, 2])

    def test_regime_profile_preserves_revision_history_and_cut_lookup(self):
        self.rt.set_runtime_compatibility(
            "d", mission_revision="m1", environment_revision="linux", schema_revision="s1"
        )
        seq1 = self.rt.head("d").sequence
        self.rt.set_runtime_compatibility(
            "d", mission_revision="m2", environment_revision="windows", schema_revision="s2"
        )
        current = self.rt.get_regime_revision("d")
        old = self.rt.get_regime_revision("d", at_seq=seq1)
        self.assertEqual((current.revision, current.predecessor_revision), (2, 1))
        self.assertEqual((current.mission_revision, current.environment_revision, current.schema_revision), ("m2", "windows", "s2"))
        self.assertEqual((old.revision, old.environment_revision), (1, "linux"))

    def test_self_version_preserves_revision_history(self):
        self.rt.set_self_version("d", "model-v1", {"context": 1000})
        seq1 = self.rt.head("d").sequence
        self.rt.set_self_version("d", "model-v2", {"context": 2000})
        current = self.rt.get_self_version_revision("d")
        old = self.rt.get_self_version_revision("d", at_seq=seq1)
        self.assertEqual((current.revision, current.profile_id), (2, "model-v2"))
        self.assertEqual((old.revision, old.profile_id), (1, "model-v1"))
        self.assertEqual(current.predecessor_revision, 1)

    def test_counterexample_applicability_is_revisioned_and_regime_scoped(self):
        self.rt.register_query_family("X", {"x"})
        region = self.rt.create_region("d", "r", principal="alice")
        raw = self.rt.add_representation(
            "d", region, kind="raw", payload={"x": 97},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=20, principal="alice",
        )
        compact = self.rt.add_representation(
            "d", region, kind="summary", payload={"x": 100}, source_representation_ids=[raw],
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice", transform_kind="SOURCE_REBASE",
        )
        self.rt.set_runtime_compatibility("d", mission_revision="m", environment_revision="windows")
        ce = self.rt.record_query_counterexample(
            "d", region_id=region, representation_id=compact, query_family="X",
            lost_dimensions={"x"}, source_witness_id=raw, decision_relevance="linux-only defect",
            cause_type=RepairCause.REGION_CONTENT, principal="alice",
            applicability={"environment_revision": "linux"},
        )
        # In Windows the counterexample is preserved but not applicable.
        frame = self.rt.compile_recall("d", "alice", [RecallRole("x", region, "X")], 50)
        self.assertEqual(frame.fragments[0].representation_id, compact)

        self.rt.set_runtime_compatibility("d", mission_revision="m", environment_revision="linux")
        frame = self.rt.compile_recall("d", "alice", [RecallRole("x", region, "X")], 50)
        self.assertEqual(frame.fragments[0].representation_id, raw)

        r1 = self.rt.get_counterexample_applicability("d", ce.counterexample_id)
        self.assertEqual((r1.revision, r1.status, r1.applicability["environment_revision"]), (1, "ACTIVE", "linux"))
        r2 = self.rt.revise_counterexample_applicability(
            "d", ce.counterexample_id, applicability={"environment_revision": "windows"},
            status="ACTIVE", expected_revision=1, principal="alice",
        )
        self.assertEqual((r2.revision, r2.predecessor_revision), (2, 1))
        with self.assertRaises(MemoryWriteConflict):
            self.rt.revise_counterexample_applicability(
                "d", ce.counterexample_id, applicability={}, status="ACTIVE",
                expected_revision=1, principal="alice",
            )


if __name__ == "__main__":
    unittest.main()
