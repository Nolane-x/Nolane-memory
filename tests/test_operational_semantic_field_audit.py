import tempfile
import unittest

from nolane_memory import MemoryRuntime


class OperationalSemanticFieldAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_section_389_registry_covers_normative_safety_fields_with_mandatory_readers(self):
        registry = self.rt.operational_semantic_field_registry()
        required = {
            "expires_at", "clock_epoch", "applicability", "invalidates_on",
            "hard_role", "declassified", "trusted_authority", "canonical",
            "recoverable", "current", "negative_result", "tool_profile",
        }
        self.assertTrue(required.issubset(registry))
        for field in required:
            entry = registry[field]
            self.assertTrue(entry["semantic_owner"])
            self.assertTrue(entry["writers"])
            self.assertTrue(entry["mandatory_readers"])
            self.assertTrue(entry["input_authority"])
            self.assertTrue(entry["freshness"])
            self.assertTrue(entry["unknown_failure"])
            self.assertTrue(entry["cache_invalidation"])
            self.assertTrue(entry["conformance_fixture"])

    def test_operational_field_audit_verifies_executable_method_bindings(self):
        audit = self.rt.audit_operational_semantic_fields()
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["missing_fields"], [])
        self.assertEqual(audit["missing_methods"], [])
        self.assertGreaterEqual(audit["field_count"], 12)


if __name__ == "__main__":
    unittest.main()
