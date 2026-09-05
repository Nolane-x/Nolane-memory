import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale


class QueryDomainRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_query_domain_materializes_bounded_principal_incarnation_cut_and_surface(self):
        qd = self.rt.compile_query_domain(
            "d", principal="alice", predicate={"field": "kind", "equals": "failure"},
            surfaces=["representations"], capability="EXACT_CANONICAL_SCAN",
        )
        self.assertEqual(qd.principal, "alice")
        self.assertEqual(qd.incarnation, 1)
        self.assertEqual(qd.cut.sequence, 0)
        self.assertEqual(qd.surfaces, ["representations"])
        self.assertEqual(qd.capability, "EXACT_CANONICAL_SCAN")

    def test_strong_negative_receipt_binds_typed_query_domain(self):
        receipt = self.rt.strong_negative_query("d", principal="alice", field="kind", equals="failure", completeness="COMPLETE")
        self.assertIsNotNone(receipt.query_domain_id)
        qd = self.rt.get_query_domain(receipt.query_domain_id)
        self.assertEqual(qd.predicate, receipt.predicate)
        self.assertEqual(qd.cut, receipt.cut)
        self.assertEqual(receipt.status, "NO_MATCH_COMPLETE_DOMAIN")

    def test_new_incarnation_stales_negative_receipt_bound_to_old_query_domain(self):
        receipt = self.rt.strong_negative_query("d", principal="alice", field="kind", equals="failure", completeness="COMPLETE")
        self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="restore")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_negative_query_receipt(receipt.receipt_id)

    def test_partial_query_domain_can_never_emit_complete_absence(self):
        qd = self.rt.compile_query_domain(
            "d", principal="alice", predicate={"field": "kind", "equals": "failure"},
            surfaces=["representations"], capability="PARTIAL_SCAN",
        )
        receipt = self.rt.execute_negative_query_domain(qd.query_domain_id)
        self.assertEqual(receipt.status, "NO_MATCH_PARTIAL_DOMAIN")
        self.assertEqual(receipt.query_domain_id, qd.query_domain_id)


if __name__ == "__main__": unittest.main()
