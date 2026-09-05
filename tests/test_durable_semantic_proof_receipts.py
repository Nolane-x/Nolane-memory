import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale


class DurableSemanticProofReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _evidence(self, op, sid, root, mode):
        h = self.rt._head_row("d")
        return self.rt.capture_evidence(
            domain_id="d", operation_id=op, expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), source_event_identity=sid,
            content={"sid": sid}, principal="alice", origin_roots=[root],
            common_mode_group=mode,
        ).object_id

    def test_independence_receipt_is_durable_and_stales_on_origin_binding_change(self):
        e1 = self._evidence("e1", "s1", "root:1", "mode:1")
        e2 = self._evidence("e2", "s2", "root:2", "mode:2")
        receipt = self.rt.issue_evidence_independence_receipt("d", [e1, e2])
        self.assertEqual(receipt.dependence, "INDEPENDENT")
        self.assertTrue(self.rt.validate_evidence_independence_receipt(receipt.receipt_id))
        b = self.rt.get_origin_bindings("d", e1)[0]
        self.rt.revoke_origin_binding("d", b.binding_id, principal="alice", reason="compromised")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_evidence_independence_receipt(receipt.receipt_id)

    def test_support_bundle_receipt_stales_on_support_lifecycle_change(self):
        e1 = self._evidence("e1", "s1", "root:1", "mode:1")
        h = self.rt._head_row("d")
        self.rt.create_claim(
            domain_id="d", operation_id="c1", expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), logical_id="claim",
            proposition={"x": 1}, valid_from=None, valid_to=None,
            support_paths=[[e1]], principal="alice",
        )
        receipt = self.rt.issue_claim_support_bundle_receipt("d", "claim")
        self.assertTrue(receipt.supported)
        self.assertTrue(self.rt.validate_claim_support_bundle_receipt(receipt.receipt_id))
        self.rt.revoke_evidence("d", e1, principal="alice")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_claim_support_bundle_receipt(receipt.receipt_id)

    def test_recoverability_certificate_is_current_route_proof(self):
        region = self.rt.create_region("d", "r", principal="alice")
        source = self.rt.add_representation(
            "d", region, kind="raw", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10,
            principal="alice",
        )
        compact = self.rt.add_representation(
            "d", region, kind="summary", payload={"text": "one"},
            source_representation_ids=[source], loss={"x": LossState.LOST},
            recoverable={"x"}, token_cost=1, principal="alice",
        )
        cert = self.rt.certify_recoverability("d", compact, query_family="X")
        self.assertEqual(cert.status, "SOURCE_REHYDRATABLE")
        self.assertEqual(cert.source_witness_ids, [source])
        self.assertTrue(self.rt.validate_recoverability_certificate(cert.certificate_id))
        self.rt.invalidate_representation("d", source, principal="alice")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_recoverability_certificate(cert.certificate_id)
        fresh = self.rt.certify_recoverability("d", compact, query_family="X")
        self.assertEqual(fresh.status, "IRRECOVERABLE_UNDER_CURRENT_RETENTION")
        self.assertEqual(fresh.source_witness_ids, [])


if __name__ == "__main__": unittest.main()
