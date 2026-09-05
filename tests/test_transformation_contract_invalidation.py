import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale, MemoryTransitionIncomplete


class TransformationContractInvalidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})
        self.region = self.rt.create_region("d", "r", principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_contract_revision_stales_preservation_certificate(self):
        self.rt.register_transformation_contract(
            "summary:v", revision=1, transform_kind="PURE",
            protected_dimensions={"x"}, forbidden_loss=set(),
        )
        rep = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice", transform_profile="summary:v",
        )
        cert = self.rt.certify_preservation("d", rep, query_family="X", verifier_ref="det:v1")
        self.assertTrue(self.rt.validate_preservation_certificate(cert.certificate_id))
        self.rt.register_transformation_contract(
            "summary:v", revision=2, transform_kind="PURE",
            protected_dimensions={"x"}, forbidden_loss={"x"},
        )
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_preservation_certificate(cert.certificate_id)

    def test_contract_revision_stales_pending_proposal_dependencies(self):
        self.rt.register_transformation_contract(
            "summary:p", revision=1, transform_kind="PURE",
            protected_dimensions={"x"}, forbidden_loss=set(),
        )
        source = self.rt.add_representation(
            "d", self.region, kind="raw", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=5, principal="alice",
        )
        proposal = self.rt.create_representation_proposal(
            "d", self.region, kind="summary", payload={"x": 1},
            source_representation_ids=[source], loss={"x": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice",
            transform_kind="PURE", transform_profile="summary:p",
        )
        self.rt.validate_dependencies("d", proposal.dependencies)
        self.rt.register_transformation_contract(
            "summary:p", revision=2, transform_kind="PURE",
            protected_dimensions={"x", "negation"}, forbidden_loss=set(),
        )
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_dependencies("d", proposal.dependencies)

    def test_contract_revisions_must_be_contiguous(self):
        self.rt.register_transformation_contract(
            "summary:c", revision=1, transform_kind="PURE", protected_dimensions={"x"}, forbidden_loss=set(),
        )
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.register_transformation_contract(
                "summary:c", revision=3, transform_kind="PURE", protected_dimensions={"x"}, forbidden_loss=set(),
            )


if __name__ == "__main__":
    unittest.main()
