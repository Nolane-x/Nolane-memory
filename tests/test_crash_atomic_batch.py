import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryIdentityCollision


class InjectedCrash(RuntimeError):
    pass


class OneShotFault:
    def __init__(self, target):
        self.target = target
        self.fired = False

    def __call__(self, point, context):
        if point == self.target and not self.fired:
            self.fired = True
            raise InjectedCrash(point)


class CrashAtomicBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = f"{self.tmp.name}/memory.db"
        self.rt = MemoryRuntime(self.path)
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_atomic_batch_with_invalid_second_item_leaves_no_partial_state(self):
        with self.assertRaises(MemoryIdentityCollision):
            self.rt.capture_evidence_batch(
                domain_id="d", operation_id="batch-1", expected_seq=0, writer_epoch=1, principal="alice",
                items=[
                    {"source_event_identity": "same", "content": {"v": 1}},
                    {"source_event_identity": "same", "content": {"v": 2}},
                ],
            )
        self.assertEqual(self.rt.count_evidence("d"), 0)
        self.assertEqual(self.rt.head("d").sequence, 0)
        self.assertTrue(self.rt.verify_integrity("d"))

    def test_crash_after_mutation_before_journal_rolls_back_everything(self):
        self.rt.set_fault_injector(OneShotFault("after_mutation_before_journal"))
        with self.assertRaises(InjectedCrash):
            self.rt.capture_evidence_batch(
                domain_id="d", operation_id="batch-1", expected_seq=0, writer_epoch=1, principal="alice",
                items=[{"source_event_identity": "a", "content": {"v": 1}}],
            )
        self.assertEqual(self.rt.count_evidence("d"), 0)
        self.assertEqual(self.rt.head("d").sequence, 0)
        self.assertTrue(self.rt.verify_integrity("d"))

    def test_crash_after_journal_before_receipt_rolls_back_journal_and_state(self):
        self.rt.set_fault_injector(OneShotFault("after_journal_before_receipt"))
        with self.assertRaises(InjectedCrash):
            self.rt.capture_evidence_batch(
                domain_id="d", operation_id="batch-1", expected_seq=0, writer_epoch=1, principal="alice",
                items=[{"source_event_identity": "a", "content": {"v": 1}}],
            )
        self.assertEqual(self.rt.count_evidence("d"), 0)
        self.assertEqual(self.rt.db.execute("SELECT COUNT(*) FROM journal WHERE domain_id='d'").fetchone()[0], 0)
        self.assertTrue(self.rt.verify_integrity("d"))

    def test_lost_response_after_commit_reconciles_exactly_once_on_retry_and_restart(self):
        fault = OneShotFault("after_commit")
        self.rt.set_fault_injector(fault)
        with self.assertRaises(InjectedCrash):
            self.rt.capture_evidence_batch(
                domain_id="d", operation_id="batch-1", expected_seq=0, writer_epoch=1, principal="alice",
                items=[{"source_event_identity": "a", "content": {"v": 1}}],
            )
        self.assertEqual(self.rt.count_evidence("d"), 1)
        self.assertEqual(self.rt.head("d").sequence, 1)
        self.rt.set_fault_injector(None)
        receipt = self.rt.capture_evidence_batch(
            domain_id="d", operation_id="batch-1", expected_seq=0, writer_epoch=1, principal="alice",
            items=[{"source_event_identity": "a", "content": {"v": 1}}],
        )
        self.assertEqual(receipt.commit_seq, 1)
        self.assertEqual(self.rt.count_evidence("d"), 1)
        self.assertTrue(self.rt.verify_integrity("d"))
        self.rt.close()
        self.rt = MemoryRuntime(self.path)
        self.assertEqual(self.rt.count_evidence("d"), 1)
        self.assertEqual(self.rt.head("d").sequence, 1)
        self.assertTrue(self.rt.verify_integrity("d"))


if __name__ == "__main__": unittest.main()
