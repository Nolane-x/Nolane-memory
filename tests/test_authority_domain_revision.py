import tempfile
import unittest

from nolane_memory import MemoryRuntime


class AuthorityDomainRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d", writer_epoch=2, incarnation=1)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_create_materializes_initial_authority_domain_revision(self):
        hist = self.rt.list_authority_domain_revisions("d")
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0].revision, 1)
        self.assertIsNone(hist[0].predecessor_revision)
        self.assertEqual(hist[0].incarnation, 1)
        self.assertEqual(hist[0].action, "CREATE")

    def test_new_incarnation_appends_domain_revision_and_retry_is_idempotent(self):
        cut1 = self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="inc-op")
        cut2 = self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="inc-op")
        self.assertEqual(cut1, cut2)
        hist = self.rt.list_authority_domain_revisions("d")
        self.assertEqual([r.revision for r in hist], [1, 2])
        self.assertEqual(hist[-1].predecessor_revision, 1)
        self.assertEqual(hist[-1].incarnation, 2)
        self.assertEqual(hist[-1].sequence, cut1.sequence)
        self.assertEqual(hist[-1].root, cut1.root)

    def test_domain_revision_at_sequence_preserves_historical_incarnation(self):
        self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="inc-op")
        before = self.rt.authority_domain_revision_at_sequence("d", 0)
        after = self.rt.authority_domain_revision_at_sequence("d", 1)
        self.assertEqual(before.incarnation, 1)
        self.assertEqual(after.incarnation, 2)

    def test_no_two_clock_audit_detects_domain_incarnation_mirror_drift(self):
        self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="inc-op")
        self.rt.db.execute("UPDATE domains SET incarnation=99 WHERE domain_id='d'")
        audit = self.rt.audit_no_two_writable_clocks("d")
        self.assertFalse(audit.passed)
        self.assertTrue(any(v["kind"] == "AUTHORITY_DOMAIN_CURRENT_HISTORY_DIVERGENCE" for v in audit.violations))


if __name__ == "__main__": unittest.main()
