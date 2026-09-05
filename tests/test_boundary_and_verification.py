import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryTransitionIncomplete, MemoryViewOverflow
from nolane_memory.types import LossState, RecallBoundaryDescriptor, RecallRole


class BoundaryAndVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.rt=MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d",writer_epoch=1); self.rt.register_query_family("X",{"x"})

    def tearDown(self): self.rt.close(); self.tmp.cleanup()

    def _rep(self,key,value,**kwargs):
        r=self.rt.create_region("d",key,principal="alice")
        rep=self.rt.add_representation("d",r,kind=kwargs.pop("kind","structured"),payload={"x":value},
            loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=kwargs.pop("token_cost",1),principal="alice",**kwargs)
        return r,rep

    def test_action_boundary_roles_are_hard_even_without_explicit_query(self):
        region,_=self._rep("recipient",1)
        boundary=RecallBoundaryDescriptor(task="send",principal="alice",action_tool_roles=[RecallRole("recipient",region,"X",False)],token_budget=10)
        frame,obligation=self.rt.compile_boundary_recall("d",boundary)
        self.assertEqual([r.role_id for r in obligation.hard_roles],["recipient"])
        self.assertEqual(frame.fragments[0].role_id,"recipient")

    def test_page_fault_exposes_new_hard_dependency_and_cycles_deduplicate(self):
        dep_region,_=self._rep("dep",2)
        main_region=self.rt.create_region("d","main",principal="alice")
        dep=RecallRole("dep",dep_region,"X",True)
        main=RecallRole("main",main_region,"X",True)
        # Main exact representation reveals dep; dependency representation points back to main, forming a cycle.
        self.rt.add_representation("d",main_region,kind="structured",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice",hard_dependencies=[dep])
        # Add a second representation in dep region with the back edge; ambiguity is avoided because x is same.
        self.rt.add_representation("d",dep_region,kind="structured",payload={"x":2},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice",hard_dependencies=[main])
        boundary=RecallBoundaryDescriptor(task="cyclic",principal="alice",explicit_roles=[main],token_budget=10)
        frame,obligation=self.rt.compile_boundary_recall("d",boundary)
        self.assertEqual({r.role_id for r in obligation.hard_roles},{"main","dep"})
        self.assertLessEqual(obligation.closure_iterations,3)
        self.assertEqual({f.role_id for f in frame.fragments},{"main","dep"})

    def test_page_fault_resource_budget_fails_visible(self):
        region=self.rt.create_region("d","rehyd",principal="alice")
        raw=self.rt.add_representation("d",region,kind="raw",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=10,principal="alice")
        self.rt.add_representation("d",region,kind="summary",payload={"text":"one"},source_representation_ids=[raw],loss={"x":LossState.LOST},recoverable={"x"},token_cost=1,principal="alice")
        b=RecallBoundaryDescriptor(task="exact",principal="alice",explicit_roles=[RecallRole("x",region,"X")],token_budget=20,page_fault_budget=0)
        with self.assertRaises(MemoryViewOverflow): self.rt.compile_boundary_recall("d",b)

    def test_unverified_proposal_cannot_promote_and_verified_proposal_can(self):
        region,source=self._rep("source",1,kind="raw")
        proposal=self.rt.create_representation_proposal("d",region,source_representation_ids=[source],kind="summary",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice")
        with self.assertRaises(MemoryTransitionIncomplete): self.rt.promote_representation_proposal(proposal.proposal_id,principal="alice")
        receipt=self.rt.verify_representation_proposal("d",proposal.proposal_id,principal="alice",verifier_ref="deterministic:v1",coverage="PASS",preservation="PASS",faithfulness="PASS")
        self.assertEqual(receipt.status,"VERIFIED")
        self.assertTrue(self.rt.promote_representation_proposal(proposal.proposal_id,principal="alice").startswith("rep_"))


if __name__=="__main__": unittest.main()
