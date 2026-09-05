import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryAmbiguousSuccessors, MemoryDependencyStale, MemoryProposalStale
from nolane_memory.types import LossState


class FullSpecSeamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("X", {"x"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_strong_negative_distinguishes_complete_partial_and_phantom_invalidation(self):
        complete = self.rt.strong_negative_query("d", principal="alice", field="kind", equals="failure", completeness="COMPLETE")
        self.assertEqual(complete.status, "NO_MATCH_COMPLETE_DOMAIN")
        partial = self.rt.strong_negative_query("d", principal="alice", field="kind", equals="failure", completeness="PARTIAL")
        self.assertEqual(partial.status, "NO_MATCH_PARTIAL_DOMAIN")
        region = self.rt.create_region("d", "failure", principal="alice")
        self.rt.add_representation("d", region, kind="failure", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_negative_query_receipt(complete.receipt_id)
        exists = self.rt.strong_negative_query("d", principal="alice", field="kind", equals="failure", completeness="COMPLETE")
        self.assertEqual(exists.status, "SUPPORT_FOR_EXISTENCE")

    def test_region_split_has_ambiguous_current_successors_and_merge_preserves_historical_handles(self):
        old = self.rt.create_region("d", "old", principal="alice")
        split = self.rt.split_region("d", old, ["left", "right"], principal="alice")
        self.assertEqual(len(split.successor_region_ids), 2)
        with self.assertRaises(MemoryAmbiguousSuccessors):
            self.rt.resolve_current_region("d", old)
        merged = self.rt.merge_regions("d", split.successor_region_ids, "merged", principal="alice")
        current_left = self.rt.resolve_current_region("d", split.successor_region_ids[0])
        self.assertEqual(current_left, merged.successor_region_ids[0])
        self.assertIsNotNone(self.rt.db.execute("SELECT 1 FROM regions WHERE region_id=?", (old,)).fetchone())

    def test_stale_representation_proposal_cannot_promote_after_source_invalidation(self):
        region = self.rt.create_region("d", "r", principal="alice")
        source = self.rt.add_representation("d", region, kind="raw", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10, principal="alice")
        proposal = self.rt.create_representation_proposal("d", region, source_representation_ids=[source],
            kind="summary", payload={"x": 1}, loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(),
            token_cost=2, principal="alice", transform_profile="summary:v1")
        self.rt.verify_representation_proposal("d", proposal.proposal_id, principal="alice",
            verifier_ref="deterministic:v1", coverage="PASS", preservation="PASS", faithfulness="PASS")
        self.rt.invalidate_representation("d", source, principal="alice")
        with self.assertRaises(MemoryProposalStale):
            self.rt.promote_representation_proposal(proposal.proposal_id, principal="alice")
        row = self.rt.db.execute("SELECT promoted_representation_id FROM representation_proposals WHERE proposal_id=?", (proposal.proposal_id,)).fetchone()
        self.assertIsNone(row[0])

    def test_unrelated_write_does_not_invalidate_proposal_dependency_lease(self):
        region = self.rt.create_region("d", "r", principal="alice")
        source = self.rt.add_representation("d", region, kind="raw", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10, principal="alice")
        proposal = self.rt.create_representation_proposal("d", region, source_representation_ids=[source],
            kind="summary", payload={"x": 1}, loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(),
            token_cost=2, principal="alice", transform_profile="summary:v1")
        self.rt.verify_representation_proposal("d", proposal.proposal_id, principal="alice",
            verifier_ref="deterministic:v1", coverage="PASS", preservation="PASS", faithfulness="PASS")
        other = self.rt.create_region("d", "unrelated", principal="alice")
        self.rt.add_representation("d", other, kind="other", payload={"x": 9},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice")
        promoted = self.rt.promote_representation_proposal(proposal.proposal_id, principal="alice")
        self.assertIsNotNone(promoted)


if __name__ == "__main__": unittest.main()
