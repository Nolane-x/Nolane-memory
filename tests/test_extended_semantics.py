import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import LossState, RecallRole
from nolane_memory.errors import MemoryDependencyStale


class ExtendedSemanticTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_or_of_and_justification_keeps_claim_supported_while_alternative_path_lives(self):
        e1 = self.rt.capture_evidence(domain_id="d", operation_id="e1", expected_seq=0, writer_epoch=1,
                                      source_event_identity="e1", content={"v": 1}, principal="alice")
        e2 = self.rt.capture_evidence(domain_id="d", operation_id="e2", expected_seq=1, writer_epoch=1,
                                      source_event_identity="e2", content={"v": 2}, principal="alice")
        e3 = self.rt.capture_evidence(domain_id="d", operation_id="e3", expected_seq=2, writer_epoch=1,
                                      source_event_identity="e3", content={"v": 3}, principal="alice")
        self.rt.create_claim(domain_id="d", operation_id="c1", expected_seq=3, writer_epoch=1,
                             logical_id="claim", proposition={"ok": True}, valid_from=None, valid_to=None,
                             support_paths=[[e1.object_id, e2.object_id], [e3.object_id]], principal="alice")
        self.assertTrue(self.rt.claim_is_supported("d", "claim"))
        self.rt.revoke_evidence("d", e2.object_id, principal="alice")
        self.assertTrue(self.rt.claim_is_supported("d", "claim"))
        self.rt.revoke_evidence("d", e3.object_id, principal="alice")
        self.assertFalse(self.rt.claim_is_supported("d", "claim"))

    def test_policy_generation_change_invalidates_frame_before_fence_issue(self):
        self.rt.register_query_family("PREF", {"polarity"})
        region = self.rt.create_region("d", "r", principal="alice")
        self.rt.add_representation("d", region, kind="exact", payload={"polarity": "yes"},
                                   loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(),
                                   token_cost=2, principal="alice")
        frame = self.rt.compile_recall("d", "alice", [RecallRole("pref", region, "PREF")], 10)
        self.rt.bump_generation("d", "policy", "global")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"x": 1})

    def test_tool_generation_is_sink_scoped_at_use_time(self):
        self.rt.register_query_family("PREF", {"polarity"})
        region = self.rt.create_region("d", "r", principal="alice")
        self.rt.add_representation("d", region, kind="exact", payload={"polarity": "yes"},
                                   loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(),
                                   token_cost=2, principal="alice")
        frame = self.rt.compile_recall("d", "alice", [RecallRole("pref", region, "PREF")], 10)
        fence = self.rt.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"x": 1})
        self.rt.bump_generation("d", "tool", "tool:other")
        self.assertTrue(self.rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:send", payload={"x": 1}))

        frame2 = self.rt.compile_recall("d", "alice", [RecallRole("pref", region, "PREF")], 10)
        fence2 = self.rt.issue_use_fence(frame2, principal="alice", sink="tool:send", payload={"x": 1})
        self.rt.bump_generation("d", "tool", "tool:send")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.consume_use_fence(fence2.fence_id, principal="alice", sink="tool:send", payload={"x": 1})

    def test_causal_cut_closes_destination_over_source_predecessor(self):
        self.rt.create_domain("a", writer_epoch=1)
        a1 = self.rt.capture_evidence(domain_id="a", operation_id="a1", expected_seq=0, writer_epoch=1,
                                      source_event_identity="a1", content={"a": 1}, principal="alice")
        b1 = self.rt.capture_evidence(domain_id="d", operation_id="b1", expected_seq=0, writer_epoch=1,
                                      source_event_identity="b1", content={"b": 1}, principal="alice")
        self.rt.add_causal_edge("a", a1.commit_seq, "d", b1.commit_seq)
        cut = self.rt.close_causal_cut({"d": b1.commit_seq})
        self.assertEqual(cut["a"].sequence, a1.commit_seq)
        self.assertEqual(cut["d"].sequence, b1.commit_seq)


if __name__ == "__main__": unittest.main()

class CutConsistencyTests(unittest.TestCase):
    def test_nested_reads_stay_on_pinned_sqlite_snapshot(self):
        tmp = tempfile.TemporaryDirectory()
        path = f"{tmp.name}/memory.db"
        rt1 = MemoryRuntime(path)
        rt1.create_domain("d", writer_epoch=1)
        rt1.register_query_family("PREF", {"polarity"})
        region = rt1.create_region("d", "r", principal="alice")
        rep = rt1.add_representation("d", region, kind="exact", payload={"polarity": "yes"},
                                     loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(),
                                     token_cost=2, principal="alice")
        rt2 = MemoryRuntime(path)
        original = rt1._resolve_role
        fired = {"v": False}

        def interleaved(*args, **kwargs):
            if not fired["v"]:
                fired["v"] = True
                rt2.invalidate_representation("d", rep, principal="alice")
            return original(*args, **kwargs)

        rt1._resolve_role = interleaved
        try:
            frame = rt1.compile_recall("d", "alice", [RecallRole("pref", region, "PREF")], 10)
            self.assertEqual(frame.fragments[0].representation_id, rep)
            with self.assertRaises(MemoryDependencyStale):
                rt1.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"x": 1})
        finally:
            rt1.close(); rt2.close(); tmp.cleanup()
