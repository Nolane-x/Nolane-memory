import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryRecallInsufficient, MemoryViewOverflow
from nolane_memory.types import LossState, RecallRole, RecoveryLayerStatus


class K4ContinuityErasureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("EXACT", {"x"})
        self.rt.set_runtime_compatibility("d", mission_revision="m1", environment_revision="env1")
        self.rt.set_self_version("d", "self:v1", {"toolset": "t1"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _evidence_rep(self, event, x, region_key):
        h = self.rt.head("d")
        ev = self.rt.capture_evidence(domain_id="d", operation_id=f"op-{event}", expected_seq=h.sequence,
            writer_epoch=1, source_event_identity=event, content={"x": x}, principal="alice")
        region = self.rt.create_region("d", region_key, principal="alice")
        rep = self.rt.add_representation("d", region, kind="structured", payload={"x": x},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2,
            principal="alice", source_evidence_ids=[ev.object_id])
        return ev.object_id, region, rep

    def test_erasure_taints_derivatives_invalidates_pin_and_blocks_current_recall(self):
        eid, region, rep = self._evidence_rep("private:1", 7, "r1")
        role = RecallRole("hard-x", region, "EXACT", hard=True)
        pin = self.rt.create_continuity_pin("d", principal="alice", hard_roles=[role], stable_refs=[eid, rep])
        receipt = self.rt.erase_evidence("d", eid, principal="alice", policy_ref="privacy:delete")
        self.assertEqual(receipt.status, "CURRENT_ERASURE_CLOSED")
        self.assertIn(rep, receipt.tainted_representation_ids)
        self.assertIn(pin.pin_id, receipt.invalidated_continuity_pin_ids)
        with self.assertRaises(MemoryRecallInsufficient):
            self.rt.compile_recall("d", "alice", [role], 20)
        assessment = self.rt.assess_recovery("d", pin_id=pin.pin_id, principal="alice")
        self.assertFalse(assessment.resume_allowed)
        self.assertEqual(assessment.layers["R3_NON_REVIVAL_BARRIER"], RecoveryLayerStatus.BLOCKED.value)

    def test_forged_pin_payload_is_not_resume_authority(self):
        eid, region, rep = self._evidence_rep("event:1", 1, "r1")
        pin = self.rt.create_continuity_pin("d", principal="alice", hard_roles=[], stable_refs=[eid, rep])
        self.rt.db.execute("UPDATE continuity_pins SET state_digest='forged' WHERE pin_id=?", (pin.pin_id,))
        assessment = self.rt.assess_recovery("d", pin_id=pin.pin_id, principal="alice")
        self.assertFalse(assessment.resume_allowed)
        self.assertEqual(assessment.layers["R4_CONTINUITY_COMPATIBILITY"], RecoveryLayerStatus.BLOCKED.value)

    def test_old_pin_requires_compatibility_after_mission_change(self):
        _, _, rep = self._evidence_rep("event:2", 2, "r2")
        pin = self.rt.create_continuity_pin("d", principal="alice", hard_roles=[], stable_refs=[rep])
        self.rt.set_runtime_compatibility("d", mission_revision="m2", environment_revision="env1")
        assessment = self.rt.assess_recovery("d", pin_id=pin.pin_id, principal="alice")
        self.assertFalse(assessment.resume_allowed)
        self.assertEqual(assessment.layers["R4_CONTINUITY_COMPATIBILITY"], RecoveryLayerStatus.BLOCKED.value)

    def test_clean_rederivation_requires_surviving_source_and_creates_new_bytes(self):
        private, region, old = self._evidence_rep("private:2", 9, "same")
        h = self.rt.head("d")
        public = self.rt.capture_evidence(domain_id="d", operation_id="public", expected_seq=h.sequence,
            writer_epoch=1, source_event_identity="public:2", content={"x": 9}, principal="alice").object_id
        # old derivative used both sources and becomes tainted when the private source is erased
        old2 = self.rt.add_representation("d", region, kind="summary", payload={"x": 9, "detail": "private"},
            source_representation_ids=[old], source_evidence_ids=[private, public], transform_kind="SOURCE_REBASE",
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=3, principal="alice")
        self.rt.erase_evidence("d", private, principal="alice", policy_ref="privacy:delete")
        clean = self.rt.clean_rederive("d", old2, surviving_evidence_ids=[public], payload={"x": 9},
            loss={"x": LossState.PRESERVED_EXACT}, principal="alice")
        old_row = self.rt.db.execute("SELECT tainted_seq FROM representations WHERE representation_id=?", (old2,)).fetchone()
        clean_row = self.rt.db.execute("SELECT tainted_seq,source_evidence_ids_json FROM representations WHERE representation_id=?", (clean,)).fetchone()
        self.assertIsNotNone(old_row[0])
        self.assertIsNone(clean_row[0])
        self.assertNotEqual(old2, clean)
        self.assertIn(public, clean_row[1])

    def test_handoff_preserves_all_hard_roles_or_overflows(self):
        roles = []
        for i in range(3):
            _, region, _ = self._evidence_rep(f"event:{10+i}", i, f"r{10+i}")
            roles.append(RecallRole(f"hard-{i}", region, "EXACT", hard=True))
        with self.assertRaises(MemoryViewOverflow):
            self.rt.create_handoff_packet("d", principal="alice", hard_roles=roles, token_budget=4)
        packet = self.rt.create_handoff_packet("d", principal="alice", hard_roles=roles, token_budget=10)
        self.assertEqual({f.role_id for f in packet.fragments}, {r.role_id for r in roles})


if __name__ == "__main__": unittest.main()
