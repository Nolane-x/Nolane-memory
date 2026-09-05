import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime
from nolane_memory.errors import MemoryPublicationBlocked


class PublicationSagaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.rt=MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("a"); self.rt.create_domain("b")
        r=self.rt.create_region("a","r",principal="alice")
        self.rep=self.rt.add_representation("a",r,kind="structured",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice")

    def tearDown(self): self.rt.close(); self.tmp.cleanup()

    def test_source_change_during_pending_publication_blocks_destination_admission(self):
        saga=self.rt.prepare_publication("a","b",self.rep,principal="alice",operation_id="p1")
        self.assertEqual(saga["state"],"DEST_PENDING")
        self.rt.invalidate_representation("a",self.rep,principal="alice")
        with self.assertRaises(MemoryPublicationBlocked):
            self.rt.complete_publication(saga["saga_id"],accept=True)
        state=self.rt.get_publication_saga(saga["saga_id"])
        self.assertEqual(state["state"],"SOURCE_REVALIDATION_REQUIRED")
        self.assertIsNone(state["destination_evidence_id"])

    def test_destination_rejection_does_not_rollback_source(self):
        saga=self.rt.prepare_publication("a","b",self.rep,principal="alice",operation_id="p2")
        result=self.rt.complete_publication(saga["saga_id"],accept=False,reason="destination-policy")
        self.assertEqual(result["state"],"DEST_REJECTED")
        source=self.rt.db.execute("SELECT invalidated_seq FROM representations WHERE representation_id=?",(self.rep,)).fetchone()
        self.assertIsNone(source[0])

    def test_admitted_publication_records_causal_edge_and_preserves_origins(self):
        saga=self.rt.prepare_publication("a","b",self.rep,principal="alice",operation_id="p3")
        pub=self.rt.complete_publication(saga["saga_id"],accept=True)
        self.assertEqual(pub.destination_domain,"b")
        state=self.rt.get_publication_saga(saga["saga_id"])
        self.assertEqual(state["state"],"DEST_ADMITTED")
        edge=self.rt.db.execute("SELECT 1 FROM causal_edges WHERE src_domain='a' AND src_seq=? AND dst_domain='b' AND dst_seq=?",(state["source_sequence"],state["destination_sequence"])).fetchone()
        self.assertIsNotNone(edge)

if __name__ == '__main__': unittest.main()
