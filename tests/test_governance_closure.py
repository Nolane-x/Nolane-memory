import tempfile
import unittest
from datetime import datetime, timezone

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryRecallInsufficient, MemoryTransitionIncomplete


class GovernanceClosureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.rt=MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d"); self.rt.register_query_family("X", {"x"})

    def tearDown(self): self.rt.close(); self.tmp.cleanup()

    def _ev(self, op, sid, content, roots=None):
        h=self.rt._head_row("d")
        return self.rt.capture_evidence(domain_id="d",operation_id=op,expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),source_event_identity=sid,content=content,principal="alice",origin_roots=roots).object_id

    def test_historical_judgement_survives_later_evidence_revocation(self):
        ev=self._ev("e1","s1",{"x":1})
        h=self.rt._head_row("d")
        claim=self.rt.create_claim(domain_id="d",operation_id="c1",expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),logical_id="claim-x",proposition={"x":1},valid_from=None,valid_to=None,support_paths=[[ev]],principal="alice").object_id
        j=self.rt.record_historical_judgement("d",claim_revision_id=claim,principal="alice",judgement="ACCEPTED",reason="evidence-at-time")
        self.rt.revoke_evidence("d",ev,principal="alice")
        self.assertFalse(self.rt.claim_is_supported("d","claim-x"))
        got=self.rt.list_historical_judgements("d",principal="alice")
        self.assertEqual(got[0].judgement,"ACCEPTED")
        self.assertEqual(got[0].cut.sequence,j.cut.sequence)

    def test_origin_copies_do_not_create_independent_support(self):
        roots=["upstream:one"]
        e1=self._ev("a","a",{"x":1},roots); e2=self._ev("b","b",{"x":1},roots)
        result=self.rt.evaluate_evidence_independence("d",[e1,e2])
        self.assertEqual(result["independent_root_count"],1)
        self.assertEqual(result["dependence"],"DEPENDENT")

    def test_transform_contract_forbids_declared_loss(self):
        self.rt.register_transformation_contract("summary:safety",revision=1,transform_kind="PURE",protected_dimensions={"x"},forbidden_loss={"x"})
        r=self.rt.create_region("d","r",principal="alice")
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.add_representation("d",r,kind="summary",payload={"text":"lost"},loss={"x":LossState.LOST},recoverable=set(),token_cost=1,principal="alice",transform_profile="summary:safety")

    def test_source_compromise_preserves_history_but_blocks_current_representation(self):
        ev=self._ev("e","source",{"x":1})
        r=self.rt.create_region("d","r",principal="alice")
        rep=self.rt.add_representation("d",r,kind="raw",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice",source_evidence_ids=[ev])
        self.rt.compromise_evidence("d",ev,principal="alice",reason="key-compromise")
        row=self.rt.db.execute("SELECT invalidated_seq FROM representations WHERE representation_id=?",(rep,)).fetchone()
        self.assertIsNotNone(row[0])
        with self.assertRaises(MemoryRecallInsufficient):
            self.rt.compile_recall("d","alice",[RecallRole("x",r,"X")],10)
        self.assertIsNotNone(self.rt.db.execute("SELECT evidence_id FROM evidence WHERE evidence_id=?",(ev,)).fetchone())

    def test_applicability_executes_against_current_environment(self):
        self.rt.set_runtime_compatibility("d",mission_revision="m1",environment_revision="linux")
        r=self.rt.create_region("d","proc",principal="alice")
        self.rt.add_representation("d",r,kind="procedure",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice",applicability={"environment_revision":"linux","mission_revision":"m1"})
        self.assertEqual(self.rt.compile_recall("d","alice",[RecallRole("p",r,"X")],10).sufficiency,"SUFFICIENT")
        self.rt.set_runtime_compatibility("d",mission_revision="m1",environment_revision="windows")
        with self.assertRaises(MemoryRecallInsufficient):
            self.rt.compile_recall("d","alice",[RecallRole("p",r,"X")],10)

if __name__ == '__main__': unittest.main()
