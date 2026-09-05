import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime
from nolane_memory.errors import MemoryPublicationBlocked, MemoryTransitionIncomplete


class IntegrityAndPublicationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.rt=MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")

    def tearDown(self): self.rt.close(); self.tmp.cleanup()

    def _evidence(self, op, sid, authority):
        h=self.rt._head_row("d")
        return self.rt.capture_evidence(
            domain_id="d",operation_id=op,expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),
            source_event_identity=sid,content={"sid":sid},principal="alice",source_authority_class=authority,
        ).object_id

    def test_integrity_authority_profile_is_rechecked_inside_claim_admission(self):
        self.rt.register_integrity_authority_profile(
            "d", profile_id="critical", revision=1, issuer="governance",
            subject_ids={"critical-claim"}, operations={"CREATE_CLAIM","REVISE_CLAIM"},
            accepted_authority_classes={"TRUSTED_FACT"}, enabled=True,
        )
        weak=self._evidence("e1","weak","UNTRUSTED_CONTENT")
        h=self.rt._head_row("d")
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.create_claim(
                domain_id="d",operation_id="c1",expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),
                logical_id="critical-claim",proposition={"ok":True},valid_from=None,valid_to=None,
                support_paths=[[weak]],principal="alice",
            )
        strong=self._evidence("e2","strong","TRUSTED_FACT")
        h=self.rt._head_row("d")
        receipt=self.rt.create_claim(
            domain_id="d",operation_id="c2",expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),
            logical_id="critical-claim",proposition={"ok":True},valid_from=None,valid_to=None,
            support_paths=[[strong]],principal="alice",
        )
        self.assertTrue(receipt.object_id.startswith("claim_"))

    def test_publication_policy_revision_change_stales_pending_saga(self):
        self.rt.create_domain("a"); self.rt.create_domain("b")
        r=self.rt.create_region("a","r",principal="alice")
        rep=self.rt.add_representation("a",r,kind="structured",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice")
        self.rt.register_publication_policy(
            "a","b",policy_id="share",revision=1,issuer="gov",allow=True,
            allowed_principals={"alice"},preserve_origin=True,
        )
        saga=self.rt.prepare_publication("a","b",rep,principal="alice",operation_id="p1")
        self.assertEqual(saga["publication_policy_revision"],1)
        self.rt.register_publication_policy(
            "a","b",policy_id="share",revision=2,issuer="gov",allow=False,
            allowed_principals={"alice"},preserve_origin=True,
        )
        with self.assertRaises(MemoryPublicationBlocked):
            self.rt.complete_publication(saga["saga_id"],accept=True)
        self.assertEqual(self.rt.get_publication_saga(saga["saga_id"])["state"],"SOURCE_REVALIDATION_REQUIRED")

    def test_publication_policy_can_block_prepare_for_principal(self):
        self.rt.create_domain("a"); self.rt.create_domain("b")
        r=self.rt.create_region("a","r",principal="alice")
        rep=self.rt.add_representation("a",r,kind="structured",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice")
        self.rt.register_publication_policy(
            "a","b",policy_id="share",revision=1,issuer="gov",allow=True,
            allowed_principals={"bob"},preserve_origin=True,
        )
        with self.assertRaises(MemoryPublicationBlocked):
            self.rt.prepare_publication("a","b",rep,principal="alice",operation_id="p2")


if __name__=='__main__': unittest.main()
