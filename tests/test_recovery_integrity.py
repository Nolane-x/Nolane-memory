import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryIntegrityError


class RecoveryIntegrityTests(unittest.TestCase):
    def test_restart_reconciles_same_operation_without_duplicate_commit(self):
        tmp = tempfile.TemporaryDirectory()
        path = f"{tmp.name}/memory.db"
        rt = MemoryRuntime(path)
        rt.create_domain("d", writer_epoch=3)
        first = rt.capture_evidence(
            domain_id="d", operation_id="op-1", expected_seq=0, writer_epoch=3,
            source_event_identity="evt:1", content={"x": 1}, principal="alice",
        )
        rt.close()

        rt2 = MemoryRuntime(path)
        try:
            again = rt2.capture_evidence(
                domain_id="d", operation_id="op-1", expected_seq=0, writer_epoch=3,
                source_event_identity="evt:1", content={"x": 1}, principal="alice",
            )
            self.assertEqual(again, first)
            self.assertEqual(rt2.head("d").sequence, 1)
        finally:
            rt2.close(); tmp.cleanup()

    def test_integrity_verifier_recomputes_hash_chain_and_rejects_tamper(self):
        tmp = tempfile.TemporaryDirectory()
        path = f"{tmp.name}/memory.db"
        rt = MemoryRuntime(path)
        rt.create_domain("d", writer_epoch=1)
        r1 = rt.capture_evidence(
            domain_id="d", operation_id="op-1", expected_seq=0, writer_epoch=1,
            source_event_identity="evt:1", content={"x": 1}, principal="alice",
        )
        rt.capture_evidence(
            domain_id="d", operation_id="op-2", expected_seq=r1.commit_seq, writer_epoch=1,
            source_event_identity="evt:2", content={"x": 2}, principal="alice",
        )
        self.assertTrue(rt.verify_integrity("d"))
        rt.db.execute("UPDATE journal SET root=? WHERE domain_id=? AND sequence=?", ("f" * 64, "d", 1))
        with self.assertRaises(MemoryIntegrityError):
            rt.verify_integrity("d")
        rt.close(); tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
