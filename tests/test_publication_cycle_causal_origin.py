import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryPublicationBlocked
from nolane_memory.types import LossState


class PublicationCycleCausalOriginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        for d in ("a", "b", "c"):
            self.rt.create_domain(d)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _source_rep(self, domain, label, root):
        head = self.rt._head_row(domain)
        ev = self.rt.capture_evidence(
            domain_id=domain, operation_id=f"capture:{domain}:{label}", expected_seq=int(head["sequence"]),
            writer_epoch=int(head["writer_epoch"]), source_event_identity=f"event:{domain}:{label}",
            content={"x": label}, principal="alice", origin_roots=[root],
        ).object_id
        region = self.rt.create_region(domain, f"region:{label}", principal="alice")
        rep = self.rt.add_representation(
            domain, region, kind="raw", payload={"x": label}, source_evidence_ids=[ev],
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        return ev, rep

    def test_revoked_imported_root_cannot_be_republished_as_healthy_destination_memory(self):
        _, rep_a = self._source_rep("a", "root", "root:R")
        ab = self.rt.publish_representation("a", "b", rep_a, principal="alice", operation_id="a-b")
        region_b = self.rt.create_region("b", "import", principal="alice")
        rep_b = self.rt.add_representation(
            "b", region_b, kind="import", payload={"x": "root"}, source_evidence_ids=[ab.destination_evidence_id],
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.revoke_evidence("b", ab.destination_evidence_id, principal="alice")
        with self.assertRaises(MemoryPublicationBlocked):
            self.rt.publish_representation("b", "c", rep_b, principal="alice", operation_id="b-c-after-revoke")

    def test_section_393_cycle_campaign_preserves_roots_and_closes_causal_predecessors(self):
        report = self.rt.run_publication_cycle_acceptance_campaign(seed=393)
        self.assertTrue(report["passed"])
        self.assertEqual(report["fixture_count"], 5)
        self.assertEqual(report["failed"], 0)
        names = {x["fixture"] for x in report["outcomes"]}
        self.assertEqual(names, {
            "pure_cycle_no_independent_support_inflation", "one_root_cycle",
            "two_independent_root_merge", "destination_revocation",
            "downstream_cut_omits_predecessor",
        })


if __name__ == "__main__":
    unittest.main()
