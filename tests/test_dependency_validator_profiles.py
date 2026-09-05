import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale
from nolane_memory.types import Dependency


class DependencyValidatorProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")
        self.rt.bump_generation("d", "tool", "pay")
        self.dep = Dependency("tool", "pay", self.rt._generation("d", "tool", "pay"))

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_strict_profile_distinguishes_unchanged_from_invalidating_generation_change(self):
        self.rt.register_dependency_validator_profile(
            "tool-strict", dep_class="tool", revision=1, procedure="STRICT_GENERATION"
        )
        same = self.rt.classify_dependency_change("d", dependency=self.dep, profile_id="tool-strict")
        self.assertEqual(same.classification, "UNCHANGED")
        self.rt.bump_generation("d", "tool", "pay")
        changed = self.rt.classify_dependency_change("d", dependency=self.dep, profile_id="tool-strict")
        self.assertEqual(changed.classification, "INVALIDATING_CHANGE")

    def test_canonical_equivalence_can_prove_compatible_refinement_but_missing_basis_is_unknown(self):
        self.rt.register_dependency_validator_profile(
            "tool-semantic", dep_class="tool", revision=1, procedure="CANONICAL_EQUIVALENCE"
        )
        self.rt.bump_generation("d", "tool", "pay")
        compatible = self.rt.classify_dependency_change(
            "d", dependency=self.dep, profile_id="tool-semantic",
            old_observable={"parameter": "amount", "default": None},
            new_observable={"default": None, "parameter": "amount"},
        )
        self.assertEqual(compatible.classification, "COMPATIBLE_REFINEMENT")
        unknown = self.rt.classify_dependency_change(
            "d", dependency=self.dep, profile_id="tool-semantic"
        )
        self.assertEqual(unknown.classification, "UNKNOWN")

    def test_change_outside_dependency_manifest_is_irrelevant(self):
        self.rt.register_dependency_validator_profile(
            "tool-strict", dep_class="tool", revision=1, procedure="STRICT_GENERATION"
        )
        result = self.rt.classify_manifest_change(
            "d", dependencies=[self.dep], changed_dep_class="region", changed_dep_key="other",
            profile_id="tool-strict",
        )
        self.assertEqual(result["classification"], "IRRELEVANT")

    def test_profile_revision_invalidates_old_compatibility_receipt(self):
        self.rt.register_dependency_validator_profile(
            "tool-semantic", dep_class="tool", revision=1, procedure="CANONICAL_EQUIVALENCE"
        )
        self.rt.bump_generation("d", "tool", "pay")
        receipt = self.rt.classify_dependency_change(
            "d", dependency=self.dep, profile_id="tool-semantic",
            old_observable={"x": 1}, new_observable={"x": 1},
        )
        self.assertTrue(self.rt.validate_dependency_compatibility_receipt(receipt.receipt_id))
        self.rt.register_dependency_validator_profile(
            "tool-semantic", dep_class="tool", revision=2, procedure="CANONICAL_EQUIVALENCE"
        )
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_dependency_compatibility_receipt(receipt.receipt_id)


if __name__ == "__main__":
    unittest.main()
