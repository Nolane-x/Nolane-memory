import tempfile
import unittest
from datetime import datetime, timezone

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryRecoveryBlocked, MemoryTransitionIncomplete


class RecoveryPrivacyClosureExtendedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})
        self.rt.set_runtime_compatibility("d", mission_revision="m1", environment_revision="e1")
        self.rt.set_self_version("d", "self:v1", {"tool": "t1"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _source_rep(self, event="evt", value=1, key="r"):
        h = self.rt._head_row("d")
        ev = self.rt.capture_evidence(
            domain_id="d", operation_id=f"op:{event}", expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), source_event_identity=event,
            content={"x": value, "private": f"secret-{value}"}, principal="alice",
        ).object_id
        region = self.rt.create_region("d", key, principal="alice")
        rep = self.rt.add_representation(
            "d", region, kind="raw", payload={"x": value, "private": f"secret-{value}"},
            loss={"x": LossState.PRESERVED_EXACT, "private": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=2, principal="alice", source_evidence_ids=[ev],
        )
        return ev, region, rep

    def test_pin_selection_ignores_serialized_order_and_chooses_latest_usable(self):
        _, region, rep = self._source_rep()
        role = RecallRole("x", region, "X", hard=True)
        older = self.rt.create_continuity_pin("d", principal="alice", hard_roles=[role], stable_refs=[rep])
        # Newer pin is deliberately blocked; it must not win simply because it is newest/list-first.
        newer = self.rt.create_continuity_pin(
            "d", principal="alice", hard_roles=[role], stable_refs=[rep], verification_blockers=["verify:open"]
        )
        selected = self.rt.select_continuity_pin("d", principal="alice", pin_ids=[newer.pin_id, older.pin_id])
        self.assertEqual(selected.pin_id, older.pin_id)
        selected2 = self.rt.select_continuity_pin("d", principal="alice", pin_ids=[older.pin_id, newer.pin_id])
        self.assertEqual(selected2.pin_id, older.pin_id)

    def test_erasure_invalidates_handoff_and_current_validation_blocks_deleted_content(self):
        ev, region, _ = self._source_rep(event="private")
        role = RecallRole("x", region, "X", hard=True)
        packet = self.rt.create_handoff_packet("d", principal="alice", hard_roles=[role], token_budget=20)
        before = self.rt.validate_handoff_packet(packet.packet_id, principal="alice")
        self.assertEqual(before["status"], "USABLE")
        receipt = self.rt.erase_evidence("d", ev, principal="alice", policy_ref="privacy:delete")
        self.assertIn(packet.packet_id, receipt.invalidated_handoff_packet_ids)
        after = self.rt.validate_handoff_packet(packet.packet_id, principal="alice")
        self.assertEqual(after["status"], "BLOCKED_BY_GOVERNANCE")

    def test_advisory_next_action_never_survives_changed_tool_boundary_as_resume_authority(self):
        _, region, _ = self._source_rep(event="tool")
        role = RecallRole("x", region, "X", hard=True)
        packet = self.rt.create_handoff_packet(
            "d", principal="alice", hard_roles=[role], token_budget=20,
            advisory_next_action={"tool": "pay", "amount": 10}, tool_boundary_digest="tool-schema:v1",
        )
        same = self.rt.validate_handoff_packet(packet.packet_id, principal="alice", current_tool_boundary_digest="tool-schema:v1")
        self.assertTrue(same["hard_roles_usable"])
        self.assertTrue(same["advisory_action_usable"])
        changed = self.rt.validate_handoff_packet(packet.packet_id, principal="alice", current_tool_boundary_digest="tool-schema:v2")
        self.assertTrue(changed["hard_roles_usable"])
        self.assertFalse(changed["advisory_action_usable"])
        self.assertEqual(changed["status"], "REVALIDATION_REQUIRED")

    def test_missing_governance_barrier_ledger_blocks_recovery_fail_closed(self):
        _, region, rep = self._source_rep(event="barrier")
        pin = self.rt.create_continuity_pin("d", principal="alice", hard_roles=[RecallRole("x", region, "X")], stable_refs=[rep])
        assessment = self.rt.assess_recovery("d", pin_id=pin.pin_id, principal="alice", barrier_ledger_complete=False)
        self.assertFalse(assessment.resume_allowed)
        self.assertEqual(assessment.layers["R3_NON_REVIVAL_BARRIER"], "BLOCKED")

    def test_mission_scoped_claim_becomes_currently_unusable_after_mission_change(self):
        ev, _, _ = self._source_rep(event="claim")
        h = self.rt._head_row("d")
        claim = self.rt.create_claim(
            domain_id="d", operation_id="claim-create", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="mission:fact", proposition={"goal": "A"}, valid_from=None, valid_to=None,
            support_paths=[[ev]], principal="alice", applicability={"mission_revision": "m1"},
        )
        self.assertTrue(self.rt.claim_currently_usable("d", "mission:fact", principal="alice"))
        self.rt.set_runtime_compatibility("d", mission_revision="m2", environment_revision="e1")
        self.assertFalse(self.rt.claim_currently_usable("d", "mission:fact", principal="alice"))
        old = self.rt.get_claim_revision("d", claim.object_id)
        self.assertEqual(old["applicability"], {"mission_revision": "m1"})

    def test_semantic_rollback_cannot_bypass_later_erasure_barrier(self):
        ev, _, _ = self._source_rep(event="rollback")
        h = self.rt._head_row("d")
        c1 = self.rt.create_claim(
            domain_id="d", operation_id="c1", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="pref", proposition={"v": 1}, valid_from=None, valid_to=None,
            support_paths=[[ev]], principal="alice",
        )
        h = self.rt._head_row("d")
        c2 = self.rt.revise_claim(
            domain_id="d", operation_id="c2", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="pref", expected_predecessor_revision_id=c1.object_id, proposition={"v": 2},
            valid_from=None, valid_to=None, support_paths=[[ev]], principal="alice",
        )
        self.rt.erase_evidence("d", ev, principal="alice", policy_ref="privacy:delete")
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.rollback_claim_to_revision("d", "pref", c1.object_id, principal="alice", operation_id="rollback-to-c1")
        self.assertEqual(self.rt.get_claim_revision("d", c2.object_id)["proposition"], {"v": 2})


if __name__ == "__main__": unittest.main()
