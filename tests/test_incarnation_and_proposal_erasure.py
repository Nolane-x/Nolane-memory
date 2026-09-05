import tempfile
import unittest

from nolane_memory import LossState, RecallRole, MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale, MemoryProposalStale


class IncarnationAndProposalErasureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d", writer_epoch=1, incarnation=1)
        self.rt.register_query_family("X", {"x"})

    def tearDown(self):
        self.rt.close()
        self.tmp.cleanup()

    def test_new_incarnation_invalidates_old_frame_and_scopes_idempotency_receipts(self):
        head0 = self.rt._head_row("d")
        old_receipt = self.rt.capture_evidence(
            domain_id="d", operation_id="same-op", expected_seq=int(head0["sequence"]),
            writer_epoch=int(head0["writer_epoch"]), source_event_identity="event-old-inc",
            content={"x": 0}, principal="alice",
        )
        self.assertEqual(old_receipt.incarnation, 1)
        region = self.rt.create_region("d", "r", principal="alice")
        self.rt.add_representation(
            "d", region, kind="structured", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        frame = self.rt.compile_recall("d", "alice", [RecallRole("x", region, "X")], 10)
        old_cut = frame.cut
        new_cut = self.rt.start_new_incarnation("d", principal="alice", reason="restore")
        self.assertEqual(new_cut.incarnation, old_cut.incarnation + 1)
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_dependencies("d", frame.dependencies)

        head = self.rt._head_row("d")
        r1 = self.rt.capture_evidence(
            domain_id="d", operation_id="same-op", expected_seq=int(head["sequence"]),
            writer_epoch=int(head["writer_epoch"]), source_event_identity="event-new-inc",
            content={"x": 1}, principal="alice",
        )
        self.assertEqual(r1.incarnation, new_cut.incarnation)
        # Reuse of an operation id that existed in a previous incarnation is legal;
        # idempotency is scoped to the active incarnation, not human-readable domain id.
        self.assertGreaterEqual(r1.commit_seq, new_cut.sequence + 1)

    def test_erasure_scrubs_and_invalidates_pending_derivative_proposals(self):
        head = self.rt._head_row("d")
        ev = self.rt.capture_evidence(
            domain_id="d", operation_id="capture-secret", expected_seq=int(head["sequence"]),
            writer_epoch=int(head["writer_epoch"]), source_event_identity="secret-source",
            content={"secret": "NEVER-RETAIN-ME"}, principal="alice",
        ).object_id
        region = self.rt.create_region("d", "private", principal="alice")
        source = self.rt.add_representation(
            "d", region, kind="raw", payload={"x": "NEVER-RETAIN-ME"},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice",
            source_evidence_ids=[ev],
        )
        proposal = self.rt.create_representation_proposal(
            "d", region, source_representation_ids=[source], kind="summary",
            payload={"x": "NEVER-RETAIN-ME"}, loss={"x": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.verify_representation_proposal(
            "d", proposal.proposal_id, principal="alice", verifier_ref="deterministic:v1",
            coverage="PASS", preservation="PASS", faithfulness="PASS",
        )
        self.rt.erase_evidence("d", ev, principal="alice", policy_ref="privacy-delete")
        row = self.rt.db.execute(
            "SELECT payload_json,invalidated_seq FROM representation_proposals WHERE proposal_id=?",
            (proposal.proposal_id,),
        ).fetchone()
        self.assertIsNotNone(row["invalidated_seq"])
        self.assertNotIn("NEVER-RETAIN-ME", row["payload_json"])
        with self.assertRaises(MemoryProposalStale):
            self.rt.promote_representation_proposal(proposal.proposal_id, principal="alice")

    def test_incarnation_transition_is_idempotent_across_lost_response_retry(self):
        first = self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="restore-1")
        second = self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="restore-1")
        self.assertEqual(first, second)
        self.assertEqual(self.rt.head("d").incarnation, 2)


if __name__ == "__main__":
    unittest.main()
