import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryStaleWriter


class WriterFenceRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d", writer_epoch=3)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_domain_creation_materializes_initial_writer_fence_revision(self):
        history = self.rt.list_writer_fence_revisions("d")
        self.assertEqual([r.writer_epoch for r in history], [3])
        self.assertIsNone(history[0].predecessor_epoch)
        self.assertEqual(history[0].reason, "DOMAIN_CREATE")

    def test_advance_writer_epoch_appends_immutable_monotonic_revision(self):
        self.rt.advance_writer_epoch("d", 5, reason="FAILOVER")
        history = self.rt.list_writer_fence_revisions("d")
        self.assertEqual([r.writer_epoch for r in history], [3, 5])
        self.assertEqual(history[-1].predecessor_epoch, 3)
        self.assertEqual(history[-1].reason, "FAILOVER")
        with self.assertRaises(MemoryStaleWriter):
            self.rt.advance_writer_epoch("d", 5)

    def test_new_incarnation_records_writer_fence_supersession(self):
        cut = self.rt.start_new_incarnation("d", principal="alice", reason="restore", operation_id="restore-1")
        history = self.rt.list_writer_fence_revisions("d")
        self.assertEqual(history[-1].writer_epoch, 4)
        self.assertEqual(history[-1].predecessor_epoch, 3)
        self.assertEqual(history[-1].incarnation, cut.incarnation)
        self.assertEqual(history[-1].reason, "NEW_INCARNATION")

    def test_no_two_clock_audit_detects_writer_epoch_mirror_drift(self):
        self.rt.advance_writer_epoch("d", 4)
        self.rt.db.execute("UPDATE domains SET writer_epoch=9 WHERE domain_id='d'")
        audit = self.rt.audit_no_two_writable_clocks("d")
        self.assertFalse(audit.passed)
        self.assertTrue(any(v["kind"] == "WRITER_FENCE_CURRENT_HISTORY_DIVERGENCE" for v in audit.violations))


if __name__ == "__main__": unittest.main()
