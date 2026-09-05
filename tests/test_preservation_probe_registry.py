import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale
from nolane_memory.types import LossState


class PreservationProbeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("POLICY", {"negation", "limit"})
        self.region = self.rt.create_region("d", "policy", principal="alice")
        self.source = self.rt.add_representation(
            "d", self.region, kind="raw", payload={"negation": True, "limit": 7},
            loss={"negation": LossState.PRESERVED_EXACT, "limit": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=8, principal="alice",
        )

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_structured_probe_compares_retained_source_against_target_observables(self):
        target = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"negation": True, "limit": 7},
            source_representation_ids=[self.source],
            loss={"negation": LossState.PRESERVED_EXACT, "limit": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=2, principal="alice",
        )
        self.rt.register_preservation_probe_profile(
            "structured:v1", revision=1, procedure="STRUCTURED_FIELD_COMPARE",
            protected_dimensions={"negation", "limit"}, verifier_class="DETERMINISTIC",
        )
        receipt = self.rt.run_preservation_probe(
            "d", source_representation_id=self.source, target_representation_id=target,
            query_family="POLICY", profile_id="structured:v1",
        )
        self.assertEqual(receipt.status, "PASS")
        self.assertEqual(receipt.dimension_results, {"limit": "MATCH", "negation": "MATCH"})
        self.assertTrue(self.rt.validate_preservation_probe_receipt(receipt.receipt_id))

    def test_dropped_critical_dimension_fails_instead_of_trusting_loss_metadata(self):
        target = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"limit": 7},
            source_representation_ids=[self.source],
            loss={"negation": LossState.PRESERVED_EXACT, "limit": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=2, principal="alice",
        )
        self.rt.register_preservation_probe_profile(
            "structured:v1", revision=1, procedure="STRUCTURED_FIELD_COMPARE",
            protected_dimensions={"negation", "limit"}, verifier_class="DETERMINISTIC",
        )
        receipt = self.rt.run_preservation_probe(
            "d", source_representation_id=self.source, target_representation_id=target,
            query_family="POLICY", profile_id="structured:v1",
        )
        self.assertEqual(receipt.status, "FAIL")
        self.assertEqual(receipt.dimension_results["negation"], "MISMATCH")

    def test_tool_specific_probe_requires_explicit_observables_and_never_self_certifies(self):
        target = self.rt.add_representation(
            "d", self.region, kind="tool-render", payload={"text": "not machine comparable"},
            source_representation_ids=[self.source],
            loss={"negation": LossState.UNKNOWN, "limit": LossState.UNKNOWN},
            recoverable={"negation", "limit"}, token_cost=2, principal="alice",
        )
        self.rt.register_preservation_probe_profile(
            "tool:v3", revision=1, procedure="DECLARED_OBSERVABLE_COMPARE",
            protected_dimensions={"negation", "limit"}, verifier_class="TOOL_SPECIFIC",
            tool_profile_ref="parser:v3",
        )
        unknown = self.rt.run_preservation_probe(
            "d", source_representation_id=self.source, target_representation_id=target,
            query_family="POLICY", profile_id="tool:v3",
        )
        self.assertEqual(unknown.status, "UNKNOWN")
        checked = self.rt.run_preservation_probe(
            "d", source_representation_id=self.source, target_representation_id=target,
            query_family="POLICY", profile_id="tool:v3",
            source_observables={"negation": True, "limit": 7},
            target_observables={"negation": True, "limit": 8},
        )
        self.assertEqual(checked.status, "FAIL")
        self.assertEqual(checked.dimension_results["limit"], "MISMATCH")

    def test_probe_receipt_stales_when_source_or_profile_changes(self):
        target = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"negation": True, "limit": 7},
            source_representation_ids=[self.source],
            loss={"negation": LossState.PRESERVED_EXACT, "limit": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=2, principal="alice",
        )
        self.rt.register_preservation_probe_profile(
            "structured:v1", revision=1, procedure="STRUCTURED_FIELD_COMPARE",
            protected_dimensions={"negation", "limit"}, verifier_class="DETERMINISTIC",
        )
        receipt = self.rt.run_preservation_probe(
            "d", source_representation_id=self.source, target_representation_id=target,
            query_family="POLICY", profile_id="structured:v1",
        )
        self.rt.register_preservation_probe_profile(
            "structured:v1", revision=2, procedure="STRUCTURED_FIELD_COMPARE",
            protected_dimensions={"negation", "limit"}, verifier_class="DETERMINISTIC",
        )
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_preservation_probe_receipt(receipt.receipt_id)


if __name__ == "__main__":
    unittest.main()
