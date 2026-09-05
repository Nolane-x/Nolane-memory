import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryDependencyStale, MemoryTransitionIncomplete


class QueryFamilyPreservationRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"}, revision=1)
        self.region = self.rt.create_region("d", "r", principal="alice")
        self.rep = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_query_family_expansion_stales_old_recall_frame(self):
        frame = self.rt.compile_recall("d", "alice", [RecallRole("r", self.region, "X")], 10)
        self.assertTrue(self.rt.validate_frame(frame.frame_id))
        self.rt.register_query_family("X", {"x", "y"}, revision=2)
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_frame(frame.frame_id)

    def test_preservation_certificate_is_bound_to_query_family_revision(self):
        cert = self.rt.certify_preservation(
            "d", self.rep, query_family="X", verifier_ref="deterministic:loss-map-v1"
        )
        self.assertEqual(cert.status, "EXACT")
        self.assertTrue(self.rt.validate_preservation_certificate(cert.certificate_id))
        self.rt.register_query_family("X", {"x", "y"}, revision=2)
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_preservation_certificate(cert.certificate_id)
        fresh = self.rt.certify_preservation(
            "d", self.rep, query_family="X", verifier_ref="deterministic:loss-map-v1"
        )
        self.assertNotEqual(fresh.status, "EXACT")
        self.assertIn("y", fresh.missing_dimensions)

    def test_query_family_revision_must_advance_contiguously(self):
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.register_query_family("X", {"x", "y"}, revision=3)

    def test_query_family_history_retains_prior_basis(self):
        self.rt.register_query_family("X", {"x", "y"}, revision=2)
        history = self.rt.get_query_family_history("X")
        self.assertEqual([(h["revision"], set(h["required_dimensions"])) for h in history], [
            (1, {"x"}), (2, {"x", "y"})
        ])


if __name__ == "__main__": unittest.main()
