import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import FlowDecision, LossState, RecallRole


class K4SecurityFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("src", writer_epoch=1)
        self.rt.register_query_family("PREF", {"polarity"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _frame_with_rep(self, allowed=None):
        region = self.rt.create_region("src", "r" + str(self.rt.head("src").sequence), principal="alice", allowed_principals=allowed)
        rep = self.rt.add_representation(
            "src", region, kind="exact", payload={"polarity": "yes"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2,
            principal="alice", allowed_principals=allowed)
        frame = self.rt.compile_recall("src", "alice", [RecallRole("pref", region, "PREF")], 20)
        return region, rep, frame

    def test_local_reasoning_permission_does_not_imply_tool_disclosure(self):
        self.rt.set_access_profile("src", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"})
        _, rep, frame = self._frame_with_rep()
        receipt = self.rt.check_information_flow(frame, principal="alice", sink="tool:external", payload={"memory": "yes"})
        self.assertEqual(receipt.decision, FlowDecision.BLOCK.value)
        self.assertIn(rep, receipt.blocked_or_rewritten_fragment_refs)
        self.assertEqual(receipt.hard_roles_affected, ["pref"])

    def test_declassification_can_widen_disclosure_then_revocation_closes_it(self):
        self.rt.set_access_profile("src", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"})
        _, rep, frame = self._frame_with_rep()
        dec = self.rt.grant_declassification("src", rep, principal="alice", sink="tool:external", authority_ref="release:7")
        allowed = self.rt.check_information_flow(frame, principal="alice", sink="tool:external", payload={"memory": "yes"})
        self.assertEqual(allowed.decision, FlowDecision.ALLOW.value)
        self.assertEqual(allowed.declassification_receipt_refs, [dec.receipt_id])
        self.rt.revoke_declassification("src", dec.receipt_id, principal="alice")
        blocked = self.rt.check_information_flow(frame, principal="alice", sink="tool:external", payload={"memory": "yes"})
        self.assertEqual(blocked.decision, FlowDecision.BLOCK.value)

    def test_composed_policy_can_block_authorized_atoms(self):
        self.rt.set_access_profile(
            "src", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE", "DISCLOSE_TO_TOOL"},
            sink_capabilities={"tool:external": ["DISCLOSE_TO_TOOL"]})
        r1 = self.rt.create_region("src", "a", principal="alice")
        r2 = self.rt.create_region("src", "b", principal="alice")
        a = self.rt.add_representation("src", r1, kind="exact", payload={"polarity": "yes"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")
        b = self.rt.add_representation("src", r2, kind="exact", payload={"polarity": "no"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")
        self.rt.register_flow_policy("src", "fusion-secret", sink="tool:external", forbidden_representation_sets=[{a, b}])
        frame = self.rt.compile_recall("src", "alice", [RecallRole("a", r1, "PREF"), RecallRole("b", r2, "PREF")], 20)
        receipt = self.rt.check_information_flow(frame, principal="alice", sink="tool:external", payload={"a": 1, "b": 2})
        self.assertEqual(receipt.decision, FlowDecision.BLOCK.value)
        self.assertIn("policy:fusion-secret", receipt.policy_checks)

    def test_publication_preserves_root_origins_and_adds_causal_dependency(self):
        self.rt.create_domain("dst", writer_epoch=1)
        self.rt.set_access_profile("src", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE", "PUBLISH_TO_DOMAIN"})
        ev = self.rt.capture_evidence(
            domain_id="src", operation_id="e1", expected_seq=self.rt.head("src").sequence, writer_epoch=1,
            source_event_identity="sensor:1", content={"polarity": "yes"}, principal="alice")
        region = self.rt.create_region("src", "pub", principal="alice")
        rep = self.rt.add_representation("src", region, kind="structured", payload={"polarity": "yes"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice",
            source_evidence_ids=[ev.object_id])
        roots_before = self.rt.get_origin_roots("src", "evidence", ev.object_id)
        pub = self.rt.publish_representation("src", "dst", rep, principal="alice", operation_id="pub-1")
        roots_after = self.rt.get_origin_roots("dst", "evidence", pub.destination_evidence_id)
        self.assertEqual(roots_after, roots_before)
        cut = self.rt.close_causal_cut({"dst": pub.destination_sequence})
        self.assertGreaterEqual(cut["src"].sequence, pub.source_sequence)

    def test_use_fence_cannot_bypass_flow_gate_and_revocation_invalidates_issued_fence(self):
        from nolane_memory.errors import MemoryDependencyStale, MemoryFlowBlocked
        self.rt.set_access_profile("src", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"})
        _, rep, frame = self._frame_with_rep()
        with self.assertRaises(MemoryFlowBlocked):
            self.rt.issue_use_fence(frame, principal="alice", sink="tool:external", payload={"memory": "yes"})
        dec = self.rt.grant_declassification("src", rep, principal="alice", sink="tool:external", authority_ref="release:9")
        fence = self.rt.issue_use_fence(frame, principal="alice", sink="tool:external", payload={"memory": "yes"})
        self.rt.revoke_declassification("src", dec.receipt_id, principal="alice")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:external", payload={"memory": "yes"})


if __name__ == "__main__": unittest.main()
