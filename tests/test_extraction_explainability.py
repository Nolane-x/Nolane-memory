import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime
from nolane_memory.errors import MemoryProposalStale, MemoryTransitionIncomplete


class ExtractionExplainabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("PRICE", {"price", "currency"})
        h = self.rt._head_row("d")
        self.ev = self.rt.capture_evidence(
            domain_id="d", operation_id="source", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            source_event_identity="page:1", content={"text": "Price is 19 USD"}, principal="alice",
            origin_roots=["url:https://example.test/item"], transport_channel="browser:https",
            external_identity="https://example.test/item", source_authority_class="UNTRUSTED_CONTENT",
            common_mode_group="publisher:example", binder_procedure="browser-capture-v1",
        ).object_id
        self.region = self.rt.create_region("d", "item-price", principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _proposal(self):
        return self.rt.propose_extraction(
            "d", source_evidence_id=self.ev, principal="alice", extractor_revision="extractor:v3",
            extracted_fields={"price": 19, "currency": "USD"},
            source_handles={"price": "chars:9-11", "currency": "chars:12-15"},
            candidate_types=["price_fact"], uncertainty={"price": 0.05, "currency": 0.01},
            high_risk_fields={"price", "currency"},
        )

    def test_extraction_is_candidate_only_until_high_risk_fields_verified(self):
        p = self._proposal()
        self.assertEqual(p.status, "CANDIDATE")
        v = self.rt.verify_extraction_proposal(
            "d", p.proposal_id, principal="alice", verifier_ref="deterministic:number-unit-v1",
            field_results={"price": "PASS"},
        )
        self.assertEqual(v.status, "INCOMPLETE")
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.promote_extraction_to_representation(
                p.proposal_id, region_id=self.region, principal="alice", kind="structured_fact",
                loss={"price": LossState.PRESERVED_EXACT, "currency": LossState.PRESERVED_EXACT},
                recoverable=set(), token_cost=2,
            )

    def test_verified_extraction_promotes_with_source_origin_and_typed_explanation(self):
        p = self._proposal()
        v = self.rt.verify_extraction_proposal(
            "d", p.proposal_id, principal="alice", verifier_ref="deterministic:number-unit-v1",
            field_results={"price": "PASS", "currency": "PASS"},
        )
        self.assertEqual(v.status, "VERIFIED")
        rep = self.rt.promote_extraction_to_representation(
            p.proposal_id, region_id=self.region, principal="alice", kind="structured_fact",
            loss={"price": LossState.PRESERVED_EXACT, "currency": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=2,
        )
        self.assertEqual(self.rt.get_origin_roots("d", "representation", rep), ["url:https://example.test/item"])
        explanation = self.rt.explain_memory(
            "d", rep, principal="alice", query_family="PRICE",
            consumer="agent:v1", task="purchase", regime="web", rendering="structured",
        )
        self.assertEqual(explanation["representation"]["extractor_revision"], "extractor:v3")
        self.assertEqual(explanation["source"]["evidence_ids"], [self.ev])
        self.assertEqual(explanation["source"]["origin_roots"], ["url:https://example.test/item"])
        self.assertEqual(explanation["source"]["authority_classes"], ["UNTRUSTED_CONTENT"])
        self.assertEqual(explanation["preservation"]["status"], "EXACT")
        self.assertEqual(explanation["preservation"]["loss"]["price"], "PRESERVED_EXACT")

    def test_source_revocation_after_verification_makes_extraction_proposal_stale(self):
        p = self._proposal()
        self.rt.verify_extraction_proposal(
            "d", p.proposal_id, principal="alice", verifier_ref="deterministic:number-unit-v1",
            field_results={"price": "PASS", "currency": "PASS"},
        )
        self.rt.revoke_evidence("d", self.ev, principal="alice")
        with self.assertRaises(MemoryProposalStale):
            self.rt.promote_extraction_to_representation(
                p.proposal_id, region_id=self.region, principal="alice", kind="structured_fact",
                loss={"price": LossState.PRESERVED_EXACT, "currency": LossState.PRESERVED_EXACT},
                recoverable=set(), token_cost=2,
            )

    def test_explanation_surfaces_unresolved_counterexample_instead_of_hiding_it(self):
        p = self._proposal()
        self.rt.verify_extraction_proposal(
            "d", p.proposal_id, principal="alice", verifier_ref="deterministic:number-unit-v1",
            field_results={"price": "PASS", "currency": "PASS"},
        )
        rep = self.rt.promote_extraction_to_representation(
            p.proposal_id, region_id=self.region, principal="alice", kind="structured_fact",
            loss={"price": LossState.PRESERVED_EXACT, "currency": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=2,
        )
        source_rep = self.rt.add_representation(
            "d", self.region, kind="source", payload={"price": 19, "currency": "USD"},
            loss={"price": LossState.PRESERVED_EXACT, "currency": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=5, principal="alice", source_evidence_ids=[self.ev],
            transform_kind="SOURCE_REBASE", transform_profile="source:v1",
        )
        ce = self.rt.record_query_counterexample(
            "d", region_id=self.region, representation_id=rep, query_family="PRICE",
            lost_dimensions={"currency"}, source_witness_id=source_rep,
            decision_relevance="wrong-currency-would-change-purchase", cause_type="REGION_CONTENT",
            principal="alice",
        )
        explanation = self.rt.explain_memory("d", rep, principal="alice", query_family="PRICE")
        self.assertEqual(explanation["counterexamples"][0]["counterexample_id"], ce.counterexample_id)
        self.assertEqual(explanation["counterexamples"][0]["resolved"], False)


if __name__ == "__main__": unittest.main()
