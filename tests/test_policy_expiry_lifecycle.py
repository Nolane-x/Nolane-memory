import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryPublicationBlocked, MemoryRecallInsufficient, MemoryTransitionIncomplete
from nolane_memory.types import FlowDecision


class PolicyExpiryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2035, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db", clock=lambda: self.now)
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_access_profile_expiry_is_enforced_by_recall_reader(self):
        self.rt.register_query_family("X", {"x"})
        region = self.rt.create_region("d", "r", principal="alice")
        self.rt.add_representation(
            "d", region, kind="raw", payload={"x": 1}, loss={"x": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.set_access_profile(
            "d", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING"}, expires_at=self.now + timedelta(minutes=5)
        )
        self.assertEqual(self.rt.compile_recall("d", "alice", [RecallRole("x", region, "X")], 10).sufficiency, "SUFFICIENT")
        self.now += timedelta(minutes=6)
        with self.assertRaises(MemoryRecallInsufficient):
            self.rt.compile_recall("d", "alice", [RecallRole("x", region, "X")], 10)

    def test_declassification_expiry_closes_disclosure_without_revoke_event(self):
        self.rt.register_query_family("X", {"x"})
        region = self.rt.create_region("d", "r", principal="alice")
        rep = self.rt.add_representation(
            "d", region, kind="raw", payload={"x": 1}, loss={"x": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.set_access_profile("d", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"})
        frame = self.rt.compile_recall("d", "alice", [RecallRole("x", region, "X")], 10)
        self.rt.grant_declassification(
            "d", rep, principal="alice", sink="tool:external", authority_ref="release:1",
            expires_at=self.now + timedelta(minutes=1),
        )
        self.assertEqual(self.rt.check_information_flow(frame, principal="alice", sink="tool:external", payload={"x": 1}).decision, FlowDecision.ALLOW.value)
        self.now += timedelta(minutes=2)
        self.assertEqual(self.rt.check_information_flow(frame, principal="alice", sink="tool:external", payload={"x": 1}).decision, FlowDecision.BLOCK.value)

    def test_expired_integrity_authority_profile_fails_closed(self):
        self.rt.register_integrity_authority_profile(
            "d", profile_id="critical", revision=1, issuer="gov", subject_ids={"claim"},
            operations={"CREATE_CLAIM"}, accepted_authority_classes={"TRUSTED_FACT"}, enabled=True,
            expires_at=self.now + timedelta(minutes=1),
        )
        h = self.rt._head_row("d")
        ev = self.rt.capture_evidence(
            domain_id="d", operation_id="e", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            source_event_identity="evt", content={"x": 1}, principal="alice", source_authority_class="TRUSTED_FACT",
        ).object_id
        self.now += timedelta(minutes=2)
        h = self.rt._head_row("d")
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.create_claim(
                domain_id="d", operation_id="c", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
                logical_id="claim", proposition={"x": 1}, valid_from=None, valid_to=None,
                support_paths=[[ev]], principal="alice",
            )

    def test_expired_publication_policy_blocks_prepare(self):
        self.rt.create_domain("a"); self.rt.create_domain("b")
        region = self.rt.create_region("a", "r", principal="alice")
        rep = self.rt.add_representation(
            "a", region, kind="raw", payload={"x": 1}, loss={"x": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.register_publication_policy(
            "a", "b", policy_id="share", revision=1, issuer="gov", allow=True,
            allowed_principals={"alice"}, preserve_origin=True, expires_at=self.now + timedelta(minutes=1),
        )
        self.now += timedelta(minutes=2)
        with self.assertRaises(MemoryPublicationBlocked):
            self.rt.prepare_publication("a", "b", rep, principal="alice", operation_id="p")


if __name__ == "__main__":
    unittest.main()
